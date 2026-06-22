#!/usr/bin/env bash
# Exit on error
set -e

echo "==> Updating system packages..."
sudo apt-get update

echo "==> Installing essential dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    jq \
    sqlite3 \
    build-essential \
    ca-certificates \
    lsb-release \
    gnupg

echo "==> Installing Docker..."
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Packages sources list
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Adding vagrant user to docker group..."
sudo usermod -aG docker $USER

echo "==> Installing Python dependencies globally (optional but good for lab)"
pip3 install --upgrade pip

echo "==> Setup Complete!"
