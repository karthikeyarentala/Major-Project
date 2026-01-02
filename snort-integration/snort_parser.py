import time
import requests
import re
import os
from datetime import datetime

SNORT_ALERT_FILE = r"C:\Snort\log\alert.ids"
BACKEND_API_URL = "http://127.0.0.1:3001/api/log-alert"

SNORT_PATTERN = re.compile(
    r'\[\*\*\]\s+\[1:(\d+):\d+\]\s+(.*?)\s+\[\*\*\].*?\{([A-Z0-9\-]+)\}\s+([0-9a-fA-F:.]+)\s+->\s+([0-9a-fA-F:.]+)'
)


def sendToBackend(payload):
    try:
        res = requests.post(BACKEND_API_URL, json=payload, timeout=2)
        res.raise_for_status()
        print("✅ Sent:", payload['logData'])
    except requests.exceptions.RequestException as e:
        print("❌ Backend error:", e)

def parse_snort_alert(line):
    match = SNORT_PATTERN.search(line)
    if not match:
        return None

    return {
        "alertId": f"SNORT-{match.group(1)}-{int(time.time())}",
        "sourceType": "Snort-IDS",
        "severity": "High",
        "logData": f"{match.group(2)} | {match.group(4)} -> {match.group(5)} | {match.group(3)}"
    }

def monitor_snort_log():
    print(f"[{datetime.now()}] Monitoring Snort alerts...")

    with open(SNORT_ALERT_FILE, "r", encoding="utf-8", errors="ignore") as file:
        file.seek(0, os.SEEK_END)

        while True:
            line = file.readline()
            if not line:
                time.sleep(0.2)
                continue

            print("[RAW]", line.strip())
            print("[MATCH]", bool(SNORT_PATTERN.search(line)))

            alert = parse_snort_alert(line)
            if alert:
                print("🚨 ALERT DETECTED")
                sendToBackend(alert)

if __name__ == "__main__":
    monitor_snort_log()
