DASHBOARD-BITAXE-601

Multi-unit dashboard for monitoring Bitaxe 601 miners with real-time data, charts, CKPool support, Telegram alerts and Tailscale remote access.

A complete monitoring system for up to 4 Bitaxe miners (601 Gamma / Ultra / DIY).
Supports CKPool solo mining, external pool mining, Tailscale remote access, Telegram alerts, live charts, averages and automatic restarts.

⭐ Features
Real-time Bitaxe telemetry

Hashrate

Temperature / VR Temp

Voltage, core voltage, frequency

Fan speed

Shares accepted / rejected

Stratum URL

Additional features

Averages panel (computed over full log duration)

Combined charts (hashrate + temperature + VRTemp)

SessionBest historical chart

CKPool log live parsing (optional)

One-click Bitaxe restart per unit

Automatic Bitaxe restart every X hours

Automatic log rotation

Telegram alert system

High temperature alert

New SessionBest alert

Tailscale-ready remote dashboard

Fully standalone (no database required)

📦 Requirements

Python 3.9+

pip

Flask

requests

Chart.js (via CDN)

Up to 4 Bitaxe miners

(Optional) CKPool running locally

(Optional) Tailscale for remote access

📁 Project Structure
dashboard_request.py       # Flask backend
templates/index.html       # Main dashboard UI
static/favicon.ico
bitaxe_log.txt             # Auto-generated
ckpool.log                 # Optional, auto-read for CKPool mode

⚙️ Configuration (dashboard_request.py)
BITAXE_IPS = [
    "100.100.100.1",
    "100.100.100.2",
    "100.100.100.3",
    "100.100.100.4"
]

LOGFILE = "bitaxe_log.txt"
CKPOOL_LOG = "ckpool.log"
DASHBOARD_PORT = 19150

COLLECT_INTERVAL = 60
DASHBOARD_REFRESH_REALTIME = 60
DASHBOARD_REFRESH_MEDIUM = 60
DASHBOARD_REFRESH_CHARTS = 60

TEMP_ALERT = 60
BITAXE_RESTART_EVERY_HOURS = 24


You can freely add or remove IP addresses.

🔔 Telegram Alerts

The script uses environment variables.

Linux/macOS:

export TG_TOKEN="your_bot_token_here"
export TG_CHAT_ID="your_chat_id_here"


Windows PowerShell:

setx TG_TOKEN "your_bot_token_here"
setx TG_CHAT_ID "your_chat_id_here"


If variables are missing, Telegram alerts are automatically disabled.

🌍 Tailscale Remote Access

The dashboard listens on:

0.0.0.0:19150


With Tailscale running, access it remotely via:

http://<TAILSCALE-IP>:19150


Bitaxe units must be reachable via LAN or Tailscale.

⛏️ Mining Modes
1. CKPool Solo Mining

If running CKPool locally, place ckpool.log in the same directory.
The dashboard will parse it automatically.

2. Pool Mining (External Pool)

No CKPool log needed.
Dashboard shows:

real-time stats

averages

combined charts

SessionBest history

▶️ Running the Dashboard

Install dependencies:

pip install flask requests


Start:

python dashboard_request.py


Open:

http://localhost:19150


Or via Tailscale:

http://<TAILSCALE-IP>:19150

🔁 (Optional) systemd Service for Linux

Create:

/etc/systemd/system/bitaxe-dashboard.service


Content:

[Unit]
Description=Bitaxe Dashboard
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/bitaxe-dashboard
ExecStart=/usr/bin/python3 dashboard_request.py
Restart=always
Environment=TG_TOKEN=your_token
Environment=TG_CHAT_ID=your_chat_id

[Install]
WantedBy=multi-user.target


Enable:

sudo systemctl daemon-reload
sudo systemctl enable bitaxe-dashboard
sudo systemctl start bitaxe-dashboard

🤝 Contributing

Pull Requests are welcome:

UI improvements

Performance optimizations

Bitaxe Ultra support

Multi-pool integrations

📜 License

MIT License.

👤 Author

Dashboard designed for multi-unit Bitaxe monitoring using:
Flask, Chart.js, Telegram Bot API, Tailscale networking.
