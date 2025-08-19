# C20Scratch IDE

A powerful low-code IDE with API integration and script execution capabilities. Build interactive applications using visual blocks (Blockly) with automatic script parsing and dynamic form generation.

## 🚀 Features

- **Visual Block Programming**: Use Blockly to create applications with drag-and-drop blocks
- **API Integration**: Automatically generate blocks from OpenAPI specifications
- **Script Execution**: Parse Python and Bash scripts and create interactive forms
- **Dynamic Forms**: Generate HTML forms for script parameters with real-time execution
- **Real-time Preview**: See your application running in a live preview pane
- **Multi-platform Support**: Works on Linux, macOS, and Windows (via WSL)

## 📋 Quick Start

### Prerequisites

- Python 3.x
- Node.js (for some dependencies)
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd c20scratch
   ```

2. **Quick setup** (recommended):
   ```bash
   make quickstart
   ```

3. **Manual setup**:
   ```bash
   # Install system dependencies and Python environment
   make install
   
   # Or install only Python environment (no sudo)
   make install-python
   
   # Setup project configuration
   make setup
   ```

### Running the Application

```bash
# Start the development server
make start

# Or start with auto-reload for development
make dev
```

The IDE will be available at: http://127.0.0.1:5005

## 🛠️ Available Make Commands

Run `make help` to see all available commands:

### Setup & Installation
- `make install` - Full installation (system packages + Python environment)
- `make install-system` - Install only system packages (requires sudo)
- `make install-python` - Install only Python environment (no sudo)
- `make setup` - Setup project environment and configuration
- `make quickstart` - Quick setup and start for new users

### Development
- `make start` - Start the Flask development server
- `make dev` - Start development server with auto-reload
- `make stop` - Stop all Python services on configured port
- `make status` - Check status of services on configured port

### Scripts & Deployment
- `make scripts` - List available scripts and their parameters
- `make process-data ARGS="input.csv 0.8"` - Run data processing script
- `make deploy ENV=staging VERSION=1.0.0` - Deploy to environment

### Testing & Maintenance
- `make test` - Run basic project tests
- `make lint` - Run code linting (if tools available)
- `make clean` - Clean temporary files and caches
- `make clean-venv` - Remove Python virtual environment
- `make clean-all` - Full cleanup (including virtual environment)

### Information
- `make info` - Show project information
- `make urls` - Show application URLs
- `make help` - Show all available commands

## 📁 Project Structure

```
c20scratch/
├── ide/                    # Frontend IDE application
│   └── index.html         # Main IDE interface
├── scripts/               # Executable scripts
│   ├── README.md         # Scripts documentation
│   ├── install.sh        # Installation script
│   ├── deploy.sh         # Deployment script
│   ├── stop.sh           # Service stop script
│   └── process_data.py   # Sample Python script
├── menu/                 # Menu resources and assets
├── frontend/             # Additional frontend files
├── server.py             # Flask backend server
├── requirements.txt      # Python dependencies
├── env.example          # Environment configuration template
├── Makefile            # Build and development commands
└── README.md           # This file
```

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and modify as needed:

```bash
# Port configuration for the Flask server
PORT=5005

# Other environment variables
# DEBUG=True
```

### Adding Scripts

1. **Python scripts**: Add `.py` files to the `scripts/` directory
   - Functions are automatically parsed and made available as blocks
   - Parameters are detected from function signatures

2. **Bash scripts**: Add `.sh` files to the `scripts/` directory  
   - Add parameter definitions using comments: `# param: paramname type`

## 🎯 Usage

### Creating Applications

1. **Open the IDE** at http://127.0.0.1:5005
2. **Drag blocks** from the toolbox categories:
   - **UI**: Create views and interface elements
   - **API**: Use automatically generated API blocks
   - **Scripts**: Execute local scripts with dynamic forms
3. **Preview in real-time** in the right pane
4. **Execute scripts** by filling out generated forms

### API Integration

The IDE automatically loads API blocks from OpenAPI specifications. Currently configured to load from:
- Petstore API (example): https://petstore.swagger.io/v2/swagger.json

### Script Integration

Scripts in the `scripts/` directory are automatically parsed:

**Python Example**:
```python
def process_data(input_file, threshold=0.5):
    """Process data with given threshold"""
    # Your processing logic here
    return f"Processed {input_file} with threshold {threshold}"
```

**Bash Example**:
```bash
#!/usr/bin/env bash
# param: env string
# param: version string

echo "Deploying to environment: $1 with version: $2"
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   make stop  # Stop services on configured port
   ```

2. **Python dependencies missing**:
   ```bash
   make install-python  # Reinstall Python environment
   ```

3. **Permission errors**:
   ```bash
   make install-python  # Skip system packages, use Python-only install
   ```

### Logs and Debugging

- Check browser console for JavaScript errors
- Flask server logs appear in the terminal where you ran `make start`
- Use `make status` to check if services are running

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `make test`
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🔗 Additional Resources

- [Scripts Documentation](scripts/README.md) - Detailed script setup and usage
- [Blockly Documentation](https://developers.google.com/blockly) - Visual programming blocks
- [Flask Documentation](https://flask.palletsprojects.com/) - Backend framework