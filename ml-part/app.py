from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib as jl
import traceback as tb

# ------------------------------------------------------------
# Flask App Initialization
# ------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# defining the loaded model
loadedModel = 'finalTrainedModel.joblib'
pipeLine = None

# ------------------------------------------------------------
# Load the Trained Model
# ------------------------------------------------------------
try:
    pipeLine = jl.load(loadedModel)
    print("✅ Model loaded successfully from:", loadedModel)
except FileNotFoundError:
    print(f"❌ Error: The model file '{loadedModel}' was not found.")
    print("Please ensure you've trained and saved the model using model.py first.")
    exit()
except Exception as e:
    print("❌ Unexpected error while loading model:")
    print(tb.format_exc())
    exit()

# ------------------------------------------------------------
# Prediction Route
# ------------------------------------------------------------
@app.route('/predict', methods=['POST'])
def predict():
    """
    POST JSON format:
    {
        "logData": "Credential Manager credentials were read."
    }
    """
    if not pipeLine:
        return jsonify({'error': 'Model not loaded on server!'}), 500

    try:
        data = request.get_json(force=True)
        log_data = data.get('logData')

        if not log_data:
            return jsonify({'error': "Missing 'logData' field in JSON payload."}), 400

        print(f"📝 Received log data for prediction: {log_data}")

        # Predict
        log_data = [log_data]
        prediction = pipeLine.predict(log_data)[0]
        confidence_probs = pipeLine.predict_proba(log_data)[0]
        confidence = round(float(confidence_probs[prediction]), 4)

        # Format response
        response = {
            'isSuspicious': bool(prediction),
            'confidence': confidence,
            'modelVersion': 'v1.1-logistic-regression',
            'predictionLabel': 'Suspicious' if prediction == 1 else 'Safe'
        }

        print(f"✅ Prediction Result: {response}")
        return jsonify(response), 200

    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        print(tb.format_exc())
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500


# ------------------------------------------------------------
# Run Flask App
# ------------------------------------------------------------
if __name__ == '__main__':
    print("🚀 Starting Flask API for PC Log Classification...")
    print(f"Listening on http://127.0.0.1:5000/predict")
    app.run(port=5000, debug=True)
