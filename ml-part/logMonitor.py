import pandas as pd
import joblib # Changed from jl alias for clarity
import requests
from datetime import datetime
import time
import warnings
import sys
import os

# Suppress warnings
warnings.filterwarnings("ignore")

# --- Configuration ---
# INPUT MODEL: Use the model trained on your PC logs
MODEL_PATH = 'finalTrainedModel.joblib' # CORRECTED model name
# INPUT LOGS: Read the ORIGINAL exported CSV (unlabeled)
# *** MAKE SURE THIS FILENAME MATCHES YOUR ORIGINAL EXPORT ***
LOG_CSV_FILE = 'labeledPCLogs.csv' # CORRECTED - Use your original export
# BACKEND: Where to send alerts
BACKEND_API_URL = 'http://127.0.0.1:3001/api/log-alert' # Use the IP address
# FEATURES: Column containing the log message text (MUST MATCH model.py TRAINING)
textCol = 'Task Category' # This MUST match the textCol used in model.py
# Optional: Columns to include in the alert message for context
idCol = 'Event ID' # CHECK YOUR CSV - maybe 'Id' or 'EventID'?
timeCol = 'Date and Time' # CHECK YOUR CSV - maybe 'TimeCreated'?


# --- Load Model ---
pipeline = None
print(f"Loading model: {MODEL_PATH}")
try:
    pipeline = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
except FileNotFoundError:
    print(f"ERROR: Model file not found: '{MODEL_PATH}'.")
    print("Please run the updated model.py script first.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Could not load model: {e}")
    sys.exit(1)

# --- DELETED map_csv_row_to_log_data function ---

# --- Main Processing Function ---
def process_log_file():
    print(f"Attempting to read log file: {LOG_CSV_FILE}")
    try:
        # Try reading with common encodings
        try:
            df = pd.read_csv(LOG_CSV_FILE, encoding='utf-8', on_bad_lines='skip', low_memory=False)
        except UnicodeDecodeError:
            print("UTF-8 failed, trying latin-1...")
            df = pd.read_csv(LOG_CSV_FILE, encoding='latin-1', on_bad_lines='skip', low_memory=False)

        print(f"Successfully read {len(df)} rows from {LOG_CSV_FILE}.")
        # Verify required columns exist
        if textCol not in df.columns:
             print(f"\n*** ERROR: Feature column '{textCol}' not found in '{LOG_CSV_FILE}'! ***")
             print(f"Columns found: {df.columns.tolist()}")
             print(f"Please ensure '{textCol}' is the correct column containing log text and exists in the CSV.")
             exit()
        print(f"Columns available for context: {df.columns.tolist()}") # Show available columns

    except FileNotFoundError:
        print(f"ERROR: Log file not found at '{LOG_CSV_FILE}'. Please export logs again if needed.")
        return
    except Exception as e:
        print(f"ERROR: Could not read CSV file '{LOG_CSV_FILE}': {e}")
        return

    suspicious_count = 0
    # Iterate through each row
    print("\nPredicting log entries...")
    # Ensure text column is string and handle potential NaN values
    df[textCol] = df[textCol].astype(str).fillna('')

    # Predict in batches for potentially better performance (optional)
    batch_size = 500
    total_processed = 0
    for i in range(0, len(df), batch_size):
         batch_df = df.iloc[i:i+batch_size]
         # CORRECTED: Get text directly from the specified textCol
         batch_texts = batch_df[textCol].tolist()

         if not batch_texts: # Skip empty batches
              continue

         # Make predictions for the batch
         try:
              predictions = pipeline.predict(batch_texts)
              probabilities = pipeline.predict_proba(batch_texts)
         except Exception as pred_e:
              print(f"ERROR during batch prediction ({i}-{i+batch_size}): {pred_e}")
              continue # Skip this batch on error


         # Process results for the batch
         for idx, (original_index, row) in enumerate(batch_df.iterrows()):
              prediction = predictions[idx]
              confidence = int(probabilities[idx][prediction] * 100)
              is_suspicious = bool(prediction)

              # Get optional info for alert - Use .get() for safety
              event_id = row.get(idCol, 'N/A')
              timestamp = row.get(timeCol, datetime.now().isoformat())
              message_text = row.get(textCol, '') # Get the actual text used for prediction
              message_snippet = message_text[:250] # Take first 250 chars

              # Print result (optional, uncomment to see all predictions)
              # print(f"  Row {original_index+1}: EventID={event_id}")
              # print(f"  Prediction: {'SUSPICIOUS' if is_suspicious else 'Safe'}, Confidence: {confidence}%")

              # If suspicious, send to backend
              if is_suspicious:
                  suspicious_count += 1
                  # FIX 2: Construct the string more carefully
                  row_num_str = str(original_index + 1) # Convert int to string first
                  timestamp_str = str(timestamp).replace(' ','_').replace(':','').replace('.','')
                  # Now combine the strings
                  full_alert_id = f"CSV_{row_num_str}_{timestamp_str}"
                  alert_id = full_alert_id[:50] # Slice after creation
                  # --- END FIX 2 ---

                  source_type = f"CSVLog_{os.path.basename(LOG_CSV_FILE)}"

                  # CORRECTED: Send the actual text snippet as logData
                  logData_to_send = f"EventID={event_id}: {message_snippet}..."

                  payload = {
                      'alertId': alert_id,
                      'sourceType': source_type,
                      'logData': logData_to_send
                  }
                  try:
                      print(f"\n  Row {original_index+1}: DETECTED SUSPICIOUS (Conf: {confidence}%)")
                      print(f"  EventID={event_id}, Log: {message_snippet}...")
                      print(f"    >>> Sending Alert: {alert_id}")
                      response = requests.post(BACKEND_API_URL, json=payload, timeout=10)
                      response.raise_for_status()
                      print(f"    <<< Alert Sent Successfully.")
                      time.sleep(0.2) # Small delay
                  except requests.exceptions.RequestException as req_e:
                      print(f"    XXX ERROR sending alert: {req_e}")
                  except Exception as send_e:
                      print(f"    XXX UNEXPECTED ERROR sending alert: {send_e}")
              # print("-" * 15) # Optional separator
         total_processed += len(batch_df)
         print(f"...processed {total_processed}/{len(df)} rows.", end='\r') # Progress indicator

    print(f"\n\nPrediction complete. Found {suspicious_count} suspicious entries out of {total_processed}.")

if __name__ == "__main__":
    # No admin check needed for reading files
    process_log_file()
