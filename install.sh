#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

clear

# Function to print status with a checkmark
print_status() {
    echo -e "${GREEN}✔${NC} ${1} completed."
}

# Update and setup system and packages
echo -e "${RED}→${NC} Starting System Update..." | tee -a /var/log/install
sudo apt-get update >>/var/log/install 2>&1 && print_status "System Update"
sudo apt-get full-upgrade -y >>/var/log/install 2>&1 && print_status "System Upgrade"
sudo rm -rf /var/lib/apt/lists/* >>/var/log/install 2>&1 && print_status "Clear cache"

# Copy required files
echo -e "${RED}→${NC} Copy requiered files..." | tee -a /var/log/install
sudo mkdir -p /usr/local/bin/custom
declare -A files=(
    ["/root/aruba-poe/etc/systemd/system/rpi-check-restart.service"]="/etc/systemd/system/rpi-check-restart.service"
    ["/root/aruba-poe/etc/systemd/system/rpi-check-restart.timer"]="/etc/systemd/system/rpi-check-restart.timer"
    ["/root/aruba-poe/etc/systemd/system/rpi-check.service"]="/etc/systemd/system/rpi-check.service"
    ["/root/aruba-poe/usr/local/bin/custom/poe.sh"]="/usr/local/bin/custom/poe.sh"
    ["/root/aruba-poe/usr/local/bin/custom/ips.list"]="/usr/local/bin/custom/ips.list"
)
RSYNC_OPTS="-a --numeric-ids --info=progress2 --no-owner --no-group"
for src in "${!files[@]}"; do
    dst="${files[$src]}"
    echo "Copying $src to $dst..."
    sudo rsync $RSYNC_OPTS "$src" "$dst" >>/var/log/install 2>&1 && print_status "$src copied to $dst"
done
print_status "All files have been successfully copied"

# Disable root
echo -e "${RED}→${NC} Disabling root login..." | tee -a /var/log/install
sudo tee /etc/ssh/sshd_config >/dev/null << 'EOF'
PermitRootLogin no
EOF
sudo passwd -l root >>/var/log/install 2>&1 && print_status "Root login disabled"

# Configure services
echo -e "${RED}→${NC} Configure services..." | tee -a /var/log/install
sudo systemctl daemon-reload >>/var/log/install 2>&1 && print_status "Daemon reloaded"
sudo systemctl enable rpi-check.service rpi-check-restart.timer >>/var/log/install 2>&1 && print_status "Services enabled"

# Clean
echo -e "${RED}→${NC} Cleaning up installer..." | tee -a /var/log/install
sudo rm -rf ./aruba-poe >>/var/log/install 2>&1 && print_status "Installer cleaned up"

# Finish
echo -e "${GREEN}✔${NC} Installation complete. Press any key to exit..." | tee -a /var/log/install 2>&1
read -n 1 -s
