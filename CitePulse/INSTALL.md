# CitePulse - Server Installation Guide

This guide walks through installing CitePulse and Ollama on a fresh Ubuntu Server.

By the end, CitePulse will be running and accessible to every device on your local network.

---

## Prerequisites

- Ubuntu Server 20.04 or later (22.04 / 24.04 recommended)
- At least 8 GB of RAM (Ollama + the Mistral model need ~4 GB; Docker services need ~2 GB)
- At least 20 GB of free disk space
- A user account with `sudo` privileges
- Network connectivity (to pull Docker images and the Ollama model)

---

## Step 1 — Install Docker

```bash
# Install Docker using the official convenience script
curl -fsSL https://get.docker.com | sh

# Allow your user to run Docker without sudo
sudo usermod -aG docker $USER

# Apply the group change (or log out and back in)
newgrp docker

# Verify
docker --version
docker compose version
```

If `docker compose version` fails, install the Compose plugin manually:

```bash
sudo apt-get update
sudo apt-get install -y docker-compose-plugin
```

---

## Step 2 — Install Ollama

Ollama runs **on the host** (not inside Docker) so it can use the server's GPU if available.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull the Mistral model (this downloads ~4 GB)
ollama pull mistral
```

Verify it is running:

```bash
ollama list
# Should show "mistral" in the output

curl http://localhost:11434/api/tags
# Should return JSON listing the mistral model
```

### Configure Ollama to accept connections from Docker

By default Ollama only listens on `127.0.0.1`. The CitePulse API container needs to reach it, so Ollama must listen on all interfaces (or at least the Docker bridge).

```bash
# Edit the Ollama systemd service
sudo systemctl edit ollama
```

In the editor that opens, add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

Save and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify:

```bash
curl http://localhost:11434/api/tags   # should still work
```

---

## Step 3 — Get the CitePulse source code

Transfer the CitePulse project folder to the server. Common methods:

```bash
# Option A: Git clone (if hosted in a repo)
git clone <your-repo-url> CitePulse
cd CitePulse

# Option B: SCP from another machine
scp -r /path/to/CitePulse user@server-ip:~/CitePulse
ssh user@server-ip
cd CitePulse
```

---

## Step 4 — Configure environment variables

```bash
# Create the .env file from the template
cp .env.example .env
```

Open `.env` in a text editor (`nano .env`) and make the following changes:

### 4a — Set the JWT secret

Replace the placeholder with a random secret:

```bash
# Generate a random secret and print it
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the output into `.env`:

```
JWT_SECRET=<paste-your-generated-secret-here>
```

### 4b — Configure Ollama (local AI)

Comment out the Mistral Cloud key and enable the Ollama settings. Your `.env` should look like this:

```
# --- Mistral AI (choose ONE option) ---

# Option 1: Mistral Cloud API — COMMENTED OUT
# MISTRAL_API_KEY=your-mistral-api-key-here
# MISTRAL_MODEL=mistral-small-latest

# Option 2: Local Ollama — ENABLED
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral
```

> **Important:** Use `http://host.docker.internal:11434` as the URL. This special
> hostname lets Docker containers reach services running on the host machine.
>
> On older Docker versions where `host.docker.internal` is not supported,
> use the server's LAN IP address instead (e.g., `http://192.168.1.50:11434`).

### 4c — (Optional) Add a Semantic Scholar API key

A free API key raises the rate limit from 100 to 300 requests per minute. Get one at https://www.semanticscholar.org/product/api and add it:

```
SEMANTIC_SCHOLAR_API_KEY=your-key-here
```

### 4d — Leave everything else as-is

The remaining defaults are correct for Docker deployment:

```
DATABASE_URL=postgresql+asyncpg://citepulse:citepulse_password@localhost:5432/citepulse
CORS_ORIGINS=*
```

(Docker Compose overrides `DATABASE_URL` internally to point at the `db` container.)

---

## Step 5 — Start CitePulse

```bash
docker compose up -d --build
```

This builds and starts three containers:

| Container | Description             | Port |
|-----------|-------------------------|------|
| `db`      | PostgreSQL 16 database  | 5432 |
| `api`     | FastAPI backend         | 8000 |
| `ui`      | Streamlit frontend      | 8501 |

The first build takes a few minutes to download base images and install Python packages.

### Verify everything is running

```bash
# Check container status — all three should show "Up" and "(healthy)"
docker compose ps

# Check the API is responding
curl http://localhost:8000/

# Check the frontend is responding
curl -s http://localhost:8501 | head -5
```

### View logs

```bash
# All services
docker compose logs -f

# Just the API
docker compose logs -f api

# Just the frontend
docker compose logs -f ui
```

---

## Step 6 — Find the server's IP address

```bash
hostname -I | awk '{print $1}'
```

This prints the LAN IP (e.g., `192.168.1.50`). Share this with users — they will access CitePulse at:

```
http://<server-ip>:8501
```

---

## Automated setup (alternative to Steps 1-5)

If you prefer a one-command install, the included `setup.sh` script handles Docker installation, `.env` creation, and starting the services:

```bash
chmod +x setup.sh
./setup.sh
```

> **Note:** `setup.sh` does not install Ollama. You still need to complete
> Step 2 (Install Ollama) and Step 4b (configure `OLLAMA_BASE_URL` in `.env`)
> manually, then restart the services with `docker compose up -d`.

---

## Managing the server

### Stop CitePulse

```bash
docker compose down
```

### Start CitePulse

```bash
docker compose up -d
```

### Restart after changing `.env`

```bash
docker compose down
docker compose up -d --build
```

### Update CitePulse (after pulling new code)

```bash
docker compose down
docker compose up -d --build
```

### Reset the database

```bash
docker compose down -v    # -v removes the database volume
docker compose up -d --build
```

> **Warning:** This deletes all user accounts and analysis history.

### View database contents

```bash
docker compose exec db psql -U citepulse -d citepulse -c "SELECT id, email, full_name FROM users;"
```

---

## Troubleshooting

### "Cannot connect to the Docker daemon"

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### API container keeps restarting

Check logs:

```bash
docker compose logs api
```

Common causes:
- `.env` file is missing — run `cp .env.example .env` and configure it
- Database is not ready yet — wait 30 seconds and check again; the API waits for a healthy database before starting

### Ollama model not responding

```bash
# Check Ollama is running
sudo systemctl status ollama

# Check it's listening on all interfaces
curl http://localhost:11434/api/tags

# From inside the API container, test connectivity
docker compose exec api curl http://host.docker.internal:11434/api/tags
```

If the container cannot reach Ollama, replace `host.docker.internal` in `.env` with the server's actual LAN IP address.

### "Permission denied" when running Docker

```bash
sudo usermod -aG docker $USER
# Then log out and log back in
```

### Port 8501 or 8000 already in use

```bash
# Find what is using the port
sudo lsof -i :8501
# Kill it or change the port in docker-compose.yml
```

---

## Using Mistral Cloud instead of Ollama

If you prefer the Mistral Cloud API instead of running Ollama locally:

1. Get an API key at https://console.mistral.ai/
2. Edit `.env`:

```
MISTRAL_API_KEY=your-api-key-here
MISTRAL_MODEL=mistral-small-latest

# Comment out Ollama lines
# OLLAMA_BASE_URL=http://host.docker.internal:11434
# OLLAMA_MODEL=mistral
```

3. Restart: `docker compose down && docker compose up -d`

With this option you do not need Ollama installed at all.
