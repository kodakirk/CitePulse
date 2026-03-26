#!/bin/bash
# CitePulse - Ubuntu Server Setup Script
# Run this on your Ubuntu server to get CitePulse running.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh

set -e

echo "============================================"
echo "  CitePulse - Ubuntu Server Setup"
echo "============================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[1/4] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "  Docker installed. You may need to log out and back in for group changes."
else
    echo "[1/4] Docker already installed."
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[2/4] Installing Docker Compose plugin..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
else
    echo "[2/4] Docker Compose already installed."
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "[3/4] Creating .env from template..."
    cp .env.example .env
    # Generate a random JWT secret
    JWT=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    sed -i "s|CHANGE_THIS_TO_A_RANDOM_SECRET|${JWT}|g" .env
    echo "  .env created. Edit it to add your Mistral API key or configure Ollama."
    echo ""
    echo "  For Mistral Cloud: set MISTRAL_API_KEY in .env"
    echo "  For local Ollama:  install ollama, pull mistral model, set OLLAMA_BASE_URL"
else
    echo "[3/4] .env already exists, skipping."
fi

# Start services
echo "[4/4] Starting CitePulse services..."
docker compose up -d --build

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "============================================"
echo "  CitePulse is running!"
echo "============================================"
echo ""
echo "  Frontend:  http://${SERVER_IP}:8501"
echo "  API:       http://${SERVER_IP}:8000"
echo "  API Docs:  http://${SERVER_IP}:8000/docs"
echo ""
echo "  Anyone on your network can access the above URLs."
echo ""
echo "  Manage with:"
echo "    docker compose logs -f    # View logs"
echo "    docker compose down       # Stop"
echo "    docker compose up -d      # Start"
echo "============================================"
