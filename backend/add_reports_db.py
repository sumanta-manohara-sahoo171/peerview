# add_reports_db.py
import sqlite3


def add_reports_table():
    conn = sqlite3.connect('peerview.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comment_id INTEGER NOT NULL,
        reporter_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'pending', 
        FOREIGN KEY (comment_id) REFERENCES comments (id),
        FOREIGN KEY (reporter_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ Reports table successfully added to peerview.db!")


if __name__ == '__main__':
    add_reports_table()