import time as t
import requests as req
import re
import os
import uuid
from datetime import datetime as dt
from scapy.all import sniff, IP
import threading as th

SNORT_ALERT_FILE = r"C:\Snort\log\alert.ids"
BACKEND_API = "http://127.0.0.1:3001/api/log-alert"
API_KEY = "snort-secret-key"

SNORT_PATTERN = re.compile(
    r'\[\*\*\]\s+\[1:(\d+):\d+\]\s+(.*?)\s+\[\*\*\].*?\{([A-Z0-9\-]+)\}\s+([\d.:]+)\s+->\s+([\d.:]+)'
)

def classify(alert):
    msg = alert.upper()
    if any(x in msg for x in ["DOS", "DDOS", "ATTACK", "EXPLOIT", "MALWARE"]):
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
        if r.status_code != 200:
            print("❌ Backend error:", r.text)
    except Exception as e:
        print("❌ Backend unreachable:", e)

def monitor_snort():
    print("🟢 Monitoring Snort alerts...")
    while not os.path.exists(SNORT_ALERT_FILE):
        t.sleep(1)
    with open(SNORT_ALERT_FILE, "r", errors='ignore') as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                t.sleep(0.1)
                continue
            match = SNORT_PATTERN.search(line)
            if match:
                rule, msg, proto, src, dst = match.groups()
                severity = classify(msg)

                payload = {
                    "alertId": f"SNORT-{rule}-{uuid.uuid4().hex[:6]}",
                    "sourceType": "Snort IDS",
                    "severity": severity,
                    "logData": f"{msg} | {src} -> {dst}"
                }

                print(f"🔥 {severity}: {msg}")
                send(payload)

def sniff_safe(packet):
    if packet.haslayer(IP):
        payload = {
            "alertId": f"SAFE-{uuid.uuid4().hex[:6]}",
            "sourceType": "Live-Sniffer",
            "severity": "Safe",
            "logData": f"{packet[IP].src} -> {packet[IP].dst}"
        }
        send(payload)


if __name__ == "__main__":
    th.Thread(target=monitor_snort, daemon=True).start()
    sniff(prn=sniff_safe, filter="ip", store=0)