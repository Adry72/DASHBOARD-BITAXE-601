import threading
import time
import requests
import os
import re
from datetime import datetime
from flask import Flask, jsonify, render_template, make_response
from collections import defaultdict


# ====================== USER CONFIGURATION ======================

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

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

TEMP_ALERT = 60
HASHRATE_ALERT = 500
CHECK_ALERT_INTERVAL = 10

BITAXE_RESTART_EVERY_HOURS = 24

# ================================================================


def parse_value(val):
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(',', '.').replace(' ', '')
    if s.endswith('k'):
        return float(s[:-1]) * 1e3
    elif s.endswith('M'):
        return float(s[:-1]) * 1e6
    elif s.endswith('G'):
        return float(s[:-1]) * 1e9
    try:
        return float(s)
    except:
        return 0


def format_value(val):
    if val >= 1e9:
        return f"{val/1e9:.2f}G"
    elif val >= 1e6:
        return f"{val/1e6:.2f}M"
    elif val >= 1e3:
        return f"{val/1e3:.2f}k"
    return f"{val:.2f}"


def convert_str_to_number(val):
    if isinstance(val, (int, float)):
        return val
    val = str(val).replace(",", "").replace(" ", "")
    m = re.match(r'^([\d.]+)([kMG]?)$', val)
    if not m:
        try:
            return float(val)
        except:
            return 0
    num, suffix = m.groups()
    num = float(num)
    if suffix == "k": num *= 1e3
    elif suffix == "M": num *= 1e6
    elif suffix == "G": num *= 1e9
    return num


def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg}, timeout=10)
    except:
        pass


# ===================== ALERT MONITOR =========================

def bitaxe_alert_monitor():
    print("Bitaxe Alert Monitor Started")
    last_temp = {}
    last_sessionbest = {}

    # Initial load
    for ip in BITAXE_IPS:
        try:
            r = requests.get(f"http://{ip}/api/system/info", timeout=3)
            if r.status_code == 200:
                info = r.json()
                sb_raw = info.get("bestSessionDiff", 0)
                last_sessionbest[ip] = parse_value(sb_raw)
        except:
            continue

    while True:
        for ip in BITAXE_IPS:
            try:
                r = requests.get(f"http://{ip}/api/system/info", timeout=3)
                if r.status_code != 200:
                    print(f"[{ip}] HTTP error {r.status_code}")
                    continue
                info = r.json()
            except:
                print(f"[{ip}] Unreachable")
                continue

            temp = float(info.get("temp", 0))
            vrtemp = float(info.get("vrTemp", 0))
            sb_raw = info.get("bestSessionDiff", 0)
            sb_val = parse_value(sb_raw)

            # Temperature alerts
            for sensor, val in (("ASIC", temp), ("VR", vrtemp)):
                key = (ip, sensor)
                if val > TEMP_ALERT:
                    if last_temp.get(key, 0) < TEMP_ALERT:
                        send_telegram(f"🔥 ALERT: {sensor} temperature on {ip} = {val}°C")
                    last_temp[key] = val
                else:
                    last_temp[key] = val

            # SessionBest improvement
            if sb_val > last_sessionbest.get(ip, 0):
                send_telegram(f"🏆 New SessionBest on {ip}: {sb_raw}")
                last_sessionbest[ip] = sb_val

        time.sleep(CHECK_ALERT_INTERVAL)


# ===================== LOG COLLECTOR ==========================

def collector_loop():
    while True:
        for ip in BITAXE_IPS:
            try:
                r = requests.get(f"http://{ip}/api/system/info", timeout=5)
                if r.status_code == 200:
                    info = r.json()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    log = (
                        f"[{now}] {ip} -> Temp: {info.get('temp', 0)}°C | "
                        f"VRTemp: {info.get('vrTemp', 0)}°C | "
                        f"Hashrate: {info.get('hashRate', 0)}/{info.get('expectedHashrate', 0)} GH/s | "
                        f"Power: {info.get('power', 0)}W | Voltage: {info.get('voltage', 0)}V | "
                        f"Frequency: {info.get('frequency', 0)} MHz | "
                        f"Accepted: {info.get('sharesAccepted', 0)} | "
                        f"Rejected: {info.get('sharesRejected', 0)} | "
                        f"BestDiff: {info.get('bestDiff', 0)} | "
                        f"SessionBest: {info.get('bestSessionDiff', 0)}\n"
                    )

                    with open(LOGFILE, "a", encoding="utf-8") as f:
                        f.write(log)
            except:
                pass

        time.sleep(COLLECT_INTERVAL)


# ===================== LOG CLEANER ============================

def reset_logs_daemon(interval=BITAXE_RESTART_EVERY_HOURS):
    while True:
        try:
            open(LOGFILE, "w").close()
            open(CKPOOL_LOG, "w").close()
        except:
            pass
        time.sleep(interval * 3600)


# ===================== AUTO RESTART ===========================

def bitaxe_restart_daemon(interval=BITAXE_RESTART_EVERY_HOURS):
    time.sleep(interval * 3600)
    while True:
        for ip in BITAXE_IPS:
            try:
                r = requests.post(f"http://{ip}/api/system/restart", timeout=5)
                if r.status_code == 200:
                    send_telegram(f"♻️ Bitaxe restarted: {ip}")
                else:
                    send_telegram(f"⚠️ Restart error on {ip}")
            except:
                send_telegram(f"⚠️ Restart error on {ip}")
        time.sleep(interval * 3600)


# ===================== FLASK APP ==============================

app = Flask(__name__)


# ===================== PARSE LOG ==============================

def parse_log():
    data = defaultdict(lambda: defaultdict(list))
    latest = {}
    averages = {}
    session_hist = defaultdict(list)
    max_hashrate = {}
    min_time = None
    max_time = None

    if not os.path.exists(LOGFILE):
        return data, latest, averages, "N/A", max_hashrate, [], session_hist

    pattern = re.compile(
        r'^\[(.*?)\] ([\d.]+(?:\.\d+){2}) -> Temp: ([\d.eE+-]+)°C \| VRTemp: ([\d.eE+-]+)°C \| '
        r'Hashrate: ([\d.eE+-]+)/([\d.eE+-]+) GH/s \| Power: ([\d.eE+-]+)W \| Voltage: ([\d.eE+-]+)V \| '
        r'Frequency: ([\d.eE+-]+) MHz \| Accepted: (\d+) \| Rejected: (\d+) \| BestDiff: ([\d.]+ ?[kMG]?) \| '
        r'SessionBest: ([\d.]+ ?[kMG]?)'
    )

    with open(LOGFILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        m = pattern.match(line.strip())
        if not m:
            continue

        (ts, ip, temp, vtemp, hashrate, maxh, power, volt, freq,
         accepted, rejected, bestdiff, sessionbest) = m.groups()

        ts_obj = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        real_hash = float(hashrate)

        data[ip]["time"].append(ts)
        data[ip]["hashrate"].append(real_hash)
        data[ip]["temp"].append(float(temp))
        data[ip]["vrtemp"].append(float(vtemp))

        if ip not in max_hashrate or real_hash > max_hashrate[ip]:
            max_hashrate[ip] = real_hash

        latest[ip] = {
            "hashrate": int(real_hash),
            "temp": int(float(temp)),
            "vrtemp": int(float(vtemp)),
            "accepted": int(accepted),
            "rejected": int(rejected),
            "sessionbest": sessionbest,
            "bestdiff": bestdiff
        }

        if ip not in averages:
            averages[ip] = {"hashrate_sum": 0, "temp_sum": 0, "vrtemp_sum": 0,
                            "maxhashrate": real_hash, "count": 0}

        averages[ip]["hashrate_sum"] += real_hash
        averages[ip]["temp_sum"] += float(temp)
        averages[ip]["vrtemp_sum"] += float(vtemp)
        averages[ip]["count"] += 1
        if real_hash > averages[ip]["maxhashrate"]:
            averages[ip]["maxhashrate"] = real_hash

        session_hist[ip].append({
            "timestamp": ts,
            "value": convert_str_to_number(sessionbest)
        })

        if not min_time or ts_obj < min_time:
            min_time = ts_obj
        if not max_time or ts_obj > max_time:
            max_time = ts_obj

    # Compute averages
    for ip in averages:
        c = averages[ip]["count"]
        averages[ip] = {
            "hashrate": int(averages[ip]["hashrate_sum"] / c),
            "temp": int(averages[ip]["temp_sum"] / c),
            "vrtemp": int(averages[ip]["vrtemp_sum"] / c),
            "maxhashrate": int(averages[ip]["maxhashrate"])
        }

    duration = "N/A"
    if min_time and max_time:
        delta = max_time - min_time
        duration = f"{delta.seconds//3600}h {(delta.seconds//60)%60}m"

    ips = sorted(list(data.keys()))
    return data, latest, averages, duration, max_hashrate, ips, session_hist


# ===================== ROUTES ===============================

@app.route("/")
def index():
    data, latest, averages, duration, maxh, ips, sessionhist = parse_log()
    return render_template(
        "index.html",
        data=data,
        latest_data=latest,
        averages=averages,
        duration=duration,
        max_hashrate=maxh,
        ips=ips,
        sessionbest_history=sessionhist,
        DASHBOARD_REFRESH_REALTIME=DASHBOARD_REFRESH_REALTIME,
        DASHBOARD_REFRESH_MEDIE=DASHBOARD_REFRESH_MEDIUM,
        DASHBOARD_REFRESH_GRAFICI=DASHBOARD_REFRESH_CHARTS
    )


@app.route("/latest-data")
def api_latest_data():
    _, latest, _, _, _, ips, _ = parse_log()
    extra = {}
    for ip in ips:
        try:
            r = requests.get(f"http://{ip}/api/system/info", timeout=5)
            if r.status_code == 200:
                info = r.json()
                extra[ip] = {
                    "frequency": info.get("frequency", ""),
                    "coreVoltageActual": info.get("coreVoltageActual", ""),
                    "voltage": info.get("voltage", ""),
                    "stratumURL": info.get("stratumURL", ""),
                    "fanspeed": info.get("fanspeed", "")
                }
        except:
            extra[ip] = {}
    return jsonify({"latest": latest, "extra": extra})


@app.route("/reset-bitaxe/<ip>", methods=["POST"])
def reset_bitaxe(ip):
    try:
        r = requests.post(f"http://{ip}/api/system/restart", timeout=5)
        if r.status_code == 200:
            return jsonify({"ok": True, "msg": f"Bitaxe {ip} reset OK"})
        return make_response(jsonify({"ok": False, "msg": f"HTTP {r.status_code}"}), 500)
    except Exception as e:
        return make_response(jsonify({"ok": False, "msg": str(e)}), 500)


@app.route("/sessionbest")
def api_sessionbest():
    *_, hist = parse_log()
    return jsonify(hist)


@app.route("/medie-data")
def api_medie():
    _, _, averages, duration, _, ips, _ = parse_log()
    return jsonify({"averages": averages, "duration": duration, "ips": ips})


@app.route("/combined-data")
def api_combined():
    data, _, _, _, _, ips, _ = parse_log()
    return jsonify({"data": data, "ips": ips})


def get_ckpool_status(logfile=CKPOOL_LOG):
    if not os.path.exists(logfile):
        return "CKPool log not found"
    try:
        with open(logfile, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "TH/s" in line or "GH/s" in line:
                return line.strip()
        return "No mining status found"
    except Exception as e:
        return f"Log read error: {e}"


@app.route("/ckpool-status")
def ckpool_status():
    return jsonify({"status": get_ckpool_status()})


# ===================== START THREADS & RUN ===============================

if __name__ == "__main__":
    threading.Thread(target=collector_loop, daemon=True).start()
    threading.Thread(target=lambda: reset_logs_daemon(BITAXE_RESTART_EVERY_HOURS), daemon=True).start()
    threading.Thread(target=lambda: bitaxe_restart_daemon(BITAXE_RESTART_EVERY_HOURS), daemon=True).start()
    threading.Thread(target=bitaxe_alert_monitor, daemon=True).start()

    print("=== FLASK ROUTES ===")
    for r in app.url_map.iter_rules():
        print(r)

    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False)
