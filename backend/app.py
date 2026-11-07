"""
LEGACY FILE — NOT USED IN PRODUCTION

This was the initial Phase 0/1 Flask prototype.
All production traffic and API endpoints are routed through:
    backend/app_fastapi.py

Preserved for reference only.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "AI Interview Assistant (Legacy Flask Prototype - Use FastAPI on Port 8001)"

if __name__ == "__main__":
    app.run(debug=False, port=5000)
