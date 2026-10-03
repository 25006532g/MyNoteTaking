import os
from pathlib import Path
from typing import Mapping


DATABASE_URL_KEYS = (
    'DATABASE_URL',
    'POSTGRES_URL',
    'POSTGRES_PRISMA_URL',
    'DATABASE_URL_UNPOOLED',
    'POSTGRES_URL_NON_POOLING',
)


def get_database_uri(environment: Mapping[str, str], root_dir: str) -> tuple[str, bool]:
    database_url = next(
        (environment[key] for key in DATABASE_URL_KEYS if environment.get(key)),
        None,
    )
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
        elif database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return database_url, True

    if environment.get('VERCEL') or environment.get('VERCEL_ENV'):
        raise RuntimeError(
            'No PostgreSQL URL is configured for Vercel. Add DATABASE_URL to the '
            'Vercel project environment variables and redeploy.'
        )

    database_path = Path(root_dir) / 'database' / 'app.db'
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return f'sqlite:///{database_path}', False