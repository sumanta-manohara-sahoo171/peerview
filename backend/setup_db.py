# setup_db.py
import sqlite3

def create_tables():
    # This will create a file named 'peerview.db' in your backend folder
    # If the file already exists, it just connects to it
    conn = sqlite3.connect('peerview.db')
    cursor = conn.cursor()

    # 1. Create the USERS table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        status TEXT DEFAULT 'active',
        strike_count INTEGER DEFAULT 0
    )
    ''')

    # 2. Create the POSTS table
    # Notice the 'file_path' column! This is where we will save the link to the uploaded images/docs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        post_type TEXT NOT NULL, 
        file_path TEXT,          
        likes INTEGER DEFAULT 0,
        FOREIGN KEY (author_id) REFERENCES users (id)
    )
    ''')

    # Save (commit) the changes and close the connection
    conn.commit()
    conn.close()
    print("✅ SQLite database 'peerview.db' created successfully with Users and Posts tables!")

if __name__ == '__main__':
    create_tables()