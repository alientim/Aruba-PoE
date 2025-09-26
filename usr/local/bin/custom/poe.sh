#!/bin/bash

LOGFILE="/var/log/rpi-$(date '+%Y%m%d%H%M%S').log"

IP_FILE=$(python3 /srv/poe_manager/generate_ips.py)

# Intervall aus DB (Sekunden) abrufen
SLEEP=$(python3 - <<END
import sqlite3
conn = sqlite3.connect("/srv/poe_manager/sqlite.db")
row = conn.execute("SELECT value FROM settings WHERE key='check_interval'").fetchone()
conn.close()
print(row[0] if row else 300)
END
)

# Umrechnung falls nötig
SLEEP=${SLEEP:-300}  # default 300 Sekunden

function disable_poe() {
    local switch_ip=$1
    local switch_port=$2
    local username=$3
    local password=$4
    expect <<EOF
set timeout 5
spawn ssh $username@$switch_ip

expect {
    "assword:" { send "$password\r"; exp_continue }
    "Press any key" { send "\r"; exp_continue }
    -re ".*> $" { }
}
send "configure terminal\r"
expect "(config)#"
send "interface $port\r"
expect "(eth-$port)#"
send "no power-over-ethernet\r"
expect "(eth-$port)#"
send "exit\r"
expect "(config)#"
send "exit\r"
expect "#"
send "exit\r"
expect ">"
send "exit\r"
expect "Do you want to log out (y/n)?" { send "y\r" }
expect eof
EOF
}

function enable_poe() {
    local switch_ip=$1
    local switch_port=$2
    local username=$3
    local password=$4
    expect <<EOF
set timeout 5
spawn ssh $username@$switch_ip

expect {
    "assword:" { send "$password\r"; exp_continue }
    "Press any key" { send "\r"; exp_continue }
    -re ".*> $" { }
}
send "configure terminal\r"
expect "(config)#"
send "interface $port\r"
expect "(eth-$port)#"
send "power-over-ethernet\r"
expect "(eth-$port)#"
send "exit\r"
expect "(config)#"
send "exit\r"
expect "#"
send "exit\r"
expect ">"
send "exit\r"
expect "Do you want to log out (y/n)?" { send "y\r" }
expect eof
EOF
}

echo "" > $LOGFILE
while true; do
    echo "--------------------------------------------------------------------" >> $LOGFILE
    IP_FILE=$(python3 /srv/poe_manager/generate_ips.py)
    while IFS=: read -r rpi_ip dev_name switch_ip switch_hostname switch_port switch_user switch_pass; do
        ping -c 1 -W 2 "$rpi_ip" &> /dev/null
        if [ $? -ne 0 ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') $dev_name ist nicht erreichbar!" >> $LOGFILE
            disable_poe "$switch_ip" "$switch_port" "$switch_user" "$switch_pass"
            echo "$(date '+%Y-%m-%d %H:%M:%S') $dev_name PoE auf Port $switch_port am Switch $switch_hostname deaktiviert." >> $LOGFILE
            sleep 2
            enable_poe "$switch_ip" "$switch_port" "$switch_user" "$switch_pass"
            echo "$(date '+%Y-%m-%d %H:%M:%S') $dev_name PoE auf Port $switch_port am Switch $switch_hostname aktiviert." >> $LOGFILE
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') $dev_name ist erreichbar!" >> $LOGFILE
        fi
    done < "$IP_FILE"
    rm -f "$IP_FILE"
    sleep $SLEEP
done
