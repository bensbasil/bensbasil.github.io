import sqlite3
import os

db_path = r"d:\Bens Files\Portfolio_Website\backend\rag.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, filename, user_id FROM documents")
        rows = cursor.fetchall()
        print(f"Total documents: {len(rows)}")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
