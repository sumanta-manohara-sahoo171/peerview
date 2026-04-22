import sqlite3
import os

base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'peerview.db')
conn = sqlite3.connect(db_path)

try:
    # Add the column. Default is 0 (Unverified)
    conn.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")

    # Auto-verify all existing accounts (like your Admin account!)
    conn.execute("UPDATE users SET is_verified = 1")
    print("✅ SUCCESS: Added 'is_verified' security column and protected existing users!")
except sqlite3.OperationalError as e:
    print(f"⚠️ Notice: {e}")

conn.commit()
conn.close()