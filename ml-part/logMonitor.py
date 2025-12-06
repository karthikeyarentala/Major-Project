import pandas as pd
import joblib # Changed from jl alias for clarity
import requests
from datetime import datetime
import time
import warnings
import sys
import os
import random
from itertools import cycle

# Suppress warnings
warnings.filterwarnings("ignore")

# --- Configuration ---
BACKEND_API_URL = 'http://127.0.0.1:3001/api/log-alert'
LOG_INTERVAL_SECONDS = 5
LOG_SOURCE_TYPE = "SystemMonitor_v1"

# --- Simulated Logs ---
SAFE_LOGS = [
    "User logon successful at workstation. Authentication type: Kerberos",
    "Application starting up normally: Chrome.exe, Process ID: 1234",
    "System checkpoint created successfully. Disk usage: 45%",
    "DHCP lease renewed successfully for IP: 192.168.1.100",
    "Registry access to HKEY_CURRENT_USER for browser settings."
]
SUSPICIOUS_LOGS = [
    "Failed logon attempt from unknown user. Source IP: 203.0.113.12",
    "New executable created in temp directory. Filename: hidden_tool.exe",
    "Abnormal network connection to port 4444. Destination: 10.0.0.5",
    "System DLL injection detected in critical process. Process: lsass.exe",
    "Massive file deletion initiated by user account."
]

LOG_STREAM_TEMPLATES = cycle(SAFE_LOGS*5 + SUSPICIOUS_LOGS*2) 

# --- Log Generation ---
def generate_simulated_log():
    #Generates a new log entry based on defined templates.
    # Decide if the next log should be suspicious based on the cycle
    is_suspicious_template = next(LOG_STREAM_TEMPLATES)
    
    # Choose a template
    if is_suspicious_template in SUSPICIOUS_LOGS:
        log_text = is_suspicious_template
        source_prefix = "ATTACK_SIM" # Identifier for the suspicious source
    else:
        log_text = is_suspicious_template
        source_prefix = "NORMAL_OP" # Identifier for safe operation

    # Create a unique ID for the alert
    # We use a timestamp-based ID to guarantee uniqueness in a real-time system
    timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
    alert_id = f"{source_prefix}_{timestamp_str}"
    
    return {
        'alertId': alert_id,
        'sourceType': LOG_SOURCE_TYPE,
        'logData': log_text # This raw string goes to the ML model and for hashing
    }

# --- Log Monitoring Loop ---
def start_log_monitoring():
    print(f"🚀 Starting Real-Time Log Monitoring. Interval: {LOG_INTERVAL_SECONDS} seconds.")
    try:
        while True:
            # 1. Generate a new log entry
            log_data_payload = generate_simulated_log()
            
            alert_id = log_data_payload['alertId']
            log_text = log_data_payload['logData']

            print("-" * 50)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating Log: {alert_id}")
            print(f"   Log Text: {log_text}")

            # 2. Send the log to the Node.js backend API
            try:
                response = requests.post(BACKEND_API_URL, json=log_data_payload, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                status = "SUSPICIOUS 🔴" if result.get('isSuspicious') else "Safe 🟢"
                
                print(f"   Response Status: {response.status_code}")
                print(f"   ML Prediction: {status} (Conf: {result.get('confidencePct')}%)")
                print(f"   Blockchain Tx: {result.get('txHash', 'N/A')[:10]}...")
                
            except requests.exceptions.RequestException as req_e:
                print(f"   XXX ERROR sending alert to backend: {req_e}")
            except Exception as e:
                print(f"   XXX UNEXPECTED ERROR during API call: {e}")

            # 3. Wait for the next interval
            time.sleep(LOG_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\n🛑 Log monitoring stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    start_log_monitoring()