# DeepFocus 🎯

**A powerful Windows desktop application to block distracting websites and social media platforms, helping you maintain focus and productivity.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

---

## ✨ Features

- **Social Media Blocking** - Facebook, Instagram, LinkedIn, Twitter/X, YouTube, TikTok, Reddit, Snapchat
- **Custom Domains** - Block any website or domain
- **Content Filtering** - Adult content & gambling site blocking
- **Password Protection** - Secure settings with master password
- **System Tray** - Minimize to tray, right-click menu
- **Auto-Start** - Launch on Windows boot
- **Multilingual** - English & Bengali support

---

## 🚀 Quick Start

### For End Users

1. Download and run `DeepFocus_Setup.exe`
2. Install (will request Administrator privileges)
3. Launch DeepFocus → Login with: `OpentheBlocker`
4. Toggle platforms to block/unblock

### For Developers

```bash
# Clone and setup
git clone https://github.com/Pro-Sifat-Hasan/deepfocus.git
cd deepfocus
pip install uv
uv venv && .venv\Scripts\activate && uv pip install -e .

# Run (as Administrator)
python -m src.main
```

---

## 📦 Building

### Build Executable

```bash
.\build_windows.ps1
```

Output: `build\windows\x64\runner\Release\deepfocus.exe`

### Create Installer

1. Install [Inno Setup](https://jrsoftware.org/isdl.php)
2. Build executable first: `.\build_windows.ps1`
3. Right-click `installer.iss` → Compile

---

## 📖 Usage

**Blocking/Unblocking:**
- Toggle switches on main page → Changes apply immediately
- Settings saved automatically

**System Tray:**
- Close window → Minimizes to tray
- Right-click tray icon:
  - **Show** - Restore window
  - **Quit** - Exit application

**Default Password:** `OpentheBlocker` (change in Settings)

---

## 🔧 How It Works

- Modifies Windows hosts file (`C:\Windows\System32\drivers\etc\hosts`)
- Redirects blocked domains to `127.0.0.1`
- Works across **all browsers and applications**
- Automatic backups before modifications
- Background monitor re-applies blocks if removed

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Permission denied | Run as Administrator |
| Websites not blocking | Clear DNS: `ipconfig /flushdns` |
| UAC prompt not showing | Check executable compatibility settings |
| Multiple tray icons | Close all instances, restart |
| Login not working | Delete `%APPDATA%\DeepFocus\settings.json` |

---

## 📁 Project Structure

```
src/
├── main.py              # Entry point
├── config/              # Settings, constants
├── core/                # Blocking logic, auth
├── ui/                  # Interface components
└── utils/               # Language, system integration
```

---

## ⚙️ Requirements

- **Windows 10/11** (64-bit)
- **Python 3.10+** (for development)
- **Administrator privileges** (required)

---

## 🔐 Security

- ✅ **No Internet** - Works completely offline
- ✅ **Local Storage** - All data stored locally
- ✅ **Password Hashing** - PBKDF2-SHA256 encryption
- ✅ **Auto Backups** - Hosts file backed up automatically

---

## 📄 License

Created by Sifat for NeuroBrain. Proprietary software. All rights reserved.

---

## 📞 Support

- **Repository:** [GitHub](https://github.com/Pro-Sifat-Hasan/deepfocus)
- **Issues:** [Report Issues](https://github.com/Pro-Sifat-Hasan/deepfocus/issues)

---

**Version:** 0.1.0 | **Last Updated:** January 2025
