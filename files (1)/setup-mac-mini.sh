#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  SECOND BRAIN — Mac Mini Setup Script
#  Run once on a fresh Mac mini to get everything configured.
#
#  Usage:
#    chmod +x setup-mac-mini.sh
#    ./setup-mac-mini.sh
#
#  What this does:
#    1. Installs Homebrew, Python, Node, Git
#    2. Installs Docker Desktop (via brew cask)
#    3. Clones the project repo
#    4. Sets up Python virtual environment
#    5. Copies .env.example to .env
#    6. Starts Docker services (Qdrant + PostgreSQL)
#    7. Configures Mac mini for always-on headless use
#    8. Sets up SSH access from your MacBook
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SECOND BRAIN — Mac Mini Setup        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 0. Pre-flight ─────────────────────────────────────────────────
if [[ "$(uname -m)" != "arm64" ]]; then
  warn "This script is optimised for Apple Silicon (M1/M2/M3/M4)."
  warn "Continuing anyway, but some steps may differ."
fi

PROJECT_DIR="$HOME/second-brain"
REPO_URL="https://github.com/YOUR_USERNAME/second-brain.git"  # update this

# ── 1. Homebrew ───────────────────────────────────────────────────
info "Checking Homebrew..."
if ! command -v brew &>/dev/null; then
  info "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add brew to PATH for Apple Silicon
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
  eval "$(/opt/homebrew/bin/brew shellenv)"
  success "Homebrew installed"
else
  success "Homebrew already installed"
fi

info "Updating Homebrew..."
brew update --quiet

# ── 2. Core Tools ─────────────────────────────────────────────────
info "Installing core tools..."

BREW_PACKAGES=(
  "python@3.11"
  "node@20"
  "git"
  "wget"
  "jq"
)

for pkg in "${BREW_PACKAGES[@]}"; do
  if brew list "$pkg" &>/dev/null; then
    success "$pkg already installed"
  else
    info "Installing $pkg..."
    brew install "$pkg" --quiet
    success "$pkg installed"
  fi
done

# Link Python 3.11
brew link python@3.11 --force 2>/dev/null || true

# ── 3. Docker Desktop ─────────────────────────────────────────────
info "Checking Docker..."
if ! command -v docker &>/dev/null; then
  info "Installing Docker Desktop..."
  brew install --cask docker --quiet
  warn "Docker Desktop installed. Please open it manually once to complete setup,"
  warn "then press ENTER to continue."
  read -r
else
  success "Docker already installed"
fi

# Wait for Docker daemon
info "Waiting for Docker daemon to start..."
MAX_WAIT=60
WAITED=0
until docker info &>/dev/null 2>&1; do
  if [[ $WAITED -ge $MAX_WAIT ]]; then
    error "Docker daemon did not start in time. Open Docker Desktop and try again."
  fi
  sleep 2
  WAITED=$((WAITED + 2))
done
success "Docker daemon is running"

# ── 4. Project Directory ──────────────────────────────────────────
info "Setting up project directory at $PROJECT_DIR..."
if [[ -d "$PROJECT_DIR/.git" ]]; then
  success "Repo already cloned at $PROJECT_DIR"
else
  if [[ "$REPO_URL" == *"YOUR_USERNAME"* ]]; then
    warn "No repo URL set. Creating directory structure manually."
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    git init
    # Create folder structure
    mkdir -p ingestion memory agents models interface observability db config tests
    success "Project directory created at $PROJECT_DIR"
  else
    info "Cloning repo..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    success "Repo cloned to $PROJECT_DIR"
  fi
fi

cd "$PROJECT_DIR"

# ── 5. Copy infra files ───────────────────────────────────────────
info "Copying infra files into project..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
  cp "$SCRIPT_DIR/docker-compose.yml" "$PROJECT_DIR/docker-compose.yml"
  success "docker-compose.yml copied"
fi

if [[ -f "$SCRIPT_DIR/db/schema.sql" ]]; then
  mkdir -p "$PROJECT_DIR/db"
  cp "$SCRIPT_DIR/db/schema.sql" "$PROJECT_DIR/db/schema.sql"
  success "schema.sql copied"
fi

# ── 6. Python Virtual Environment ────────────────────────────────
info "Setting up Python virtual environment..."
if [[ ! -d "$PROJECT_DIR/.venv" ]]; then
  python3.11 -m venv "$PROJECT_DIR/.venv"
  success "Virtual environment created"
else
  success "Virtual environment already exists"
fi

source "$PROJECT_DIR/.venv/bin/activate"

# Install core Python dependencies
info "Installing Python dependencies..."
pip install --upgrade pip --quiet

pip install --quiet \
  anthropic \
  langchain \
  langchain-anthropic \
  langchain-community \
  langchain-qdrant \
  langgraph \
  langsmith \
  qdrant-client \
  psycopg2-binary \
  sqlalchemy \
  alembic \
  chainlit \
  python-dotenv \
  unstructured \
  "unstructured[pdf]" \
  pypdf \
  python-docx \
  tiktoken \
  pydantic \
  httpx \
  asyncpg

success "Python dependencies installed"

# ── 7. Environment File ───────────────────────────────────────────
info "Setting up environment file..."
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
  if [[ -f "$SCRIPT_DIR/.env.example" ]]; then
    cp "$SCRIPT_DIR/.env.example" "$PROJECT_DIR/.env"
  else
    cat > "$PROJECT_DIR/.env" << 'EOF'
# ── Anthropic ─────────────────────────────────────────────────────
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# ── LangSmith ─────────────────────────────────────────────────────
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=second-brain

# ── Qdrant (local Docker) ─────────────────────────────────────────
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=second_brain

# ── PostgreSQL (local Docker) ─────────────────────────────────────
POSTGRES_DB=second_brain
POSTGRES_USER=brain_user
POSTGRES_PASSWORD=changeme_local
DATABASE_URL=postgresql://brain_user:changeme_local@localhost:5432/second_brain

# ── pgAdmin (optional) ────────────────────────────────────────────
PGADMIN_EMAIL=admin@secondbrain.local
PGADMIN_PASSWORD=changeme_local

# ── Azure (Phase 3) ───────────────────────────────────────────────
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER=documents
EOF
  fi
  warn "Created .env — open it and fill in your API keys before running the app:"
  warn "  nano $PROJECT_DIR/.env"
else
  success ".env already exists"
fi

# ── 8. Docker Services ────────────────────────────────────────────
info "Starting Docker services (Qdrant + PostgreSQL)..."
cd "$PROJECT_DIR"
docker compose up -d --wait

# Wait for healthy status
info "Waiting for services to be healthy..."
sleep 5

POSTGRES_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' second_brain_postgres 2>/dev/null || echo "unknown")
QDRANT_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' second_brain_qdrant 2>/dev/null || echo "unknown")

if [[ "$POSTGRES_HEALTHY" == "healthy" ]]; then
  success "PostgreSQL is healthy"
else
  warn "PostgreSQL status: $POSTGRES_HEALTHY — check with: docker compose logs postgres"
fi

if [[ "$QDRANT_HEALTHY" == "healthy" ]]; then
  success "Qdrant is healthy"
else
  warn "Qdrant status: $QDRANT_HEALTHY — check with: docker compose logs qdrant"
fi

# ── 9. Mac Mini Always-On Configuration ──────────────────────────
info "Configuring Mac mini for always-on headless operation..."

# Disable sleep entirely (requires admin)
sudo pmset -a sleep 0
sudo pmset -a disksleep 0
sudo pmset -a displaysleep 10    # display off after 10 min (saves energy)
sudo pmset -a powernap 1         # allow background tasks during display sleep
sudo pmset -a autorestart 1      # auto restart after power failure
success "Power management configured (no sleep, auto-restart on power failure)"

# Enable SSH (Remote Login)
sudo systemsetup -setremotelogin on 2>/dev/null || true
success "SSH (Remote Login) enabled"

# Enable automatic login (optional — comment out if you prefer manual login)
# Note: requires disabling FileVault or adding user to auto-login
warn "To enable automatic login: System Settings → General → Login Items & Extensions → Automatic Login"

# Set hostname for easy SSH access
DESIRED_HOSTNAME="second-brain-server"
sudo scutil --set HostName "$DESIRED_HOSTNAME"
sudo scutil --set LocalHostName "$DESIRED_HOSTNAME"
sudo scutil --set ComputerName "$DESIRED_HOSTNAME"
success "Hostname set to: $DESIRED_HOSTNAME"

# ── 10. Docker Auto-start on Boot ────────────────────────────────
info "Configuring Docker to start on login..."
# Docker Desktop handles this — just ensure it's in Login Items
open -a Docker --background 2>/dev/null || true
warn "Ensure Docker Desktop is added to Login Items:"
warn "  System Settings → General → Login Items → Add Docker"

# Create a launchd plist to auto-start docker compose on boot
PLIST_PATH="$HOME/Library/LaunchAgents/com.secondbrain.dockercompose.plist"
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.secondbrain.dockercompose</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/docker</string>
    <string>compose</string>
    <string>-f</string>
    <string>$PROJECT_DIR/docker-compose.yml</string>
    <string>up</string>
    <string>-d</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>$PROJECT_DIR</string>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/secondbrain-compose.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/secondbrain-compose-error.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH" 2>/dev/null || true
success "Docker Compose auto-start plist installed"

# ── 11. SSH Key Setup ─────────────────────────────────────────────
info "Checking SSH setup..."
if [[ ! -f "$HOME/.ssh/authorized_keys" ]]; then
  mkdir -p "$HOME/.ssh"
  touch "$HOME/.ssh/authorized_keys"
  chmod 700 "$HOME/.ssh"
  chmod 600 "$HOME/.ssh/authorized_keys"
fi

MAC_MINI_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "unknown")
success "SSH is ready. Your Mac mini IP: $MAC_MINI_IP"

echo ""
echo -e "${YELLOW}To connect from your MacBook, run:${NC}"
echo "  ssh $(whoami)@$MAC_MINI_IP"
echo ""
echo -e "${YELLOW}To add your MacBook's SSH key (passwordless login):${NC}"
echo "  On MacBook: ssh-copy-id $(whoami)@$MAC_MINI_IP"

# ── 12. Verify Services ───────────────────────────────────────────
echo ""
info "Running service verification..."

# PostgreSQL
if docker exec second_brain_postgres pg_isready -U brain_user -d second_brain &>/dev/null; then
  success "PostgreSQL responding on localhost:5432"
else
  warn "PostgreSQL not responding — run: docker compose logs postgres"
fi

# Qdrant
if curl -sf http://localhost:6333/healthz &>/dev/null; then
  success "Qdrant responding on localhost:6333"
else
  warn "Qdrant not responding — run: docker compose logs qdrant"
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup complete! Next steps:                         ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  1. Fill in API keys:                                ║${NC}"
echo -e "${GREEN}║     nano ~/second-brain/.env                         ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  2. Connect from MacBook (VS Code Remote SSH):       ║${NC}"
echo -e "${GREEN}║     Host: $(printf '%-42s' "$MAC_MINI_IP")║${NC}"
echo -e "${GREEN}║     User: $(printf '%-42s' "$(whoami)")║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  3. Services running at:                             ║${NC}"
echo -e "${GREEN}║     PostgreSQL → localhost:5432                      ║${NC}"
echo -e "${GREEN}║     Qdrant     → localhost:6333                      ║${NC}"
echo -e "${GREEN}║     Qdrant UI  → http://localhost:6333/dashboard     ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  4. Start building! Run the app:                     ║${NC}"
echo -e "${GREEN}║     source .venv/bin/activate                        ║${NC}"
echo -e "${GREEN}║     chainlit run interface/app.py                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
