from database import get_engine
import pandas as pd
from sqlalchemy import text

def preview_db():
    engine = get_engine()
    
    sql = text("""
    SELECT 
        v.video_id, 
        v.url, 
        v.title, 
        t.language, 
        t.is_generated, 
        LENGTH(t.transcript) as transcript_length, 
        SUBSTRING(t.transcript, 1, 100) as preview 
    FROM videos v 
    JOIN transcripts t ON v.video_id = t.video_id
    """)
    
    print("--- Database Preview ---")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
            if not df.empty:
                print(df.to_string())
            else:
                print("No data found.")
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    preview_db()
