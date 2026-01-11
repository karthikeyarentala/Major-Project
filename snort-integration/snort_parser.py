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
    r'\[\*\*\].*?\]\s+(.*?)\s+\[\*\*\][\s\S]*?\{(\w+)\}\s+([\d.:]+)\s+->\s+([\d.:]+)',
    re.MULTILINE
)

""" def classify(alert):
    msg = alert.upper()

    SUSPICIOUS_KEYWORDS = [
        "SCAN",
        "PORTSCAN",
        "NMAP",
        "INDICATOR",
        "PROBE",
        "UPNP",
        "DISCOVER",
        "RECON",
        "ENUMERATION"
    ]

    for word in SUSPICIOUS_KEYWORDS:
        if word in msg:
            return "High"

    return "Safe" """

def classify(alert):
    msg = alert.upper()
    if any(x in msg for x in ["SCAN", "PROBE", "DISCOVER", "UPNP", "NMAP"]):
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
                severity, score = classify(msg, rule)

                payload = {
                    "alertId": f"SNORT-{rule}-{uuid.uuid4().hex[:6]}",
                    "sourceType": "Snort IDS",
                    "severity": severity,
                    "confidence": score,
                    "logData": f"{msg} | {src} -> {dst}"
                }

                print(f"🔥 {severity}: {msg}")
                send(payload)

def sniff_safe(packet):
    if packet.haslayer(IP):
        return


if __name__ == "__main__":
    th.Thread(target=monitor_snort, daemon=True).start()
    sniff(prn=sniff_safe, filter="ip", store=0)