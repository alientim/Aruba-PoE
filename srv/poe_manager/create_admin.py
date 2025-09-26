#!/usr/bin/env python3
import sqlite3
from getpass import getpass
from flask_bcrypt import Bcrypt

DB_PATH = "/srv/poe_manager/sqlite.db"
bcrypt = Bcrypt()

def main():
    username = input("Admin-Benutzername: ")
    password = getpass("Passwort: ")
    password_confirm = getpass("Passwort bestätigen: ")

    if password != password_confirm:
        print("Passwörter stimmen nicht überein!")
        return

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                    (username, pw_hash, 1))
        conn.commit()
        print(f"Admin-Benutzer '{username}' erfolgreich angelegt.")
    except sqlite3.IntegrityError:
        print("Benutzername existiert bereits!")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
