import duckdb

def preview_db():
    conn = duckdb.connect('youtube_data.duckdb', read_only=True)
    
    # SQL extracted from db.ipynb (cell 14)
    sql = """
    SELECT 
        v.video_id, 
        v.url, 
        v.title, 
        t.language, 
        t.is_generated, 
        len(t.transcript) as transcript_length, 
        t.transcript[:100] as preview 
    FROM videos v 
    JOIN transcripts t ON v.video_id = t.video_id
    """
    
    print("--- Database Preview ---")
    conn.sql(sql).show()
    conn.close()

if __name__ == "__main__":
    preview_db()
