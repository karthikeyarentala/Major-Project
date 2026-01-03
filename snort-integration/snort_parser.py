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

# defining the severity
def get_severity(rule_id, alert_msg):
    if "Traffic Detected" in alert_msg:
        return "Info"
    
    if any(word in alert_msg.upper() for word in ["DOS", "DDOS", "ATTACK", "EXPLOIT", "MALWARE", "RANSOMWARE"]):
        return "Suspicious"
    return "low"


# Monitor suspicious traffic
def monitor_snort_log():
    print(f"[{datetime.now()}] Monitoring Snort alerts...")

    while not os.path.exists(SNORT_ALERT_FILE):
        t.sleep(1)

    with open(SNORT_ALERT_FILE, "r", encoding="utf-8", errors="ignore") as file:
        file.seek(0, os.SEEK_END)

        while True:
            line = file.readline()
            if not line:
                t.sleep(0.1)
                continue
            match = SNORT_PATTERN.search(line)
            if match:
                rule_id = match.group(1)
                alert_msg = match.group(2)

                currSevirity = get_severity(rule_id, alert_msg)

                payload = {
                    "alertId": f"SNORT-{rule_id}-{int(t.time())}",
                    "sourceType": "Snort-IDS",
                    "severity": currSevirity,
                    "logData": f"ALERT: {alert_msg} | {match.group(4)} -> {match.group(5)}"
                }
                print(f"🔥 SUSPICIOUS: {alert_msg}")
                send_to_backend(payload)
                

# Monitor Safe traffic
last_safe_time = 0
def capture_live_safe_traffic(packet):
    global last_safe_time
    curr_time = t.time()
    if curr_time - last_safe_time < 2:
        return
    
    if packet.haslayer(IP):
        src = packet[IP].src
        dst = packet[IP].dst
        protocol = packet[IP].proto

        payload = {
            "alertId": f"SAFE-{int(t.time()*1000)}",
            "sourceType": "Live-Sniffer",
            "severity": "Safe",
            "logData": f"PASS: {src} -> {dst} | Protocol: {protocol}"
        }
        send_to_backend(payload)
        last_safe_time = curr_time

if __name__ == "__main__":
    thread = th.Thread(target=monitor_snort_log, daemon=True)
    thread.start()
    print("🟢 Sniffing Safe Traffic... (Press Ctrl+C to stop)")
    try:
        sniff(prn=capture_live_safe_traffic, store=0, filter="ip", count=0)
    except KeyboardInterrupt:
        print("\nStopping...")
