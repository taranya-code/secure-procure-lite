#!/usr/bin/env bash
# =============================================================================
# SecureProcure Lite — Dev Server Manager
#
# Usage:
#   ./procure-lite.sh start              Start the app (auto-installs everything)
#   ./procure-lite.sh stop               Stop the server
#   ./procure-lite.sh restart            Stop then start
#   ./procure-lite.sh status             Show running status
#   ./procure-lite.sh logs               Show last 50 log lines
#   ./procure-lite.sh install-python     Install Python 3 via Homebrew / apt
#   ./procure-lite.sh install-deps       Create venv and install pip packages
#   ./procure-lite.sh validate           Run all pre-flight checks and report
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PID_FILE="$SCRIPT_DIR/.pids/app.pid"
LOG_FILE="$SCRIPT_DIR/.logs/app.log"
PORT="${PORT:-5001}"
MIN_PY_MINOR=10   # require Python 3.10+

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${BOLD}[SecureProcure Lite]${RESET} $*"; }
ok()   { echo -e "  ${GREEN}✓${RESET} $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $*"; }
err()  { echo -e "  ${RED}✗${RESET}  $*"; }
info() { echo -e "  ${CYAN}→${RESET} $*"; }
sep()  { echo -e "  ────────────────────────────────────────"; }

ensure_dirs() { mkdir -p "$SCRIPT_DIR/.pids" "$SCRIPT_DIR/.logs" "$SCRIPT_DIR/data"; }

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

port_in_use() { lsof -i :"$1" -t >/dev/null 2>&1; }

# ── Detect OS ────────────────────────────────────────────────────────────────
detect_os() {
  case "$(uname -s)" in
    Darwin) echo "mac" ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl"
      else echo "linux"; fi ;;
    *) echo "unknown" ;;
  esac
}

# ── Python helpers ───────────────────────────────────────────────────────────
python_ok() {
  local py
  py=$(command -v python3 2>/dev/null || true)
  [[ -z "$py" ]] && return 1
  local minor
  minor=$(python3 -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
  [[ "$minor" -ge "$MIN_PY_MINOR" ]]
}

python_version() {
  python3 -c 'import sys; v=sys.version_info; print(f"3.{v.minor}.{v.micro}")' 2>/dev/null || echo "unknown"
}

# ── install-python ───────────────────────────────────────────────────────────
cmd_install_python() {
  echo ""
  echo -e "${BOLD}${BLUE}Installing Python 3${RESET}"
  sep

  if python_ok; then
    ok "Python $(python_version) already installed — nothing to do."
    echo ""; return 0
  fi

  local os
  os=$(detect_os)

  case "$os" in
    mac)
      info "macOS detected."
      if command -v brew &>/dev/null; then
        info "Homebrew found — running: brew install python"
        brew install python
      else
        info "Homebrew not found — installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Add brew to PATH for Apple Silicon
        if [[ -f /opt/homebrew/bin/brew ]]; then
          eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        info "Installing Python via Homebrew..."
        brew install python
      fi
      ;;
    linux|wsl)
      info "Linux detected."
      if command -v apt-get &>/dev/null; then
        info "Running: sudo apt-get install -y python3 python3-venv python3-pip"
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-venv python3-pip
      elif command -v dnf &>/dev/null; then
        info "Running: sudo dnf install -y python3"
        sudo dnf install -y python3
      elif command -v yum &>/dev/null; then
        info "Running: sudo yum install -y python3"
        sudo yum install -y python3
      else
        err "Could not detect package manager (apt/dnf/yum)."
        info "Please install Python 3.10+ manually from https://www.python.org/downloads/"
        exit 1
      fi
      ;;
    *)
      err "Unsupported OS. Please install Python 3.10+ manually."
      info "Download from: https://www.python.org/downloads/"
      exit 1
      ;;
  esac

  echo ""
  if python_ok; then
    ok "Python $(python_version) installed successfully."
  else
    err "Installation ran but python3 3.10+ still not found."
    info "You may need to open a new terminal session and try again."
    exit 1
  fi
  echo ""
}

# ── install-deps ─────────────────────────────────────────────────────────────
cmd_install_deps() {
  echo ""
  echo -e "${BOLD}${BLUE}Installing Dependencies${RESET}"
  sep

  if ! python_ok; then
    err "Python 3.10+ is required first. Run:  ./procure-lite.sh install-python"
    exit 1
  fi

  ok "Python $(python_version) found"

  # Create venv if missing
  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    ok "Virtualenv created at venv/"
  else
    ok "Virtualenv already exists"
  fi

  # Activate and install
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"

  info "Upgrading pip..."
  pip install -q --upgrade pip

  info "Installing packages from requirements.txt..."
  pip install -q -r "$SCRIPT_DIR/requirements.txt"
  ok "All dependencies installed"
  echo ""
}

# ── validate ─────────────────────────────────────────────────────────────────
cmd_validate() {
  echo ""
  echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${BLUE}║   SecureProcure Lite — Pre-flight Check  ║${RESET}"
  echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════╝${RESET}"
  echo ""

  local all_ok=true

  # 1. Python
  if python_ok; then
    ok "Python $(python_version) — OK"
  else
    err "Python 3.10+ not found"
    info "Fix: ./procure-lite.sh install-python"
    all_ok=false
  fi

  # 2. Virtualenv
  if [[ -d "$VENV_DIR" ]]; then
    ok "Virtualenv — OK (venv/)"
  else
    err "Virtualenv not found"
    info "Fix: ./procure-lite.sh install-deps"
    all_ok=false
  fi

  # 3. Dependencies
  if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    if python3 -c "import flask, flask_login, flask_wtf, sqlalchemy, werkzeug" 2>/dev/null; then
      ok "Python packages (Flask, SQLAlchemy, …) — OK"
    else
      err "Some pip packages are missing"
      info "Fix: ./procure-lite.sh install-deps"
      all_ok=false
    fi
  fi

  # 4. Database connectivity
  if [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
    cd "$SCRIPT_DIR"
    local user_count
    user_count=$(python3 -c "
from app import create_app
from app.models import User
app = create_app()
with app.app_context():
    print(User.query.count())
" 2>/dev/null || echo "error")
    if [[ "$user_count" == "error" ]]; then
      err "Database not accessible"
      info "Fix: ./procure-lite.sh start  (will init DB automatically)"
      all_ok=false
    else
      ok "Database — OK ($user_count users)"
    fi
  fi

  # 5. Port availability
  if port_in_use "$PORT"; then
    if is_running; then
      ok "Port $PORT — in use by this app (server is running)"
    else
      warn "Port $PORT — in use by another process"
      info "Fix: lsof -ti:$PORT | xargs kill  or change PORT= env var"
    fi
  else
    ok "Port $PORT — available"
  fi

  # 6. Server process
  echo ""
  if is_running; then
    ok "Server — RUNNING (PID $(cat "$PID_FILE"))  →  http://localhost:${PORT}"
  else
    warn "Server — NOT running"
    info "Start: ./procure-lite.sh start"
  fi

  echo ""
  if $all_ok; then
    echo -e "  ${GREEN}${BOLD}All checks passed.${RESET} Ready to run."
  else
    echo -e "  ${RED}${BOLD}Some checks failed.${RESET} See fixes above, or run:"
    echo -e "  ${CYAN}./procure-lite.sh install-python${RESET}   — install Python"
    echo -e "  ${CYAN}./procure-lite.sh install-deps${RESET}     — install pip packages"
    echo -e "  ${CYAN}./procure-lite.sh start${RESET}            — start app (auto-fixes everything)"
  fi
  echo ""
}

# ── Internal: ensure Python + venv + deps are present, auto-install if not ──
ensure_python() {
  if ! python_ok; then
    warn "Python 3.10+ not found — attempting auto-install..."
    cmd_install_python
    if ! python_ok; then
      err "Auto-install failed. Please install Python 3.10+ manually."
      info "  Mac:   brew install python"
      info "  Linux: sudo apt install python3 python3-venv"
      info "  Any:   https://www.python.org/downloads/"
      exit 1
    fi
  fi
}

ensure_deps() {
  local needs_install=false

  if [[ ! -d "$VENV_DIR" ]]; then needs_install=true; fi

  if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
    python3 -c "import flask, flask_login, flask_wtf, sqlalchemy" 2>/dev/null || needs_install=true
  else
    needs_install=true
  fi

  if $needs_install; then
    info "Dependencies not ready — running install-deps..."
    cmd_install_deps
  else
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    info "Installing/checking dependencies..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
    ok "Dependencies ready"
  fi
}

setup_db() {
  source "$VENV_DIR/bin/activate"
  cd "$SCRIPT_DIR"

  info "Initialising database..."
  if python3 -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
" >> "$LOG_FILE" 2>&1; then
    ok "Database ready"
  else
    err "Database init failed — check $LOG_FILE"
    exit 1
  fi

  info "Checking demo data..."
  local user_count
  user_count=$(python3 -c "
from app import create_app
from app.models import User
app = create_app()
with app.app_context():
    print(User.query.count())
" 2>/dev/null || echo "0")

  if [[ "$user_count" == "0" ]]; then
    info "Seeding demo data..."
    if python3 -c "
from app import create_app
from app.seed import seed_demo_data
app = create_app()
with app.app_context():
    seed_demo_data()
" >> "$LOG_FILE" 2>&1; then
      ok "Demo data seeded"
    else
      warn "Seed failed — check $LOG_FILE"
    fi
  else
    ok "Database has data ($user_count users)"
  fi
}

# ── Commands ─────────────────────────────────────────────────────────────────
cmd_start() {
  ensure_dirs

  echo ""
  echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${BLUE}║   SecureProcure Lite — Starting Up       ║${RESET}"
  echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════╝${RESET}"
  echo ""

  if is_running; then
    warn "Already running (PID $(cat "$PID_FILE"))"
    cmd_status; return 0
  fi

  if port_in_use "$PORT"; then
    err "Port $PORT is already in use."
    info "Run: lsof -ti:$PORT | xargs kill   to free the port"
    exit 1
  fi

  ensure_python
  ensure_deps
  setup_db

  echo ""
  log "Starting Flask server..."
  source "$VENV_DIR/bin/activate"
  cd "$SCRIPT_DIR"

  nohup python3 run.py >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  ok "Server started (PID $(cat "$PID_FILE"))"

  local elapsed=0
  printf "  ${CYAN}→${RESET} Waiting for server"
  while ! port_in_use "$PORT"; do
    sleep 1; elapsed=$((elapsed+1)); printf "."
    if [[ $elapsed -ge 20 ]]; then
      echo ""; err "Server did not start — check $LOG_FILE"; exit 1
    fi
  done
  echo ""

  echo ""
  echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${GREEN}║   SecureProcure Lite is ready!               ║${RESET}"
  echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════╣${RESET}"
  echo -e "${BOLD}${GREEN}║${RESET}  App:   ${CYAN}http://localhost:${PORT}${RESET}               ${BOLD}${GREEN}║${RESET}"
  echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════╣${RESET}"
  echo -e "${BOLD}${GREEN}║${RESET}  Login: admin@demo.com / password123         ${BOLD}${GREEN}║${RESET}"
  echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════╣${RESET}"
  echo -e "${BOLD}${GREEN}║${RESET}  Stop:  ./procure-lite.sh stop               ${BOLD}${GREEN}║${RESET}"
  echo -e "${BOLD}${GREEN}║${RESET}  Logs:  ./procure-lite.sh logs               ${BOLD}${GREEN}║${RESET}"
  echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════╝${RESET}"
  echo ""

  if [[ "$(uname)" == "Darwin" ]]; then
    open "http://localhost:${PORT}" 2>/dev/null || true
  elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:${PORT}" 2>/dev/null || true
  fi
}

cmd_stop() {
  echo ""
  log "Stopping SecureProcure Lite..."

  if is_running; then
    kill "$(cat "$PID_FILE")" 2>/dev/null && rm -f "$PID_FILE"
    ok "Server stopped"
  else
    warn "Server was not running"
  fi

  local pids
  pids=$(lsof -i :"$PORT" -t 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs kill 2>/dev/null || true
    ok "Cleared port $PORT"
  fi
  echo ""
}

cmd_status() {
  echo ""
  echo -e "${BOLD}SecureProcure Lite — Status${RESET}"
  echo -e "────────────────────────────────"

  if is_running; then
    echo -e "  Server  ${GREEN}● RUNNING${RESET}  PID: $(cat "$PID_FILE")  →  http://localhost:${PORT}"
  else
    if port_in_use "$PORT"; then
      echo -e "  Server  ${YELLOW}● PORT IN USE${RESET} (port $PORT occupied by another process)"
    else
      echo -e "  Server  ${RED}○ STOPPED${RESET}"
    fi
  fi

  echo ""
  echo -e "${BOLD}Logs${RESET}"
  echo -e "────────────────────────────────"
  [[ -f "$LOG_FILE" ]] && echo -e "  App: $LOG_FILE  ($(wc -l < "$LOG_FILE") lines)" || echo -e "  App: no log yet"
  echo ""
}

cmd_restart() { cmd_stop; sleep 1; cmd_start; }

cmd_logs() {
  ensure_dirs
  echo -e "${BOLD}App Logs${RESET} (last 50 lines)"
  echo "──────────────────────────────"
  [[ -f "$LOG_FILE" ]] && tail -50 "$LOG_FILE" || echo "No log yet."
}

cmd_help() {
  echo ""
  echo -e "${BOLD}SecureProcure Lite — Server Manager${RESET}"
  echo ""
  echo -e "  ${BOLD}App commands:${RESET}"
  echo -e "  ${CYAN}./procure-lite.sh start${RESET}            Start the app (auto-installs everything)"
  echo -e "  ${CYAN}./procure-lite.sh stop${RESET}             Stop the server"
  echo -e "  ${CYAN}./procure-lite.sh restart${RESET}          Stop then start"
  echo -e "  ${CYAN}./procure-lite.sh status${RESET}           Show running status"
  echo -e "  ${CYAN}./procure-lite.sh logs${RESET}             Show last 50 log lines"
  echo ""
  echo -e "  ${BOLD}Setup commands:${RESET}"
  echo -e "  ${CYAN}./procure-lite.sh install-python${RESET}   Install Python 3 via Homebrew / apt"
  echo -e "  ${CYAN}./procure-lite.sh install-deps${RESET}     Create venv and install pip packages"
  echo -e "  ${CYAN}./procure-lite.sh validate${RESET}         Run all pre-flight checks"
  echo ""
  echo -e "  ${BOLD}URL:${RESET} http://localhost:${PORT}"
  echo -e "  ${BOLD}Demo login:${RESET} admin@demo.com / password123"
  echo ""
  echo -e "  ${BOLD}First time on a new machine?${RESET}"
  echo -e "  Just run:  ${CYAN}./procure-lite.sh start${RESET}  — it handles everything automatically."
  echo ""
}

# ── Dispatch ─────────────────────────────────────────────────────────────────
COMMAND="${1:-help}"
case "$COMMAND" in
  start)            cmd_start ;;
  stop)             cmd_stop ;;
  status)           cmd_status ;;
  restart)          cmd_restart ;;
  logs)             cmd_logs ;;
  install-python)   cmd_install_python ;;
  install-deps)     cmd_install_deps ;;
  validate)         cmd_validate ;;
  help|--help|-h)   cmd_help ;;
  *)
    err "Unknown command: $COMMAND"
    cmd_help; exit 1 ;;
esac
