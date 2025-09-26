#!/usr/bin/env python3
import sqlite3
import tempfile
import os
from app import decrypt_password, DB_PATH

def generate_ips_list():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Alle Switches laden
    switches = {row['hostname']: row for row in conn.execute("SELECT hostname, ip, username, password FROM switches")}
    
    # Alle Geräte laden
    devices = conn.execute("SELECT mac, rpi_ip, port, name, switch_hostname FROM devices").fetchall()
    conn.close()

    tmp = tempfile.NamedTemporaryFile(delete=False, mode='w', prefix='ips_', suffix='.list')
    tmp_path = tmp.name

    for dev in devices:
        switch = switches.get(dev['switch_hostname'])
        if not switch:
            continue  # Switch existiert nicht, überspringen

        password = decrypt_password(switch['password'])
        # Format: IP-Device:Hostname-Device:IP-Switch:Hostname-Switch:Port-Switch:Username-Switch:Password-Switch
        line = f"{dev['rpi_ip']}:{dev['name']}:{switch['ip']}:{switch['hostname']}:{dev['port']}:{switch['username']}:{password}\n"
        tmp.write(line)

    tmp.close()
    return tmp_path

if __name__ == "__main__":
    path = generate_ips_list()
    print(path)  # optional, gibt die Tempdatei zurück
