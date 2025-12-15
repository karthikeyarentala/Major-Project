"""import time as t
import requests as req
import re
from datetime import datetime as dt
import os

SNORT_ALERT_FILE = r'C:\Snort\log\alerts.log'
BACKEND_API_URL = "http://127.0.0.1:3001/api/log-alert"

SNORT_PATTERN = re.compile(
    r'^\[\*\*\] \[(\d+):\d+:\d+\] (.*?) \[.*\] \{(\w+)\} (\S+):(\S+) -> (\S+):(\S+)'
)

def parse_snort_alert(line):
    #It parses a single line of snort alert_fast output
    match = SNORT_PATTERN.match(line)

    if match:
        rule_sid = match.group(1)
        description = match.group(2).strip()
        protocol = match.group(3)
        src_ip = match.group(4)

        log_data = f"PROTOCOL: {protocol} | SID: {rule_sid} | DESC: {description} | SRC: {src_ip}"

        return {
            'alertID': f"SNORT-ID-{rule_sid}-{dt.now().strftime('%Y%m%d%H%M%S%f')}",
            'sourceType': 'NIDS_Snort_Alert',
            'logData': log_data
        }
    return None

def monitor_snort_log():
    #It continuously monitors the Snort alert log files
    try:
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
        print(f"An unexpected error occurred in the parser: {e}")

def sendToBackend(payload):
    #It sends the parsed alert payload to the Node.JS API for hashing and blockchain anchoring
    try:
        res = req.post(BACKEND_API_URL, json=payload, timeout=5)
        res.raise_for_status()
        print(f"✅ Alert send to Node.JS. Status: {res.status_code}, Response: {res.text}")
    except req.exceptions.RequestException as e:
        print(f"❌ ERROR communicating with Node.JS backend: {e}")

if __name__ == "__main__":
    monitor_snort_log()

"""

import time
import os
import re
import json

LOG_FILE = r'C:\Snort\log\alerts.log' # Use r-string for Windows path

def parse_alert_line(line):
    line = line.strip()

    if line.startswith("[**]"):
        match = re.search(r'\[\*\*\]\s+\[(\d+:\d+:\d+)\]\s+(.*?)\[\*\*\]\s+\[Classification:\s+(.*?)\]\s+\[Priority:\s+(\d+)\]\s+\{(.*?)\}\s+([\d\.:]+)\s+->\s+([\d\.:]+)', line)
        if match:
            sid, msg, classification, priority, protocol, src, dst = match.groups()
            # creating a JSON object 
            alert_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "sid": sid,
                "message": msg.strip(),
                "classification": classification.strip(),
                "priority": priority.strip(),
                "protocol": protocol.strip(),
                "source_ip": src.strip(),
                "destination_ip": dst.strip()
            }
            print("---THREAT DETECTED---")
            print(json.dumps(alert_data, indent=4))
            return alert_data
        print(f"!!! ALERT DETECTED !!!: {line}")
        return None
    else:
        # Handle other types of alerts if needed
        pass

def tail_file(filepath):
    # Continuously monitor a file for new lines.
    print(f"Waiting for Snort to create the log file at: {filepath}")

    # 1. Wait for the file to be created
    while not os.path.exists(filepath):
        # Print a dot every 2 seconds to show it's active
        print(".", end="", flush=True) 
        time.sleep(2)
    
    print("\nLog file found! Starting monitoring...")

    # 2. Open and monitor the file. 'r' mode is fine for continuous reading
    with open(filepath, 'r', encoding='utf-8') as f:
        # Move cursor to the end of the file so we only read new lines
        f.seek(0, 2)
        
        while True:
            new_line = f.readline()
            if not new_line:
                time.sleep(0.1)
                continue
            
            # Process the new line
            parsed_data = parse_alert_line(new_line)
            # In a real application, you would send parsed_data to your React API here.

if __name__ == "__main__":
    tail_file(LOG_FILE)