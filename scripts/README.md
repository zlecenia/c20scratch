# Scripts Guide (Linux, macOS, Windows)

This folder contains helper scripts for setting up the project and processing the PDF into PNG pages.

- `install.sh` – sets up system dependencies (Linux distros), Python venv, and project requirements.

Supported systems
- Linux: Debian/Ubuntu (apt), Fedora (dnf), RHEL/CentOS (yum), Arch (pacman), openSUSE (zypper), Alpine (apk)
- macOS: Homebrew (brew) is supported by `install.sh`
- Windows: WSL (Ubuntu) recommended, or Git Bash/PowerShell with manual dependencies

If you use Windows, the recommended path is WSL (Windows Subsystem for Linux) or Git Bash to run these scripts.

## 1) Installation

### Linux (Debian/Ubuntu, Fedora, RHEL/CentOS, Arch, openSUSE, Alpine)
- The installer auto-detects your package manager (`apt`, `dnf`, `yum`, `pacman`, `zypper`, `apk`).
- What it does:
  - Installs: Python 3 + venv, poppler-utils (pdftoppm), ImageMagick, jq
  - Creates Python virtualenv in `backend/.venv` and installs `backend/requirements.txt`
  - Creates `.env` from `env.example` if missing

Run (may ask for sudo password):
```bash
bash scripts/install.sh
```

Skip system packages (no sudo), only Python env + requirements:
```bash
bash scripts/install.sh --skip-system
# or
SKIP_SYSTEM=1 bash scripts/install.sh
```

### macOS
- Use Homebrew to install dependencies:
```bash
# Install Homebrew if needed: https://brew.sh/
brew update
brew install python poppler imagemagick jq
```
- Or simply run the installer on macOS (Homebrew will be auto-detected, no sudo required):
```bash
bash scripts/install.sh
```
- Create venv and install Python deps:
```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt
```
Notes:
- ImageMagick on macOS sometimes exposes `magick` instead of legacy `convert/mogrify`. Our script supports both (`magick mogrify` fallback).
- We process only PNGs with ImageMagick, so no PDF policy changes are required.
