import time as t
import requests as req
import re
import os
import threading as th
from scapy.all import sniff, IP, TCP, UDP, ICMP
from datetime import datetime

SNORT_ALERT_FILE = r"C:\Snort\log\alert.ids"
BACKEND_API_URL = "http://127.0.0.1:3001/api/log-alert"

SNORT_PATTERN = re.compile(
    r'\[\*\*\]\s+\[1:(\d+):\d+\]\s+(.*?)\s+\[\*\*\].*?\{([A-Z0-9\-]+)\}\s+([0-9a-fA-F:.]+)\s+->\s+([0-9a-fA-F:.]+)'
)


def send_to_backend(payload):
    try:
       req.post(BACKEND_API_URL, json=payload, timeout=1)
    except:
        pass

def parse_snort_alert(line):
    match = SNORT_PATTERN.search(line)
    if not match:
        return None

    return {
        "alertId": f"SNORT-{match.group(1)}-{int(t.time())}",
        "sourceType": "Snort-IDS",
        "severity": "High",
        "logData": f"{match.group(2)} | {match.group(4)} -> {match.group(5)} | {match.group(3)}"
    }

# Monitor suspicious traffic
def monitor_snort_log():
    print(f"[{datetime.now()}] Monitoring Snort alerts...")

    with open(SNORT_ALERT_FILE, "r", encoding="utf-8", errors="ignore") as file:
        file.seek(0, os.SEEK_END)

        while True:
            line = file.readline()
            if not line:
                t.sleep(0.1)
                continue
            match = SNORT_PATTERN.search(line)
            if match:
                payload = {
                    "alertId": f"SNORT-{match.group(1)}-{int(t.time())}",
                    "sourceType": "Snort-IDS",
                    "severity": "Suspicious",  # Hardcoded label
                    "logData": f"ALERT: {match.group(2)} | {match.group(4)} -> {match.group(5)}"
                }
                print(f"🔥 SUSPICIOUS: {match.group(2)}")
                send_to_backend(payload)
                

# Monitor Safe traffic
def capture_live_safe_traffic(packet):
    if packet.haslayer(IP):
        src = packet[IP].src
        dst = packet[IP].dst
        protocol = packet[IP].proto

        payload = {
            "alertId": f"SAFE-{int(t.time()*1000)}",
            "sourceType": "Live-Sniffer",
            "severity": "Safe", # Hardcoded label
            "logData": f"PASS: {src} -> {dst} | Protocol: {protocol}"
        }
        send_to_backend(payload)

if __name__ == "__main__":
    thread = th.Thread(target=monitor_snort_log, daemon=True)
    thread.start()
    print("🟢 Sniffing Safe Traffic... (Press Ctrl+C to stop)")
    sniff(prn=capture_live_safe_traffic, store=0, filter="ip", count=0)
