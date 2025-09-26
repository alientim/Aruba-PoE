
---

## **create_db.py**

```python
import sqlite3

conn = sqlite3.connect("sqlite.db")
c = conn.cursor()

# Switches
c.execute("""
CREATE TABLE IF NOT EXISTS switches (
    hostname TEXT PRIMARY KEY,
    ip TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);
""")

# Devices
c.execute("""
CREATE TABLE IF NOT EXISTS devices (
    mac TEXT PRIMARY KEY,
    rpi_ip TEXT NOT NULL,
    switch_hostname TEXT NOT NULL,
    port TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (switch_hostname) REFERENCES switches(hostname)
);
""")

# Benutzer
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);
""")

conn.commit()
conn.close()
print("Datenbank sqlite.db wurde initialisiert.")
