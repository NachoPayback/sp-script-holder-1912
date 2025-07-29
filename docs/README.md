# 🎭 Prank Hub System

A silent background prank system with a **hub** (Python) and **remote** (Flutter) applications connected via NATS messaging.

## 🏗️ Architecture

```
Hub (Python - Silent Background) ←→ NATS Cloud ←→ Remote Apps (Flutter)
```

- **Hub**: Runs silently on VM, executes prank scripts, manages Git repo
- **Remotes**: Beautiful Flutter apps with animated buttons (up to 6 remotes)
- **NATS**: Secure messaging between hub and remotes
- **Git**: Silent script management and updates

## 🚀 Quick Start

### 1. Hub Setup (Python)

#### Requirements
- Python 3.8+
- Git installed
- Windows 10+ (for VM)

#### Installation

##### Option A: Using UV (Recommended - Much Faster!)
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# On Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone or download the project
cd P_Virus

# Install dependencies with UV (much faster!)
uv pip install -r requirements.txt

# Configure NATS (optional - uses demo server by default)
# Edit config.json to set your NATS URL

# Run the hub
uv run python hub.py
```

##### Option B: Using pip (Traditional)
```bash
# Clone or download the project
cd P_Virus

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure NATS (optional - uses demo server by default)
# Edit config.json to set your NATS URL

# Run the hub
python hub.py
```

**Why UV?** UV is 10-100x faster than pip for package installation and provides better dependency resolution. Installation time: UV ~3-5 seconds vs pip ~30-60 seconds.

#### First Time Setup
1. **Create Git Repository** (optional for script management):
   ```bash
   # Initialize git in scripts directory
   cd scripts
   git init
   git remote add origin https://github.com/yourusername/prank-scripts.git
   ```

2. **Test the Hub**:
   - Press `Ctrl+Alt+S+P` to show pairing code
   - Verify scripts are detected in `scripts/` folder

### 2. Remote Setup (Flutter)

#### Requirements
- Flutter 3.0+
- Dart 3.0+

#### Installation
```bash
cd remote_app

# Get dependencies
flutter pub get

# Run on desktop
flutter run -d windows  # For Windows
flutter run -d macos    # For macOS
flutter run -d linux    # For Linux

# Or build executable
flutter build windows
```

### 3. NATS Setup

#### Option A: Use Demo Server (Quick Start)
The system works immediately with the public demo server:
- No setup required
- URL: `nats://demo.nats.io:4222`

#### Option B: NATS Cloud (Recommended)
1. Sign up at [nats.io](https://nats.io/)
2. Create a connection
3. Update `config.json` with your NATS URL and credentials

## 🔗 Pairing Process

### Hub Side
1. Press `Ctrl+Alt+S+P` on the hub machine
2. A popup shows the pairing code (e.g., `PRANK-ABC123`)
3. Share this code with remote users

### Remote Side
1. Launch the remote app
2. Enter your name and the pairing code
3. Click "Connect to Hub"
4. Wait for assignment confirmation

## 🎯 Usage

### Remote Operations
- **Main Button**: Press to execute assigned prank command
- **Script Refresh**: Pull latest scripts from Git repository
- **Activity Log**: View command history and results
- **Disconnect**: Unpair from hub

### Hub Operations
- **Silent Execution**: All commands run in background
- **Git Integration**: Automatic script updates on remote request
- **Random Assignment**: Each remote gets a different command
- **Logging**: All activities logged to `logs/` directory

## 📝 Adding New Prank Scripts

### Method 1: Direct File Addition
1. Add script to `scripts/` directory
2. Supported formats: `.py`, `.ps1`, `.bat`, `.exe`
3. Scripts are auto-detected on next assignment

### Method 2: Git Repository (Recommended)
1. Push scripts to your Git repository
2. Remote users click "Refresh Scripts" button
3. Hub automatically pulls latest scripts

### Example Script Structure
```python
#!/usr/bin/env python3
"""
Example prank script
"""

def execute_prank():
    # Your prank code here
    print("Prank executed!")
    return True

if __name__ == "__main__":
    try:
        success = execute_prank()
        exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
```

## 🔧 Configuration

### Hub Configuration (`config.json`)
```json
{
  "nats_url": "nats://demo.nats.io:4222",
  "subject_prefix": "prank",
  "git_repo_url": "https://github.com/yourusername/prank-scripts.git",
  "hotkey_combo": ["ctrl", "alt", "s", "p"],
  "command_timeout": 30,
  "max_remotes": 6
}
```

### Remote Configuration
- Settings stored automatically in app
- Customizable remote names
- Persistent pairing information

## 🛠️ Development

### Project Structure
```
P_Virus/
├── hub.py                 # Main hub application
├── requirements.txt       # Python dependencies
├── config.json           # Hub configuration
├── scripts/              # Prank scripts directory
│   ├── play_sound.py
│   ├── rotate_screen.py
│   ├── fake_system_message.py
│   └── desktop_prank.ps1
├── remote_app/           # Flutter remote application
│   ├── lib/
│   │   ├── main.dart
│   │   ├── services/
│   │   ├── screens/
│   │   ├── models/
│   │   └── widgets/
│   └── pubspec.yaml
└── logs/                 # Hub logs directory
```

### Message Protocol
```json
// Remote → Hub
{
  "type": "pair",
  "remote_id": "Remote-ABC123",
  "code": "PRANK-XYZ"
}

// Hub → Remote
{
  "type": "paired",
  "success": true,
  "assigned_command": "play_sound.py",
  "remote_id": "Remote-ABC123"
}
```

## 🔒 Security Features

- **NATS Authentication**: Support for user/password or JWT tokens
- **Subject Isolation**: Each hub uses unique subject prefix
- **Local Script Execution**: No remote code execution
- **Git Integration**: Scripts managed through version control
- **Activity Logging**: Full audit trail of all operations

## 🐛 Troubleshooting

### Common Issues

#### Hub Not Responding
- Check if Python dependencies are installed
- Verify NATS connection in logs
- Ensure hotkey isn't blocked by other software

#### Remote Can't Connect
- Verify NATS URL is correct
- Check internet connection
- Try the demo server first

#### Scripts Not Updating
- Verify Git repository URL
- Check network connectivity
- Review Git credentials

### Debug Mode
```bash
# Run hub with debug logging
python hub.py --debug

# Flutter debug mode
flutter run --debug
```

## 📋 Requirements

### Hub Requirements
- Windows 10+ (VM compatible)
- Python 3.8+
- Git
- Internet connection for NATS

### Remote Requirements
- Windows/macOS/Linux
- Flutter 3.0+
- Internet connection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your prank scripts or improvements
4. Test thoroughly
5. Submit a pull request

## ⚠️ Disclaimer

This software is for educational and entertainment purposes only. Use responsibly and ensure you have permission before executing pranks on any system.

## 📄 License

MIT License - see LICENSE file for details.

---

**Happy Pranking! 🎉** 