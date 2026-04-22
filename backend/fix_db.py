import sqlite3
import os

# Connect to the exact same database file
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'peerview.db')

conn = sqlite3.connect(db_path)

try:
    # Forcefully add the missing column to the existing posts table
    conn.execute("ALTER TABLE posts ADD COLUMN post_type TEXT DEFAULT 'blog'")
    print("✅ SUCCESS: Forced the 'post_type' column into the posts table!")
except sqlite3.OperationalError as e:
    # If the column already exists, it will throw an error, which we can ignore
    print(f"⚠️ Notice: {e}")

conn.commit()
conn.close()