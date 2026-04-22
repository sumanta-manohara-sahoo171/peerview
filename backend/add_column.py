import sqlite3
import os

# Connect to the database
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'peerview.db')
conn = sqlite3.connect(db_path)

print("Attempting to upgrade the users table...")

try:
    # 1. Add the missing column
    conn.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")
    print("✅ SUCCESS: Added 'is_verified' column to the database!")
except Exception as e:
    print(f"⚠️ Column might already exist. Notice: {e}")

try:
    # 2. Auto-verify all existing accounts so you don't get locked out
    conn.execute("UPDATE users SET is_verified = 1")
    conn.commit()
    print("✅ SUCCESS: Protected existing users (like your Admin account)!")
except Exception as e:
    print(f"⚠️ Failed to update users. Notice: {e}")

conn.close()