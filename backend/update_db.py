# update_db.py
import sqlite3

def add_comments_table():
    conn = sqlite3.connect('peerview.db')
    cursor = conn.cursor()

    # Create the comments table
    # is_anonymous uses INTEGER (1 for True, 0 for False) since SQLite doesn't have a strict BOOLEAN type
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_anonymous INTEGER DEFAULT 1, 
        FOREIGN KEY (post_id) REFERENCES posts (id),
        FOREIGN KEY (author_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ Comments table successfully added to peerview.db!")

if __name__ == '__main__':
    add_comments_table()