import os
from database import get_engine
from sqlalchemy import text

def migrate():
    engine = get_engine()
    print(f"Migrating database using engine: {engine.url}...")
    
    with engine.connect() as conn:
        try:
            # DuckDB and Postgres both support ALTER TABLE ... ADD COLUMN IF NOT EXISTS
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS study_guide TEXT"))
            print("Added column study_guide")
            if not engine.url.drivername.startswith("duckdb"):
                conn.commit()
        except Exception as e:
            print(f"Error adding study_guide: {e}")

        try:
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS quiz TEXT"))
            print("Added column quiz")
            if not engine.url.drivername.startswith("duckdb"):
                conn.commit()
        except Exception as e:
            print(f"Error adding quiz: {e}")
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
