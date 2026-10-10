import sys
from pathlib import Path
from sqlalchemy import inspect, text

# Ensure backend project root is on sys.path so `import app` works when
# executing this script directly (sys.path[0] becomes the scripts/ folder).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config.settings import settings
from app.database.database import engine

def main():
    try:
        # Attempt a lightweight connection test
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            inspector = inspect(conn)
            tables = inspector.get_table_names()

        print('Database connection: OK')
        if tables:
            print('\nTables:')
            for t in tables:
                print(f'- {t}')
        else:
            print('No tables found in the target database.')

    except Exception as exc:
        print('Database connection: FAILED')
        print('Error:', str(exc))
        # Do not print secrets or full DATABASE_URL
        sys.exit(1)

if __name__ == '__main__':
    main()
