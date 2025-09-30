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
    is_active INTEGER DEFAULT 0
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

# Settings (z.B. Prüfintervall)
c.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
""")

# Standard-Setting: Prüfintervall 5 Minuten
c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("interval_minutes", "5"))

conn.commit()
conn.close()
print("Datenbank sqlite.db wurde initialisiert inklusive Settings.")
