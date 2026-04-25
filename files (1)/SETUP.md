# Second Brain — Infrastructure & Setup Guide

## What This Guide Covers

Everything you need to get the local development environment running on a Mac mini M4, connect to it from your MacBook Air, and have all services verified and ready before writing a single line of application code.

---

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Mac mini | M4, 16GB RAM | M4 Pro, 24GB RAM |
| Storage | 256GB SSD | 512GB SSD |
| Network | WiFi | Ethernet (for stability) |
| MacBook | Any (just for SSH/VS Code) | Any |

**16GB is sufficient for the full MVP stack.** You are not running any local LLMs. All Claude inference happens via API. The local stack (Docker + app) uses approximately 1.5–2GB RAM.

Upgrade to 32GB only if you later want to run local models via Ollama alongside the agent stack.

---

## Software Overview

### On the Mac mini (server)
| Software | Version | Purpose |
|---|---|---|
| macOS | Sequoia 15+ | Operating system |
| Homebrew | Latest | Package manager |
| Python | 3.11 | Application runtime |
| Docker Desktop | Latest | Container platform |
| Git | Latest | Version control |

### Cloud Services (no local install needed)
| Service | Free Tier | Purpose |
|---|---|---|
| Anthropic API | Pay per use | Claude LLM |
| LangSmith | Yes (free) | Tracing & observability |
| Qdrant Cloud | Yes (1GB free) | Vector store (optional — or run locally) |

---

## Files in This Package

```
second-brain-infra/
├── setup-mac-mini.sh      # Run once on Mac mini — installs everything
├── docker-compose.yml     # Qdrant + PostgreSQL local services
├── db/schema.sql          # PostgreSQL table definitions (auto-applied)
├── .env.example           # Environment variable template
└── SETUP.md               # This guide
```

---

## Step-by-Step Setup

### Step 1 — Prepare the Mac mini

Before running the setup script, do the following manually:

1. Complete macOS setup and sign into iCloud
2. Enable Screen Sharing: **System Settings → General → Sharing → Screen Sharing ON**
3. Enable Remote Login (SSH): **System Settings → General → Sharing → Remote Login ON**
4. Plug into ethernet if possible (more stable than WiFi for a server)
5. Note the Mac mini's local IP address: **System Settings → WiFi/Network → Details**

### Step 2 — Run the Setup Script

Copy this infra folder to the Mac mini (USB, AirDrop, or SCP), then:

```bash
chmod +x setup-mac-mini.sh
./setup-mac-mini.sh
```

The script will:
- Install Homebrew, Python 3.11, Node, Git
- Install Docker Desktop
- Create the project directory at `~/second-brain`
- Create a Python virtual environment with all dependencies
- Copy `.env.example` to `.env`
- Start Qdrant and PostgreSQL via Docker Compose
- Apply the PostgreSQL schema automatically
- Configure the Mac mini for always-on headless operation
- Set up auto-start for Docker Compose on boot
- Enable SSH and print your connection details

### Step 3 — Fill in API Keys

```bash
nano ~/second-brain/.env
```

Required keys for MVP:
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `LANGCHAIN_API_KEY` — from smith.langchain.com (free account)

Everything else can stay as default for local development.

### Step 4 — Connect from Your MacBook

#### Option A: SSH Terminal
```bash
ssh YOUR_USERNAME@MAC_MINI_IP
```

Add to your MacBook's `~/.ssh/config` for convenience:
```
Host secondbrain
    HostName 192.168.x.x        # your Mac mini's IP
    User your_username
    IdentityFile ~/.ssh/id_ed25519
```

Then just: `ssh secondbrain`

#### Option B: VS Code Remote SSH (Recommended)
1. Install the **Remote - SSH** extension in VS Code on your MacBook
2. Press `Cmd+Shift+P` → `Remote-SSH: Connect to Host`
3. Enter `your_username@192.168.x.x`
4. Open the folder `~/second-brain`
5. All your editing, terminal, and debugging now runs on the Mac mini

Your slow MacBook Air is now just a screen and keyboard. All compute runs on the mini.

---

## Verifying Services

After setup, confirm everything is running:

```bash
# Check Docker containers
docker compose ps

# Expected output:
# NAME                      STATUS
# second_brain_postgres     running (healthy)
# second_brain_qdrant       running (healthy)

# Test PostgreSQL
docker exec second_brain_postgres pg_isready -U brain_user -d second_brain

# Test Qdrant REST API
curl http://localhost:6333/healthz

# View Qdrant dashboard in browser (from Mac mini or via SSH tunnel)
open http://localhost:6333/dashboard
```

### SSH Tunnel to View Services from MacBook

If you want to access the Qdrant dashboard or pgAdmin from your MacBook browser:

```bash
# On your MacBook — tunnel all service ports
ssh -L 6333:localhost:6333 \
    -L 5432:localhost:5432 \
    -L 5050:localhost:5050 \
    secondbrain -N

# Then open in MacBook browser:
# Qdrant:  http://localhost:6333/dashboard
# pgAdmin: http://localhost:5050  (start with --profile tools)
```

---

## Docker Compose Reference

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# View logs for one service
docker compose logs -f postgres
docker compose logs -f qdrant

# Restart a service
docker compose restart postgres

# Start pgAdmin (optional tool)
docker compose --profile tools up -d pgadmin

# Wipe all data and start fresh (destructive!)
docker compose down -v
```

---

## PostgreSQL Schema

The schema is applied automatically on first `docker compose up`. Tables created:

| Table | Purpose |
|---|---|
| `documents` | Tracks every ingested file (status, metadata, blob path) |
| `conversations` | Each chat session |
| `messages` | Every message turn (user + assistant) with LangSmith run ID |
| `user_profile` | Extracted facts, preferences, style notes about the user |
| `ingestion_jobs` | Async queue for embedding, transcription, crawl jobs |

To connect manually:
```bash
# From Mac mini
psql postgresql://brain_user:changeme_local@localhost:5432/second_brain

# Useful queries
\dt                          -- list all tables
SELECT * FROM user_profile;  -- view extracted user facts
SELECT * FROM documents;     -- view ingested files
SELECT count(*) FROM messages; -- conversation volume
```

---

## Python Environment

```bash
# Activate virtual environment (do this every terminal session)
cd ~/second-brain
source .venv/bin/activate

# Install a new dependency
pip install some-package

# Freeze dependencies
pip freeze > requirements.txt

# Deactivate
deactivate
```

---

## Running the Application

Once API keys are filled in and services are running:

```bash
cd ~/second-brain
source .venv/bin/activate

# Run Chainlit UI (opens on port 8000)
chainlit run interface/app.py

# Access from MacBook browser via SSH tunnel:
# ssh -L 8000:localhost:8000 secondbrain -N
# Then open: http://localhost:8000
```

---

## Cost Breakdown (MVP Phase)

| Service | Type | Monthly Cost |
|---|---|---|
| Mac mini M4 16GB | One-time $599 | ~$0/month after purchase |
| Electricity (Mac mini idle) | ~6W continuous | ~$0.50/month |
| Anthropic API | Pay per use | ~$5–20 depending on usage |
| LangSmith | Free tier | $0 |
| Qdrant | Local Docker | $0 |
| PostgreSQL | Local Docker | $0 |
| **Total MVP** | | **~$5–20/month** |

Compare to cloud-only approach:
- Azure Container Apps + PostgreSQL + Qdrant Cloud ≈ $40–70/month
- Mac mini pays for itself in 9–12 months

---

## Troubleshooting

### Docker won't start
```bash
# Open Docker Desktop app manually first
open -a Docker
# Wait 30 seconds, then retry
docker compose up -d
```

### PostgreSQL connection refused
```bash
docker compose restart postgres
docker compose logs postgres  # look for errors
```

### Qdrant not responding
```bash
curl -v http://localhost:6333/healthz
docker compose restart qdrant
```

### Can't SSH from MacBook
```bash
# On Mac mini — verify SSH is enabled
sudo systemsetup -getremotelogin
# Should say: Remote Login: On

# On MacBook — test connection verbose
ssh -v your_username@MAC_MINI_IP
```

### Mac mini goes to sleep
```bash
# On Mac mini — verify power settings
pmset -g | grep sleep
# All sleep values should be 0

# Re-apply if needed
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
```

---

## Moving to Azure (Phase 3)

When you're ready to move off local Docker to Azure:

1. Create Azure PostgreSQL Flexible Server → update `DATABASE_URL` in `.env`
2. Create Azure Blob Storage account → update `AZURE_STORAGE_CONNECTION_STRING`
3. Switch to Qdrant Cloud → update `QDRANT_URL` and `QDRANT_API_KEY`
4. Deploy app to Azure Container Apps via `Dockerfile`
5. All code stays identical — only `.env` values change

The architecture is designed so local Docker and Azure use the same interface. No code changes required to migrate.
