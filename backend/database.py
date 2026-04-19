# database.py
import sqlite3


def get_db_connection():
    """Opens a connection to the SQLite database."""
    # Connect to the file we just generated
    conn = sqlite3.connect('peerview.db')

    # This crucial line tells SQLite to return data as dictionaries (like JSON)
    # instead of standard Python tuples. It makes formatting the API response much easier!
    conn.row_factory = sqlite3.Row

    return conn