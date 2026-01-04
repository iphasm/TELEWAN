#!/usr/bin/env python3
"""
Script simple para probar que Flask funciona correctamente
"""

from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def healthcheck():
    return jsonify({
        "status": "healthy",
        "service": "TELEWAN Bot",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Flask is working"}), 200

if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', '8443'))
    print(f"Testing Flask on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)

