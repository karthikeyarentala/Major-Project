import pandas as pd
from sklearn.model_selection import train_test_split as tts
from sklearn.feature_extraction.text import TfidfVectorizer as TFIDF
from sklearn.linear_model import LogisticRegression as LR
from sklearn.pipeline import make_pipeline as mp
import joblib as jl
import warnings as w
from sklearn.metrics import classification_report, accuracy_score

# --- Configuration ---
w.filterwarnings("ignore")

# INPUT: Use the MODIFIED CSV you generated
dataset = 'labeledPCLogs.csv'

# FEATURES: Use the 'Task Category' column which contains the log text
textCol = 'Task Category'

# LABEL: Use the 'Output' column (0 = safe, 1 = suspicious)
labelCol = 'Output'

# OUTPUT: Save the trained model
output_model_file = 'finalTrainedModel.joblib'

# --- Load Dataset ---
print(f"Loading labeled dataset: {dataset}")
try:
    df = pd.read_csv(dataset, on_bad_lines='skip', low_memory=False, encoding='utf-8')
except UnicodeDecodeError:
    print("UTF-8 failed, trying latin-1...")
    df = pd.read_csv(dataset, on_bad_lines='skip', low_memory=False, encoding='latin-1')
except FileNotFoundError:
    print(f"Error: The file '{dataset}' was not found. Please check its path.")
    exit()

# --- Validate Columns ---
if textCol not in df.columns:
    print(f"\n*** ERROR: Feature column '{textCol}' not found in '{dataset}'! ***")
    print(f"Columns found: {df.columns.tolist()}")
    exit()

if labelCol not in df.columns:
    print(f"\n*** ERROR: Label column '{labelCol}' not found in '{dataset}'! ***")
    print(f"Columns found: {df.columns.tolist()}")
    exit()

# --- Data Cleaning ---
df = df.dropna(subset=[textCol, labelCol])
df[textCol] = df[textCol].astype(str)
df[labelCol] = df[labelCol].astype(int)

X = df[textCol]
y = df[labelCol]

if X.empty or y.empty or len(y.unique()) < 2:
    print("\nError: Dataset empty or only one class present after cleaning.")
    exit()

print(f"Dataset loaded with {len(X)} samples.")
print("Label distribution:")
print(y.value_counts(normalize=True))

is_imbalanced = y.mean() < 0.05 or y.mean() > 0.95
print(f"Dataset appears {'imbalanced' if is_imbalanced else 'reasonably balanced'}.")

# --- Create Model Pipeline ---
print("\nCreating Logistic Regression training pipeline...")
pipeline = mp(
    TFIDF(
        max_features=3000,  # slightly increased for variety
        stop_words='english',
        max_df=0.8,
        min_df=3
    ),
    LR(
        max_iter=1000,
        class_weight='balanced',
        solver='liblinear',
        random_state=42
    )
)

# --- Train/Test Split ---
print("Splitting data and training model...")
try:
    X_train, X_test, y_train, y_test = tts(X, y, test_size=0.25, random_state=42, stratify=y)
except ValueError:
    print("Warning: Stratified split failed, falling back to regular split.")
    X_train, X_test, y_train, y_test = tts(X, y, test_size=0.25, random_state=42)

# --- Model Training ---
pipeline.fit(X_train, y_train)

# --- Evaluation ---
y_pred = pipeline.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ Model Accuracy on Your PC Logs: {accuracy * 100:.2f}%")

print("\n-- Classification Report --")
try:
    if len(set(y_test)) > 1 and len(set(y_pred)) > 1:
        print(classification_report(y_test, y_pred, target_names=['Safe (0)', 'Suspicious (1)'], zero_division=0))
    else:
        print("⚠️ Only one class present in test or predicted data.")
        print(f"Accuracy score: {accuracy}")
        print(f"Unique predictions: {set(y_pred)}")
except Exception as e:
    print(f"Could not generate classification report: {e}")

# --- Save Model ---
print(f"\nSaving trained model to '{output_model_file}'...")
jl.dump(pipeline, output_model_file)

print("\n--- Training Complete! ---")
print(f"✅ Model '{output_model_file}' is ready to classify new PC logs.")
print("You can now use this model with your 'predict_pc_logs.py' script to test unseen logs.")