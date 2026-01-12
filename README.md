# SM-Blocker

A powerful desktop application for blocking social media platforms and websites on Windows. Built with Python Flet framework.

## Features

- **Platform Blocking**: Block/unblock popular social media platforms (Facebook, Instagram, LinkedIn, Twitter, YouTube, TikTok, Reddit, Snapchat)
- **Custom Domain Blocking**: Add and block custom domains
- **Adult Content Blocking**: Automatic blocking of adult content websites
- **Password Protection**: 
  - Main application password (default: `OpentheBlocker`)
  - Per-platform password protection
- **Language Support**: English and Bengali (বাংলা) interface
- **System Tray**: Minimize to system tray, right-click menu
- **Auto-Start**: Option to start automatically on Windows boot
- **Modern UI**: Clean, responsive interface using Flet Material Design

## Requirements

- Windows 10/11
- Python 3.10 or higher
- Administrator privileges (required for modifying hosts file)

## Installation

### Using UV (Recommended)

1. Install UV if not already installed:
   ```bash
   pip install uv
   ```

2. Create virtual environment:
   ```bash
   uv venv
   ```

3. Activate virtual environment:
   ```bash
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   uv pip install -e .
   ```

### Using pip

1. Create virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate virtual environment:
   ```bash
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```
   
   Or if you prefer pip:
   ```bash
   pip install -e .
   ```
   
   Note: For the `flet build windows` command to work, ensure `flet[all]` is installed which includes the CLI tools.

## Running the Application

There are several ways to run the application:

**Method 1: Using Python directly (Recommended)**
```bash
python -m src.main
```

**Method 2: Using Flet CLI (if installed)**
```bash
# Run as a module (required for relative imports)
flet run -m src.main

# OR if your current directory is the project root
flet run -m src.main --cwd .
```

**Method 3: Direct Python execution**
```bash
python src/main.py
```

**Note about execution speed:**
- Once your virtual environment is activated, all methods above use the same Python interpreter from `.venv`
- `uv` is a package manager (fast for installing packages), but running code uses Python itself
- Execution speed is identical regardless of whether you used `uv` or `pip` to install dependencies
- `flet run` just wraps Python execution with some Flet-specific setup

**Important**: 
- Run as Administrator to allow hosts file modification
- Default login password: `OpentheBlocker`

## Building Executable

To build a Windows executable:

```bash
flet build windows
```

All build configuration (product name, company, copyright, icon) is automatically loaded from `pyproject.toml`. The icon file should be placed in `src/assets/icon.png` (or `.ico`, `.bmp`, `.jpg`, `.webp` format).

### Administrator Privileges

**The built exe will automatically request administrator privileges when launched.** This is configured in `pyproject.toml` with `requested-execution-level = "requireAdministrator"`. Windows will show a UAC (User Account Control) prompt asking for permission when you run the exe. This is required for the blocking functionality to work.

**Optional:** If you want to manually embed a manifest file for additional control, you can:
1. Build the exe: `flet build windows`
2. Run the post-build script: `python build_with_manifest.py`

### Auto-Start Setup

The app includes auto-start functionality:
1. Go to **Settings** page in the app
2. Toggle **"Start on Windows Boot"** to ON
3. The app will start automatically when Windows boots
4. For executable files, it uses PowerShell to launch with elevation, ensuring admin privileges
5. The app will request administrator privileges automatically on boot

**How it works:**
- When enabled, the app registers itself in Windows Registry (`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`)
- For exe files: Uses PowerShell `Start-Process` with `-Verb RunAs` to request admin privileges
- The app will start on Windows login and automatically request admin elevation via UAC

You can also use the build script:
```bash
# Windows
build.bat

# Linux/Mac
./build.sh
```

## Default Password

Default login password: `OpentheBlocker`

You can change this password in the Settings page after logging in.

## How It Works

SM-Blocker modifies the Windows hosts file (`C:\Windows\System32\drivers\etc\hosts`) to redirect blocked domains to `127.0.0.1`, effectively blocking access to those websites. The application:

1. Creates backups of the hosts file before modifications
2. Tracks blocked state in settings
3. Requires administrator privileges for hosts file operations
4. Provides a user-friendly interface for managing blocks

## Project Structure

```
SM_Blocker/
├── src/
│   ├── main.py              # Application entry point
│   ├── config/              # Configuration and constants
│   ├── core/                # Core functionality (blocker, auth, hosts)
│   ├── ui/                  # User interface components
│   └── utils/               # Utilities (language, system integration)
├── assets/                  # Icons and assets
├── pyproject.toml           # Project configuration
└── README.md
```

## Security

- Passwords are hashed using PBKDF2 with SHA-256
- Settings are stored locally in JSON format
- Requires administrator privileges for security

## Troubleshooting

### "Permission denied" error
- Run the application as Administrator
- Right-click the executable and select "Run as administrator"

### Websites not blocking
- Ensure the application is running as Administrator
- Check Windows Firewall settings
- Clear browser DNS cache

### Language not changing
- Restart the application after changing language
- Navigate to a different page and back

## License

This project is created by Sifat.

## Disclaimer

This software is provided as-is. Use at your own risk. Always backup your hosts file before making modifications.
