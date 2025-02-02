from flask import Flask, request, jsonify
from t import *
import pymongo
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

client = (insert db link here)

db = client['Neuro-Gait']

collection = db['Patients']

@app.route('/get_patient', methods = ['GET'])
def fetchpatient():
    patientName = request.args.get('name');
    patient = get_patient(patientName, collection)
    print(patientName)
    if patient:
        return jsonify(patient)
    else:
        return jsonify({"error": "not found."}),404

if __name__ == '__main__':
    # Run the Flask development server with debug mode enabled
    app.run(debug=True)
