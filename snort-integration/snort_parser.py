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

LOG_FILE = r'C:\Snort\log\alerts.log' # Use r-string for Windows path

def parse_alert_line(line):
    """
    Simple function to parse the alert_fast format.
    [**] [1:1000001:1] TEST: ICMP Ping Detected [**]
    [Classification: Misc activity] [Priority: 3]
    09/25-10:00:00.123456 IP 192.168.1.100 -> 8.8.8.8 ICMP Echo request
    """
    if "TEST: ICMP Ping Detected" in line:
        # You can implement more complex parsing here to extract timestamps, IPs, etc.
        print(f"!!! THREAT DETECTED !!!: {line.strip()}")
    else:
        # Handle other types of alerts if needed
        pass

def tail_file(filepath):
    # Continuously monitor a file for new lines.
    print(f"Waiting for Snort to create the log file at: {filepath}")

    # 1. Wait for the file to exist
    while not os.path.exists(filepath):
        # Print a dot every 2 seconds to show it's active
        print(".", end="", flush=True) 
        time.sleep(2)
    
    print("\nLog file found! Starting monitoring...")

    # 2. Open and monitor the file as before
    with open(filepath, 'r') as f:
        f.seek(0, 2)
        
        while True:
            new_line = f.readline()
            if not new_line:
                time.sleep(0.1)
                continue
            
            # Process the new line
            parse_alert_line(new_line)

if __name__ == "__main__":
    tail_file(LOG_FILE)