import sqlite3
import os

# Connect to the database
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'peerview.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("--- Checking Current Users ---")
users = conn.execute("SELECT id, username, email, role FROM users").fetchall()

if not users:
    print("❌ ERROR: Your database is completely empty! Go to the website and Sign Up first.")
else:
    for u in users:
        print(f"Found User -> Username: {u['username']} | Email: {u['email']} | Role: {u['role']}")

    # Automatically promote the very first user in the database
    first_user_email = users[0]['email']
    print(f"\nAttempting to auto-promote: {first_user_email}...")

    conn.execute("UPDATE users SET role = 'admin' WHERE email = ?", (first_user_email,))
    conn.commit()

    print("✅ SUCCESS: User has been promoted to ADMIN!")
    print("👉 Next Step: Go to your browser, click 'Logout', and log back in to get your Admin token.")

conn.close()