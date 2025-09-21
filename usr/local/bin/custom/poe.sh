#!/bin/bash

USER="admin"
PASS="Expl0rer#2022"
IP_FILE="/usr/local/bin/custom/ips.list"
LOGFILE="/var/log/rpi-$(date '+%Y%m%d%H%M%S').log"

function disable_poe() {
    local switch_ip=$1
    local port=$2
    expect <<EOF
set timeout 5
spawn ssh $USER@$switch_ip

expect {
    "assword:" { send "$PASS\r"; exp_continue }
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
    local port=$2
    expect <<EOF
set timeout 5
spawn ssh $USER@$switch_ip

expect {
    "assword:" { send "$PASS\r"; exp_continue }
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
   while IFS=: read -r ip switch port hap; do
       ping -c 1 -W 2 $ip &> /dev/null
       if [ $? -ne 0 ]; then
           echo "$(date '+%Y-%m-%d %H:%M:%S') $hap ist nicht erreichbar!" >> $LOGFILE
           disable_poe $switch $port
           echo "$(date '+%Y-%m-%d %H:%M:%S') $hap PoE auf Port $port für IP $ip am Switch $switch deaktiviert." >> $LOGFILE
           sleep 2
           enable_poe $switch $port
           echo "$(date '+%Y-%m-%d %H:%M:%S') $hap PoE auf Port $port für IP $ip am Switch $switch aktiviert." >> $LOGFILE
       else
           echo "$(date '+%Y-%m-%d %H:%M:%S') $hap ist erreichbar!" >> $LOGFILE
       fi
   done < "$IP_FILE"
   sleep 300
done