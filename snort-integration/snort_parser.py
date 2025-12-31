import time as t
import requests as req
import re
from datetime import datetime as dt
import os
import threading as th
import json
from scapy.all import sniff, IP, TCP, UDP, ICMP

SNORT_ALERT_FILE = r'C:\Snort\log\alert.ids'
BACKEND_API_URL = "http://127.0.0.1:3001/api/log-alert"
SNORT_PATTERN = re.compile(r'^\[\*\*\] \[(\d+):\d+:\d+\] (.*?) \[.*\] \{(\w+)\} (\S+):(\S+) -> (\S+):(\S+)')

def sendToBackend(payload):
    #It sends the parsed alert payload to the Node.JS API for hashing and blockchain anchoring
    try:
        res = req.post(BACKEND_API_URL, json=payload, timeout=2)
        res.raise_for_status()
        print(f"✅ Alert send to Node.JS. Status: {res.status_code}, Response: {res.text}")
    except req.exceptions.RequestException as e:
        print(f"❌ ERROR communicating with Node.JS backend: {e}")

def parse_snort_alert(line):
    #It parses a single line of snort alert_fast output
    match = SNORT_PATTERN.match(line)

    if match:
        rule_sid = match.group(1)
        description = match.group(2).strip()
        protocol = match.group(3)
        src_ip = match.group(4)

        #log_data = f"PROTOCOL: {protocol} | SID: {rule_sid} | DESC: {description} | SRC: {src_ip}"

        return {
            'alertID': f"SNORT-ID-{rule_sid}-{t.time()}",
            'sourceType': 'NIDS_Snort_Alert',
            'severity': 'Suspicious',
            'logData': f"ALERT: {description} | SRC: {src_ip} | PROT: {protocol}"
        }
    return None

def capture_live_traffic(packet):
    if packet.haslayer(IP):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        protocol = "TCP" if packet.haslayer(TCP) else "UDP" if packet.haslayer(UDP) else "ICMP" if packet.haslayer(ICMP) else "OTHER"

        safeData = {
            'alertID': f"SAFE-{t.time()}",
            'sourceType': "Live_Traffic",
            'severity': 'Safe',
            'logData': f"PASS {src_ip} -> {dst_ip} | PROT: {protocol}"
        }
        
        sendToBackend(safeData)

def monitor_snort_log():
    #It continuously monitors the Snort alert log files
    """ try:
        file = open(SNORT_ALERT_FILE, 'r')
        file.seek(0, os.SEEK_END)  # Move to the end of the file
        print(f"[{dt.now().strftime('%H:%M:%S')}] Monitoring Snort alerts at {SNORT_ALERT_FILE}...")

        while True:
            line = file.readline()
            if not line:
                t.sleep(0.1)
                continue
            alert_data = parse_snort_alert(line)

            if alert_data:
                print(f"\n 🚨 [{dt.now().strftime('%H:%M:%S')}] ALERT DETECTED:")
                sendToBackend(alert_data)

    except FileNotFoundError:
        print(f"FATAL ERROR: Snort log file not found at {SNORT_ALERT_FILE}.")
        print("Please ensure Snort is running and logging to its path.")
    except Exception as e:
        print(f"An unexpected error occurred in the parser: {e}") """
    
    file = open(SNORT_ALERT_FILE, 'r')
    file.seek(0, os.SEEK_END)  # Move to the end of the file
    print(f"[{dt.now().strftime('%H:%M:%S')}] Monitoring Snort alerts at {SNORT_ALERT_FILE}...")

    while True:
        line = file.readline()
        if not line:
            t.sleep(0.1)
            continue
        alert_data = parse_snort_alert(line)

        if alert_data:
            print(f"\n 🚨 [{dt.now().strftime('%H:%M:%S')}] ALERT DETECTED:")
            sendToBackend(alert_data)


if __name__ == "__main__":
    monitor_snort_log()
