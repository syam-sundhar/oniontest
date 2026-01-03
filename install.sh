#!/bin/bash

set -e

# ===== Colors =====
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
RESET="\e[0m"
BOLD="\e[1m"

info() {
  echo -e "${GREEN}[+]${RESET} $1"
}

warn() {
  echo -e "${YELLOW}[!]${RESET} $1"
}

echo_box() {
  local text="$1"
  local len=${#text}
  local border=$(printf '═%.0s' $(seq 1 $((len + 2))))

  echo -e "${YELLOW}${BOLD}"
  echo "╔${border}╗"
  echo "║ ${text} ║"
  echo "╚${border}╝"
  echo -e "${RESET}"
}

# ==================

info "Updating system"
sudo apt update -y

info "Installing dependencies"
sudo apt install -y tor python3 python3-pip netcat-openbsd

info "Installing Python cryptography module (E2EE)"
pip3 install --upgrade cryptography

info "Configuring Tor Hidden Service"

HS_DIR="/var/lib/tor/terminal_chat"

sudo mkdir -p "$HS_DIR"
sudo chown -R debian-tor:debian-tor "$HS_DIR"
sudo chmod 700 "$HS_DIR"

TORRC="/etc/tor/torrc"

if ! grep -q "terminal_chat" "$TORRC"; then
  sudo bash -c "cat >> $TORRC <<EOF

HiddenServiceDir $HS_DIR/
HiddenServicePort 5555 127.0.0.1:5555
EOF"
fi

info "Restarting Tor"
sudo systemctl enable tor
sudo systemctl restart tor

sleep 5

warn "Your .onion address"

ONION_ADDR=$(sudo cat "$HS_DIR/hostname")
echo_box "$ONION_ADDR"

echo -e "${GREEN}${BOLD}[✓] Setup complete${RESET}"
