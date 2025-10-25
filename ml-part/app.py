from flask import Flask, request, jsonify
import joblib as jl
import traceback as tb

#app initialization
app = Flask(__name__)

loadedModel = 'trainedModel.joblib'
pipeLine = None

#loading the trained model
try:
    pipeLine = jl.load(loadedModel)
    print("✅ Model loaded successfully.")
except FileNotFoundError:
    print(f"Error: The model file '{loadedModel}' was not found.")
    exit()
except Exception as e:
    print("Error loading the model:")
    exit()

#Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    if not pipeLine:
        return jsonify({'error': 'Model not loaded'}), 500
    try:
        data = request.json
        log_data = data.get('logData')
        if not log_data:
            return jsonify({'error': 'logData field is missing!'}), 400
        print(f"Received log data for prediction: {log_data}")
        log_data = [log_data]
        pred = pipeLine.predict(log_data)[0]
        confidenceProbs = pipeLine.predict_proba(log_data)[0]
        confidence = confidenceProbs[pred]

        is_suspicious = bool(pred)
        model_version = "v1.0-logistic-regression"

        response = {
            'isSuspicious': is_suspicious,
            'confidence': confidence,
            'modelVersion': model_version
        }
        print(f"Sending result: {response}")
        return jsonify(response)
    except Exception as e:
        print(f"Error while predicting: {e}")
        print(tb.format_exc())
        return jsonify({'error': 'Internal Server error'}), 500
    
if __name__ == '__main__':
    app.run(port=5000, debug=True)