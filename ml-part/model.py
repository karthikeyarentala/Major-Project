import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split as tts
from sklearn.feature_extraction.text import TfidfVectorizer as TFIDF
from sklearn.linear_model import LogisticRegression as LR
from sklearn.pipeline import make_pipeline as mp
import joblib as jl
import warnings as w

w.filterwarnings("ignore")

dataset = 'advanced_cybersecurity_data.csv'

#loading dataset
try:
    data = pd.read_csv(dataset, on_bad_lines='skip')
except FileNotFoundError:
    print(f"Error: The file '{dataset}' was not found.")
    exit()

textCols = ['Request_Type', 'Status_Code', 'User_Agent', 'Location']

data = data.dropna(subset=textCols)

data['Status_Code'] = data['Status_Code'].astype(str)
data['User_Agent'] = data['User_Agent'].astype(str)

suspicious_UA = data['User_Agent'].str.contains('Bot|Scraper|attack|sqlmap|nmap|nikto|acunetix|havij|fimap|dirbuster|burpsuite|nessus', case=False, na=False)
suspicious_STATUS = data['Status_Code'].str.contains('403|404|500', case=False, na=False)
data['OP_Label'] = ((suspicious_UA) | (suspicious_STATUS)).astype(int)

data['Log_Feature'] = data[textCols].agg(' '.join, axis=1)

X = data['Log_Feature']
y = data['OP_Label']

print(y.value_counts(normalize=True))

pipeLine = mp(
    TFIDF(max_features=1000),
    LR(max_iter=1000, class_weight='balanced')
)

X_train, X_test, y_train, y_test = tts(X, y, test_size=0.2, random_state=42)
pipeLine.fit(X_train, y_train)

accuracy = pipeLine.score(X_test, y_test)
print(f"Model's Accuracy: {accuracy*100:.2f}%")

print("-- Classification Report --")
from sklearn.metrics import classification_report
y_pred = pipeLine.predict(X_test)
print(classification_report(y_test, y_pred, target_names=['Normal (0)', 'Anomalous (1)']))

#saving the model
jl.dump(pipeLine, 'trainedModel.joblib')