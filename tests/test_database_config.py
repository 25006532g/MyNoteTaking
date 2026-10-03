import tempfile
import unittest
from pathlib import Path

from src.database_config import get_database_uri


class DatabaseConfigTests(unittest.TestCase):
    def test_prefers_pooled_database_url_and_uses_psycopg_driver(self):
        uri, is_postgres = get_database_uri({
            'DATABASE_URL': 'postgresql://db.example/neondb',
            'DATABASE_URL_UNPOOLED': 'postgresql://direct.example/neondb',
        }, '/tmp/not-used')
        self.assertEqual(uri, 'postgresql+psycopg://db.example/neondb')
        self.assertTrue(is_postgres)

    def test_accepts_vercel_postgres_url_alias(self):
        uri, is_postgres = get_database_uri({
            'VERCEL': '1',
            'POSTGRES_URL': 'postgres://db.example/neondb',
        }, '/tmp/not-used')
        self.assertEqual(uri, 'postgresql+psycopg://db.example/neondb')
        self.assertTrue(is_postgres)

    def test_requires_remote_database_on_vercel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RuntimeError, 'Add DATABASE_URL'):
                get_database_uri({'VERCEL': '1'}, temp_dir)
            self.assertFalse((Path(temp_dir) / 'database').exists())

    def test_uses_sqlite_fallback_only_for_local_development(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            uri, is_postgres = get_database_uri({}, temp_dir)
            self.assertEqual(uri, f'sqlite:///{temp_dir}/database/app.db')
            self.assertFalse(is_postgres)
            self.assertTrue((Path(temp_dir) / 'database').is_dir())


if __name__ == '__main__':
    unittest.main()