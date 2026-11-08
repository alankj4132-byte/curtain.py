#!/bin/bash
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y nmap enum4linux ldap-utils john smbclient rdesktop freerdp2-x11 xterm mousepad less python3-impacket evil-winrm

echo "Installing Kerbrute..."
wget -q https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64 -O /tmp/kerbrute
chmod +x /tmp/kerbrute
sudo mv /tmp/kerbrute /usr/local/bin/

echo "All dependencies installed!"
