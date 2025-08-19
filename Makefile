# C20Scratch IDE Project Makefile
# Low-code IDE with API integration and script execution

# Configuration
-include .env
export

# Default values if not set in .env
PORT ?= 5005
PYTHON ?= python3
VENV_DIR ?= venv
SCRIPTS_DIR = scripts

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help install install-system install-python setup clean start stop status dev test scripts deploy

# Default target
help: ## Show this help message
	@echo "$(BLUE)C20Scratch IDE Project$(NC)"
	@echo "Low-code IDE with API integration and script execution"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;33m%-15s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Full installation (system packages + Python environment)
	@echo "$(BLUE)Installing system dependencies and Python environment...$(NC)"
	@bash $(SCRIPTS_DIR)/install.sh

install-system: ## Install only system packages (requires sudo)
	@echo "$(BLUE)Installing system packages...$(NC)"
	@bash $(SCRIPTS_DIR)/install.sh

install-python: ## Install only Python environment (no sudo required)
	@echo "$(BLUE)Installing Python environment...$(NC)"
	@bash $(SCRIPTS_DIR)/install.sh --skip-system

# Environment setup
setup: ## Setup project environment and configuration
	@echo "$(BLUE)Setting up project environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "Creating .env from env.example..."; \
		cp env.example .env; \
	fi
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating Python virtual environment..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	@echo "Installing Python dependencies..."
	@$(VENV_DIR)/bin/pip install --upgrade pip
	@$(VENV_DIR)/bin/pip install -r requirements.txt
	@echo "$(GREEN)Setup completed!$(NC)"

# Development targets
start: ## Start the Flask development server
	@echo "$(BLUE)Starting Flask server on port $(PORT)...$(NC)"
	@source $(VENV_DIR)/bin/activate && $(PYTHON) server.py

dev: ## Start development server with auto-reload
	@echo "$(BLUE)Starting development server with auto-reload...$(NC)"
	@source $(VENV_DIR)/bin/activate && FLASK_ENV=development $(PYTHON) server.py

stop: ## Stop all Python services on configured port
	@echo "$(BLUE)Stopping Python services...$(NC)"
	@bash $(SCRIPTS_DIR)/stop.sh

status: ## Check status of services on configured port
	@echo "$(BLUE)Checking services on port $(PORT)...$(NC)"
	@lsof -i :$(PORT) || echo "No services found on port $(PORT)"

# Script execution targets
scripts: ## List available scripts and their parameters
	@echo "$(BLUE)Available scripts:$(NC)"
	@echo "$(YELLOW)Python scripts:$(NC)"
	@find $(SCRIPTS_DIR) -name "*.py" -exec echo "  {}" \; || true
	@echo "$(YELLOW)Bash scripts:$(NC)"  
	@find $(SCRIPTS_DIR) -name "*.sh" -exec echo "  {}" \; || true

process-data: ## Run data processing script (example: make process-data ARGS="input.csv 0.8")
	@echo "$(BLUE)Running data processing script...$(NC)"
	@source $(VENV_DIR)/bin/activate && $(PYTHON) $(SCRIPTS_DIR)/process_data.py $(ARGS)

deploy: ## Deploy to environment (example: make deploy ENV=staging VERSION=1.0.0)
	@echo "$(BLUE)Running deployment script...$(NC)"
	@bash $(SCRIPTS_DIR)/deploy.sh $(ENV) $(VERSION)

# Testing and development
test: ## Run basic project tests
	@echo "$(BLUE)Running basic project tests...$(NC)"
	@echo "Testing Flask server import..."
	@source $(VENV_DIR)/bin/activate && $(PYTHON) -c "import server; print('✓ Server imports correctly')"
	@echo "Testing script parsing..."
	@source $(VENV_DIR)/bin/activate && $(PYTHON) -c "import server; print('✓ Script scanning works:', len(server.scan_scripts()), 'scripts found')"
	@echo "$(GREEN)Basic tests passed!$(NC)"

lint: ## Run code linting (if tools are available)
	@echo "$(BLUE)Running code linting...$(NC)"
	@source $(VENV_DIR)/bin/activate && python -m flake8 server.py $(SCRIPTS_DIR)/*.py 2>/dev/null || echo "flake8 not installed, skipping..."

# Cleanup targets
clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-venv: ## Remove Python virtual environment
	@echo "$(YELLOW)Removing Python virtual environment...$(NC)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)Virtual environment removed!$(NC)"

clean-all: clean clean-venv ## Full cleanup (including virtual environment)
	@echo "$(GREEN)Full cleanup completed!$(NC)"

# Information targets
info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "  Project: C20Scratch IDE"
	@echo "  Port: $(PORT)"
	@echo "  Python: $(PYTHON)"
	@echo "  Virtual Environment: $(VENV_DIR)"
	@echo "  Scripts Directory: $(SCRIPTS_DIR)"
	@echo ""
	@echo "$(BLUE)Project Structure:$(NC)"
	@tree -L 2 . 2>/dev/null || find . -maxdepth 2 -type d | head -20

urls: ## Show application URLs
	@echo "$(BLUE)Application URLs:$(NC)"
	@echo "  Main IDE: http://127.0.0.1:$(PORT)"
	@echo "  Scripts API: http://127.0.0.1:$(PORT)/scripts.json"
	@echo "  Run Script API: http://127.0.0.1:$(PORT)/run-script"

# Docker targets (if needed in future)
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t c20scratch-ide .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -p $(PORT):$(PORT) c20scratch-ide

# Quick start target
quickstart: setup ## Quick setup and start for new users
	@echo "$(GREEN)Quick start completed! Starting server...$(NC)"
	@make start
