# 🚀 DASHBOARD-BITAXE-601

A modern, multi-unit dashboard for monitoring **Bitaxe 601 miners** with real-time data, session analytics, temperature monitoring, CKPool support, Telegram alerts and full compatibility with **Tailscale** for secure remote access.

Supports up to **2 Bitaxe units** (Gamma / Ultra / DIY).  
No database required. Fully standalone **Flask** backend.

## ⭐ Features

### 📡 Real-time Bitaxe Telemetry
- Hashrate (GH/s)
- Temperature (°C)
- VR Temperature (°C)
- Voltage & Core Voltage
- Frequency (MHz)
- Fan speed
- Shares accepted / rejected
- Stratum URL
- Per-unit SessionBest + BestDiff

### 📊 Analytics & Charts
- Real-time charts (hashrate + temps)
- Averages calculated over the entire log session
- SessionBest historical line chart
- Combined multi-metric charts for each Bitaxe

### 🧰 Extra Tools
- One-click restart per Bitaxe
- Automatic system restart every X hours
- Automatic log rotation
- CKPool log live parsing (optional)
- Fully Tailscale-ready (0.0.0.0 binding)
- Telegram alerts:
  - High temperature
  - SessionBest improvement

## 📦 Requirements

- Python **3.9+**
- Flask
- requests
- Chart.js (via CDN)
- Bitaxe units
- Optional CKPool
- Optional Tailscale

## 🗂️ Project Structure

```
DASHBOARD-BITAXE-601/
├── dashboard_request.py
├── templates/
│   └── index.html
├── static/
│   └── favicon.ico
```

## ⚙️ Configuration

Edit `dashboard_request.py`:

```python
BITAXE_IPS = [
    "100.100.100.1",
    "100.100.100.2",
    "100.100.100.3",
    "100.100.100.4",
]
```

## 🔔 Telegram Alerts (ENV)

Linux/macOS:
```
export TG_TOKEN="bot_token"
export TG_CHAT_ID="chat_id"
```

Windows:
```
setx TG_TOKEN "bot_token"
setx TG_CHAT_ID "chat_id"
```

## 🌍 Tailscale Access

Open:
```
http://<TAILSCALE-IP>:19150
```

## ⛏️ Mining Modes

### 1 — CKPool Solo Mining  
Reads `ckpool.log` automatically.

### 2 — Pool Mining  
Dashboard works normally without CKPool.

## 🖥️ Start

```
python dashboard_request.py
```

Open:
```
http://localhost:19150
```

## 🤝 Contributing
PRs welcome!

## 📄 License
MIT License.
