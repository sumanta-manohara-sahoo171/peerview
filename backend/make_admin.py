# make_admin.py
import sqlite3


def promote_user():
    try:
        conn = sqlite3.connect('peerview.db')
        cursor = conn.cursor()

        # We changed the username here!
        cursor.execute(
            "UPDATE users SET role = 'admin' WHERE username = 'real_admin'"
        )

        conn.commit()

        if cursor.rowcount > 0:
            print("✅ Success! 'real_admin' is now an Admin.")
        else:
            print("❌ User not found. Check the username spelling!")

        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    promote_user()