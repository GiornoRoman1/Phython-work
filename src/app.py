# src/app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/ready')
def ready_check():
    return jsonify({"status": "ready"})

@app.route('/')
def hello():
    return jsonify({"message": "Hello from GCP Pipeline!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)