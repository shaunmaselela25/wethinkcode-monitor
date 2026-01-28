# WeThinkCode Application Monitor

Automated monitoring tool that checks the WeThinkCode application status and sends alerts when applications open or close.

## Features

- 🔍 Monitors WeThinkCode application page using Selenium (JavaScript-rendered content)
- 📧 Email notifications when status changes
- 🖥️ Console alerts
- 📄 File-based alerts (alerts.txt)
- ⏰ Configurable check intervals
- 💾 Persistent state tracking

## Requirements

- Python 3.8+
- Chromium/Chrome browser
- ChromeDriver

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd wethinkcode-monitor
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install ChromeDriver (Ubuntu/Debian):
```bash
sudo apt-get install chromium-chromedriver
```

## Configuration

1. Copy the example config:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your settings:
   - Set email credentials (use App-Specific Password for iCloud)
   - Adjust check interval
   - Enable/disable alert methods

## Usage

**Single check:**
```bash
python wethinkcode_monitor.py --mode once
```

**Continuous monitoring:**
```bash
python wethinkcode_monitor.py --mode continuous
```

This will check every 6 hours (or your configured interval) and alert you when the application status changes.

## Email Setup (iCloud)

1. Go to https://appleid.apple.com
2. Sign in and navigate to Security
3. Generate an App-Specific Password
4. Use this password in `config.json` instead of your regular password

## Files

- `config.json` - Your configuration (not tracked in git)
- `wethinkcode_state.json` - Tracks application status
- `wethinkcode_monitor.log` - Log file
- `alerts.txt` - Alert history

## License

MIT License
