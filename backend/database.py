import sqlite3
import os


def get_db_connection():
    # Ensure the backend creates the DB in the correct folder
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'peerview.db')

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys for SQLite
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db_connection()

    # 1. USERS TABLE (Email & OTP Auth)
    conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                bio TEXT,
                avatar_url TEXT,
                otp_code TEXT,
                otp_expiry DATETIME,
                is_verified BOOLEAN DEFAULT 0  -- Add this line!
            )
        ''')

    # 2. POSTS TABLE (FIXED: Added post_type)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            file_path TEXT,
            post_type TEXT DEFAULT 'blog',  -- NEW: The missing column!
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 3. COMMENTS TABLE
    conn.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_reported BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 4. VOTES TABLE
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            vote_type INTEGER NOT NULL,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with post_type, Email, and OTP support!")