import sys
from argon2 import PasswordHasher
from ule.core.database import ULEDatabase


def add_user(dbname, username, password, role="user"):
    db = ULEDatabase(dbname)
    db.open()

    ph = PasswordHasher()
    hashed = ph.hash(password)

    try:
        # Insert or replace existing user
        db._conn.execute(
            "INSERT OR REPLACE INTO _users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hashed, role)
        )
        db._conn.commit()
        print(f"User '{username}' set successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python user_add.py <dbname> <username> <password>")
        sys.exit(1)
    add_user(sys.argv[1], sys.argv[2], sys.argv[3])
