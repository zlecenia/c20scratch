#!/usr/bin/env bash
# Installer for local development dependencies
# - System packages: Python, pip/venv, poppler-utils (pdftoppm), ImageMagick, jq
# - Python venv in backend/.venv and pip install -r backend/requirements.txt
# - Prepare .env from env.example if missing
#
# Supported package managers: apt, dnf, yum, pacman, zypper, apk (Alpine), brew (macOS)
# Flags/Env:
#   --skip-system or SKIP_SYSTEM=1   Skip installing system packages (no sudo)
# Usage:
#   bash scripts/install.sh [--skip-system]

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

log() { printf "\033[1;34m[install]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[error]\033[0m %s\n" "$*" 1>&2; }

# Args
SKIP_SYSTEM_PACKAGES=${SKIP_SYSTEM:-0}
for a in "$@"; do
  case "$a" in
    --skip-system)
      SKIP_SYSTEM_PACKAGES=1
      ;;
  esac
done

need_sudo() {
  if [[ $EUID -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      echo sudo
    else
      err "This script requires root privileges to install system packages. Re-run as root or install sudo."
      exit 1
    fi
  else
    echo ""
  fi
}

PKG=""
if command -v apt-get >/dev/null 2>&1; then PKG=apt;
elif command -v dnf >/dev/null 2>&1;   then PKG=dnf;
elif command -v yum >/dev/null 2>&1;    then PKG=yum;
elif command -v pacman >/dev/null 2>&1; then PKG=pacman;
elif command -v zypper >/dev/null 2>&1; then PKG=zypper;
elif command -v apk >/dev/null 2>&1;   then PKG=apk;
elif command -v brew >/dev/null 2>&1;  then PKG=brew;
fi

if [[ -z "$PKG" ]]; then
  err "Unsupported system (no apt/dnf/yum/pacman/zypper/apk/brew detected)."
  exit 2
fi

SUDO=$(need_sudo)

if [[ "$SKIP_SYSTEM_PACKAGES" -eq 0 ]]; then
  log "Installing system packages using: $PKG"
  case "$PKG" in
    apt)
      $SUDO apt-get update -y
      $SUDO apt-get install -y python3 python3-venv python3-pip poppler-utils imagemagick jq
      ;;
    dnf)
      $SUDO dnf -y install python3 python3-pip poppler-utils ImageMagick jq
      ;;
    yum)
      $SUDO yum -y install python3 python3-pip poppler-utils ImageMagick jq
      ;;
    pacman)
      $SUDO pacman -Sy --noconfirm --needed python python-pip poppler imagemagick jq
      ;;
    zypper)
      $SUDO zypper refresh
      # poppler-tools provides pdftoppm on openSUSE; ImageMagick pkg name is ImageMagick
      $SUDO zypper install -y python3 python3-pip poppler-tools ImageMagick jq || true
      # venv tooling may be in a separate pkg on some variants
      $SUDO zypper install -y python3-venv python3-virtualenv || true
      ;;
    apk)
      $SUDO apk update
      # Alpine packages; python3 provides venv module on recent releases
      $SUDO apk add --no-cache python3 py3-pip poppler-utils imagemagick jq
      ;;
    brew)
      # Homebrew (macOS): do not use sudo
      brew update
      brew install python poppler imagemagick jq
      ;;
  esac

  hash -r || true

  # Verify tools
  if ! command -v pdftoppm >/dev/null 2>&1; then
    err "pdftoppm not found after install. Please install 'poppler-utils' (Debian/Fedora) or 'poppler'/'poppler-tools' for your distro."
    exit 3
  fi
  if ! command -v mogrify >/dev/null 2>&1 && ! command -v convert >/dev/null 2>&1 && ! command -v magick >/dev/null 2>&1; then
    err "ImageMagick not found after install. Please install 'imagemagick'."
    exit 4
  fi
else
  log "Skipping system packages installation (--skip-system)"
fi

# Ensure scripts are executable
chmod +x "$ROOT_DIR/scripts/pdf_to_png_rotate_crop.sh" 2>/dev/null || true

# Python environment for backend
log "Setting up Python venv in backend/.venv"
cd "$ROOT_DIR/backend"
if [[ ! -d .venv ]]; then
  if ! python3 -m venv .venv 2>/dev/null; then
    log "python3 -m venv failed. Trying virtualenv..."
    # Try to ensure virtualenv exists
    if ! command -v virtualenv >/dev/null 2>&1; then
      python3 -m pip install --user virtualenv || pip3 install --user virtualenv || true
    fi
    # Try different invocation styles
    if command -v virtualenv >/dev/null 2>&1; then
      virtualenv .venv || {
        err "Failed to create venv using virtualenv. Install python3-venv or virtualenv."
        exit 5
      }
    else
      python3 -m virtualenv .venv || {
        err "Failed to create venv. Install python3-venv or virtualenv."
        exit 5
      }
    fi
  fi
fi

# Locate pip/python inside the venv (Linux/macOS and Git Bash on Windows)
PIP_BIN="$ROOT_DIR/backend/.venv/bin/pip"
PY_BIN="$ROOT_DIR/backend/.venv/bin/python"
if [[ ! -x "$PIP_BIN" ]]; then
  PIP_BIN="$ROOT_DIR/backend/.venv/Scripts/pip.exe"
fi
if [[ ! -x "$PIP_BIN" ]]; then
  PIP_BIN="$ROOT_DIR/backend/.venv/Scripts/pip"
fi
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="$ROOT_DIR/backend/.venv/Scripts/python.exe"
fi
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="$ROOT_DIR/backend/.venv/Scripts/python"
fi

"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install -r requirements.txt

# Prepare .env
if [[ ! -f "$ROOT_DIR/.env" && -f "$ROOT_DIR/env.example" ]]; then
  cp "$ROOT_DIR/env.example" "$ROOT_DIR/.env"
  log "Created .env from env.example"
fi

log "All set. You can now:"
cat <<EOF
  - Backend (local):   $PY_BIN $ROOT_DIR/backend/app.py
  - Frontend (docker): docker compose up --build  (UI: http://localhost:3000, API: http://localhost:5000)
  - PDF → PNG script:  scripts/pdf_to_png_rotate_crop.sh menu.pdf frontend/pages/png
EOF
