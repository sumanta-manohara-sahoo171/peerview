# add_votes_db.py
import sqlite3


def add_votes_table():
    conn = sqlite3.connect('peerview.db')
    cursor = conn.cursor()

    # The UNIQUE(post_id, user_id) constraint is the magic here.
    # It tells the database: "Never allow two rows with the same user on the same post!"
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        vote_type INTEGER NOT NULL, 
        UNIQUE(post_id, user_id),
        FOREIGN KEY (post_id) REFERENCES posts (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ Votes table successfully added to peerview.db!")


if __name__ == '__main__':
    add_votes_table()