# DeepFocus

A powerful Windows desktop application designed to help you maintain focus by blocking distracting websites and social media platforms. Built with Python and Flet framework.

## Overview

DeepFocus enables you to take control of your digital distractions by blocking access to websites at the system level. Perfect for productivity, study sessions, or maintaining digital wellness. The application modifies the Windows hosts file to redirect blocked domains, ensuring they're inaccessible across all browsers and applications.

## Key Features

- **Social Media Blocking**: Block/unblock popular platforms (Facebook, Instagram, LinkedIn, Twitter/X, YouTube, TikTok, Reddit, Snapchat)
- **Custom Domain Management**: Add and block any custom domains or websites
- **Adult Content Protection**: Automatic blocking of adult content websites
- **Password Protection**: Secure your settings with password authentication (default: `OpentheBlocker`)
- **Per-Platform Security**: Set individual passwords for each platform
- **Multilingual Interface**: Supports English and Bengali (বাংলা)
- **System Tray Integration**: Minimize to system tray with right-click menu
- **Auto-Start Option**: Launch automatically on Windows boot
- **Modern UI**: Clean, responsive interface built with Flet Material Design

## Requirements

- **OS**: Windows 10/11
- **Python**: 3.10 or higher
- **Permissions**: Administrator privileges (required for hosts file modification)

## Installation

### Prerequisites

Install UV (if not already installed):
```bash
pip install uv
```

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Pro-Sifat-Hasan/deepfocus.git
cd deepfocus
```

2. Create virtual environment and install dependencies:
```bash
uv venv && .venv\Scripts\activate && uv pip install -e .
```

## Usage

### Running from Source

**Important**: Run as Administrator to allow hosts file modification.

```bash
python -m src.main
```

### Building Windows Executable

**Automated Build (Recommended):**
```bash
.\build_windows.ps1
```

This script will:
- Run `flet build windows` automatically
- Copy all plugin DLLs
- Verify Python runtime dependencies
- Create a distribution package in `dist/DeepFocus/` folder

The distribution folder contains everything needed - just zip it and share!

**Manual Build:**
```bash
flet build windows
.\copy_plugin_dlls.ps1  # Copy plugin DLLs if install step fails
```

The executable will be located in `build/flutter/build/windows/x64/runner/Release/`. The built application automatically requests administrator privileges when launched.

### Default Credentials

- **Login Password**: `OpentheBlocker`

You can change this password in the Settings page after first login.

## How It Works

DeepFocus modifies the Windows hosts file (`C:\Windows\System32\drivers\etc\hosts`) to redirect blocked domains to `127.0.0.1`, effectively preventing access to those websites across your entire system. The application:

- Creates automatic backups before modifying the hosts file
- Tracks blocked/unblocked state in local settings
- Requires administrator privileges for security
- Provides an intuitive interface for managing blocks

## Project Structure

```
deepfocus/
├── src/
│   ├── main.py              # Application entry point
│   ├── config/              # Configuration and constants
│   ├── core/                # Core functionality (blocker, auth, hosts)
│   ├── ui/                  # User interface components
│   └── utils/               # Utilities (language, system integration)
├── build-templates/         # Flet build templates
├── pyproject.toml           # Project configuration
└── README.md
```

## Security

- Passwords are securely hashed using PBKDF2 with SHA-256
- All settings stored locally in JSON format
- Administrator privileges required for system-level blocking

## Troubleshooting

**Permission Denied Errors**
- Ensure the application is running with Administrator privileges
- Right-click the executable and select "Run as administrator"

**Websites Not Blocking**
- Verify the application has Administrator privileges
- Clear your browser's DNS cache
- Restart the application

**Language Settings**
- Restart the application after changing language settings

## License

Created by Sifat for NeuroBrain.

## Disclaimer

This software is provided as-is. Use at your own risk. Always ensure you have backups of your hosts file before making modifications.
