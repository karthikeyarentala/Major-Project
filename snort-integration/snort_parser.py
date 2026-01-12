import time as t
import requests as req
import re
import os
import uuid

SNORT_ALERT_FILE = r"C:\Snort\log\alert.fast"
BACKEND_API = "http://127.0.0.1:3001/api/log-alert"
API_KEY = "snort-secret-key"

SNORT_PATTERN = re.compile(
    r'\[\*\*\]\s+\[\d+:\d+:\d+\]\s+(.*?)\s+\[\*\*\].*\{(\w+)\}\s+([\d\.]+:\d+)\s+->\s+([\d\.]+:\d+)'
)

def classify(msg):
    msg = msg.upper()
    for k in ["SCAN", "PORTSCAN", "NMAP", "PROBE", "RECON"]:
        if k in msg:
            return "High"
    return "Safe"

def send(payload):
    try:
        r = req.post(
            BACKEND_API,
            json=payload,
            headers={"x-api-key": API_KEY},
            timeout=3
        )
        print("➡ Sent to backend:", r.status_code)
    except Exception as e:
        print("❌ Backend error:", e)

def monitor_snort():
    print("🟢 Monitoring Snort alerts...")

    while not os.path.exists(SNORT_ALERT_FILE):
        t.sleep(1)

    with open(SNORT_ALERT_FILE, "r", errors="ignore") as f:
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if not line:
                t.sleep(0.1)
                continue

            print("RAW:", line.strip())

            m = SNORT_PATTERN.search(line)
            if not m:
                print("❌ NO MATCH")
                continue

            msg, proto, src, dst = m.groups()
            sev = classify(msg)

            payload = {
                "alertId": "SNORT-" + uuid.uuid4().hex[:6],
                "sourceType": "Snort IDS",
                "severity": sev,
                "logData": f"{msg} | {src} -> {dst}"
            }

            print(f"🔥 DETECTED [{sev}] {msg}")
            send(payload)

monitor_snort()
