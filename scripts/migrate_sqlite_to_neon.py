import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import create_engine, select, text


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.models.note import Note
from src.models.user import User, db


TABLES = (Note.__table__, User.__table__)


def parse_args():
    parser = argparse.ArgumentParser(description='Copy local SQLite rows to Neon Postgres.')
    parser.add_argument(
        '--source',
        type=Path,
        default=ROOT_DIR / 'database' / 'app.db',
        help='Path to the source SQLite database',
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Create missing tables and copy rows; without this flag, only inspect',
    )
    return parser.parse_args()


def get_postgres_url():
    load_dotenv(ROOT_DIR / '.env')
    url = os.getenv('DATABASE_URL_UNPOOLED')
    if not url:
        raise RuntimeError('Set DATABASE_URL_UNPOOLED to the Neon direct connection URL')

    parsed = urlsplit(url)
    if parsed.scheme not in ('postgres', 'postgresql', 'postgresql+psycopg'):
        raise RuntimeError('DATABASE_URL_UNPOOLED must be a PostgreSQL connection URL')
    if parsed.hostname and '-pooler' in parsed.hostname:
        raise RuntimeError('Migrations require the direct, unpooled Neon connection URL')
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql+psycopg://', 1)
    if url.startswith('postgresql://'):
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return url


def read_source_rows(source_path):
    if not source_path.is_file():
        raise RuntimeError(f'Source SQLite database does not exist: {source_path}')

    with sqlite3.connect(source_path) as connection:
        connection.row_factory = sqlite3.Row
        rows_by_table = {}
        for table in TABLES:
            rows_by_table[table.name] = [dict(row) for row in connection.execute(
                f'SELECT * FROM "{table.name}" ORDER BY id'
            )]

    for rows in rows_by_table.values():
        for row in rows:
            for timestamp in ('created_at', 'updated_at'):
                if timestamp in row and isinstance(row[timestamp], str):
                    row[timestamp] = datetime.fromisoformat(row[timestamp])
    return rows_by_table


def find_existing(connection, table, source_rows):
    source_ids = [row['id'] for row in source_rows]
    if not source_ids:
        return {}
    rows = connection.execute(
        select(table).where(table.c.id.in_(source_ids))
    ).mappings()
    return {row['id']: dict(row) for row in rows}


def rows_to_insert(table, source_rows, existing_rows):
    pending = []
    for source_row in source_rows:
        existing = existing_rows.get(source_row['id'])
        if existing is None:
            pending.append(source_row)
            continue

        for column in table.columns:
            name = column.name
            if source_row[name] != existing[name]:
                raise RuntimeError(
                    f'Conflicting {table.name} row id {source_row["id"]}; '
                    'no remote rows were changed'
                )
    return pending


def print_plan(engine, rows_by_table, apply):
    with engine.connect() as connection:
        for table in TABLES:
            exists = engine.dialect.has_table(connection, table.name, schema='public')
            target_count = None
            pending_count = len(rows_by_table[table.name])
            if exists:
                existing = find_existing(connection, table, rows_by_table[table.name])
                pending_count = len(rows_to_insert(table, rows_by_table[table.name], existing))
                target_count = connection.scalar(select(text('count(*)')).select_from(table))
            print(
                f'{table.name}: source={len(rows_by_table[table.name])}, '
                f'target_before={target_count if target_count is not None else "table missing"}, '
                f'rows_to_insert={pending_count}'
            )

    if not apply:
        print('Dry run only. Pass --apply to create missing tables and copy rows.')


def migrate(engine, rows_by_table):
    db.metadata.create_all(engine)
    with engine.begin() as connection:
        for table in TABLES:
            existing = find_existing(connection, table, rows_by_table[table.name])
            pending = rows_to_insert(table, rows_by_table[table.name], existing)
            if pending:
                connection.execute(table.insert(), pending)
            connection.execute(text(
                f"SELECT setval(pg_get_serial_sequence('public.\"{table.name}\"', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM public.\"{table.name}\"), 1), "
                f"EXISTS (SELECT 1 FROM public.\"{table.name}\"))"
            ))
            print(f'{table.name}: inserted={len(pending)}, already_present={len(existing)}')


def main():
    args = parse_args()
    rows_by_table = read_source_rows(args.source)
    engine = create_engine(get_postgres_url(), pool_pre_ping=True)
    try:
        print_plan(engine, rows_by_table, args.apply)
        if args.apply:
            migrate(engine, rows_by_table)
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, sqlite3.Error) as error:
        print(f'Migration stopped: {error}', file=sys.stderr)
        raise SystemExit(1) from error