#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet
import sqlite3
import glob, os, re

app = Flask(__name__)
app.secret_key = "309cc4d5ce1fe7486ae25cbd232bbdfe6a72539c03f0127d372186dbdc0fc928"
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

DB_PATH = "/srv/poe_manager/sqlite.db"

class User(UserMixin):
    def __init__(self, id_, username, is_admin):
        self.id = id_
        self.username = username
        self.is_admin = is_admin

def get_interval_seconds():
    conn = get_db_connection()
    row = conn.execute("SELECT value FROM settings WHERE key='check_interval'").fetchone()
    conn.close()
    return int(row['value']) if row else 300

with open("/srv/poe_manager/fernet.key", "rb") as f:
    fernet = Fernet(f.read())

def encrypt_password(password: str) -> str:
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_devices():
    """
    Liefert eine Liste aller Devices aus der Datenbank als Dictionaries.
    """
    conn = get_db_connection()
    devices = conn.execute("SELECT mac, rpi_ip, port, name, switch_hostname FROM devices").fetchall()
    conn.close()
    return devices

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['is_admin'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and bcrypt.check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['is_admin']))
            return redirect(url_for('index'))
        else:
            flash("Ungültiger Benutzername oder Passwort")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    devices = get_devices()  # alle Devices aus der DB
    status = load_device_status()
    
    # Standardstatus, falls Gerät im Log noch nicht auftaucht
    for d in devices:
        if d['name'] not in status:
            status[d['name']] = 'offline'

    interval_min = get_interval_seconds() // 60
    return render_template('index.html', devices=devices, status=status, interval=interval_min)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_admin:
        flash("Zugriff verweigert!")
        return redirect(url_for('index'))

    conn = get_db_connection()
    interval_row = conn.execute("SELECT value FROM settings WHERE key='check_interval'").fetchone()
    interval_min = int(interval_row['value']) // 60 if interval_row else 5  # Standard 5 Minuten

    if request.method == 'POST':
        new_interval_min = int(request.form['interval'])
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('check_interval', ?)", (new_interval_min*60,))
        conn.commit()
        flash(f"Intervall auf {new_interval_min} Minuten gesetzt.")
        interval_min = new_interval_min

    conn.close()
    return render_template('settings.html', interval=interval_min)

@app.route('/devices', methods=['GET', 'POST'])
@login_required
def devices():
    conn = get_db_connection()
    switches = conn.execute("SELECT hostname FROM switches").fetchall()

    # Inline-Add
    if request.method == 'POST' and 'add_device' in request.form:
        if not current_user.is_admin:
            flash("Zugriff verweigert!")
            return redirect(url_for('devices'))
        mac = request.form['mac']
        rpi_ip = request.form['rpi_ip']
        port = request.form['port']
        name = request.form['name']
        switch_hostname = request.form['switch_hostname']
        try:
            conn.execute("INSERT INTO devices (mac, rpi_ip, port, name, switch_hostname) VALUES (?, ?, ?, ?, ?)",
                         (mac, rpi_ip, port, name, switch_hostname))
            conn.commit()
            flash(f"Gerät {name} hinzugefügt.")
        except sqlite3.IntegrityError:
            flash("MAC existiert bereits oder Eingabefehler!")

    # Inline-Edit
    if request.method == 'POST' and 'edit_device' in request.form:
        if not current_user.is_admin:
            flash("Zugriff verweigert!")
            return redirect(url_for('devices'))
        old_mac = request.form['old_mac']
        mac = request.form['mac']
        rpi_ip = request.form['rpi_ip']
        port = request.form['port']
        name = request.form['name']
        switch_hostname = request.form['switch_hostname']
        try:
            conn.execute("""
                UPDATE devices
                SET mac=?, rpi_ip=?, port=?, name=?, switch_hostname=?
                WHERE mac=?
            """, (mac, rpi_ip, port, name, switch_hostname, old_mac))
            conn.commit()
            flash(f"Gerät {name} aktualisiert.")
        except sqlite3.IntegrityError:
            flash("MAC existiert bereits oder Eingabefehler!")

    # Inline-Delete
    if request.method == 'POST' and 'delete_device' in request.form:
        if not current_user.is_admin:
            flash("Zugriff verweigert!")
            return redirect(url_for('devices'))
        del_mac = request.form['delete_device']
        conn.execute("DELETE FROM devices WHERE mac=?", (del_mac,))
        conn.commit()
        flash(f"Gerät {del_mac} gelöscht.")

    devices = conn.execute("""
        SELECT devices.mac, devices.rpi_ip, devices.port, devices.name, switches.hostname AS switch_hostname
        FROM devices
        JOIN switches ON devices.switch_hostname = switches.hostname
    """).fetchall()
    conn.close()
    interval_min = get_interval_seconds() // 60
    return render_template('devices.html', devices=devices, switches=switches)

@app.route('/switches', methods=['GET', 'POST'])
@login_required
def switches():
    conn = get_db_connection()

    # Inline-Add
    if request.method == 'POST' and 'add_switch' in request.form:
        if not current_user.is_admin:
            flash("Zugriff verweigert!")
            return redirect(url_for('switches'))
        hostname = request.form['hostname']
        ip = request.form['ip']
        username = request.form['username']
        password = encrypt_password(request.form['password'])
        try:
            conn.execute("INSERT INTO switches (hostname, ip, username, password) VALUES (?, ?, ?, ?)",
                         (hostname, ip, username, password))
            conn.commit()
            flash(f"Switch {hostname} hinzugefügt.")
        except sqlite3.IntegrityError:
            flash("Hostname existiert bereits oder Eingabefehler!")

    # Inline-Edit
    if request.method == 'POST' and 'edit_switch' in request.form:
        if not current_user.is_admin:
            flash("Zugriff verweigert!")
            return redirect(url_for('switches'))
        old_hostname = request.form['old_hostname']
        hostname = request.form['hostname']
        ip = request.form['ip']
        username = request.form['username']
        password = encrypt_password(request.form['password'])
        try:
            conn.execute("""
                UPDATE switches
                SET hostname=?, ip=?, username=?, password=?
                WHERE hostname=?
            """, (hostname, ip, username, password, old_hostname))
            conn.commit()
            flash(f"Switch {hostname} aktualisiert.")
        except sqlite3.IntegrityError:
            flash("Hostname existiert bereits oder Eingabefehler!")

    # Inline-Delete
    if request.method == 'POST' and 'delete_switch' in request.form:
        if not current_user.is_admin:
            flash("Zugriff verweigert!")
            return redirect(url_for('switches'))
        del_hostname = request.form['delete_switch']
        conn.execute("DELETE FROM switches WHERE hostname=?", (del_hostname,))
        conn.commit()
        flash(f"Switch {del_hostname} gelöscht.")

    switches = conn.execute("SELECT hostname, ip, username FROM switches").fetchall()
    conn.close()
    return render_template('switche.html', switches=switches)

@app.route("/get_log")
@login_required
def get_log():
    log_files = glob.glob("/var/log/rpi-*.log")
    if not log_files:
        return "Keine Logfiles gefunden."

    latest_log = max(log_files, key=os.path.getctime)

    try:
        with open(latest_log, "r") as f:
            return f.read()
    except Exception as e:
        return f"Fehler beim Lesen des Logs: {e}"

@app.route('/logs')
@login_required
def logs():
    # alle Logfiles mit Muster rpi-YYYYMMDDHHMMSS.log
    log_files = glob.glob("/var/log/rpi-*.log")
    if not log_files:
        return render_template('logs.html', log_content="Keine Logfiles gefunden.")

    # das neuste Logfile auswählen
    latest_log = max(log_files, key=os.path.getctime)

    try:
        with open(latest_log, "r") as f:
            log_content = f.read()
    except Exception as e:
        log_content = f"Fehler beim Lesen des Logs: {e}"

    return render_template('logs.html', log_content=log_content, log_name=os.path.basename(latest_log))

def load_device_status():
    """
    Liest das aktuellste rpi-Logfile und extrahiert den letzten Status jedes Devices.
    Gibt ein Dictionary zurück: {Device-Name: 'online'/'offline'}
    """
    status = {}
    log_files = glob.glob("/var/log/rpi-*.log")
    if not log_files:
        return status

    latest_log = max(log_files, key=os.path.getctime)

    # Jede Zeile des Logs lesen
    with open(latest_log, "r") as f:
        lines = f.readlines()

    # Regex für Ping-Ergebnisse
    online_re = re.compile(r"(\S+) ist erreichbar!")
    offline_re = re.compile(r"(\S+) ist nicht erreichbar!")

    for line in lines:
        line = line.strip()
        m_online = online_re.search(line)
        m_offline = offline_re.search(line)
        if m_online:
            status[m_online.group(1)] = 'online'
        elif m_offline:
            status[m_offline.group(1)] = 'offline'

    return status

@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    if not current_user.is_admin:
        flash("Nur Admins dürfen Benutzer verwalten!")
        return redirect(url_for("index"))

    conn = sqlite3.connect("sqlite.db")
    conn.row_factory = sqlite3.Row  # wichtig für Template
    c = conn.cursor()

    # Neues Benutzer hinzufügen
    if request.method == "POST":
        if "add_user" in request.form:
            username = request.form["username"]
            password = generate_password_hash(request.form["password"])
            is_admin = 1 if "is_admin" in request.form else 0
            try:
                c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                          (username, password, is_admin))
                conn.commit()
                flash(f"Benutzer {username} hinzugefügt!")
            except sqlite3.IntegrityError:
                flash("Benutzername existiert bereits!")

        if "delete_user" in request.form:
            user_id = request.form["delete_user"]
            c.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            flash("Benutzer gelöscht!")

        if "edit_user" in request.form:
            user_id = request.form["user_id"]
            username = request.form["username"]
            is_admin = 1 if "is_admin" in request.form else 0
            c.execute("UPDATE users SET username=?, is_admin=? WHERE id=?",
                      (username, is_admin, user_id))
            conn.commit()
            flash("Benutzer geändert!")

    # Alle Benutzer laden
    c.execute("SELECT id, username, is_admin FROM users")
    users_list = c.fetchall()
    conn.close()

    return render_template("users.html", users=users_list)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
