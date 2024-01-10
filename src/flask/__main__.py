"""This is the script to run the flask app."""

import os
from flask import Flask, request, jsonify

from .social import BertClassifier

app = Flask(__name__)

# Load model
MODEL = None


@app.route("/predict", methods=["POST"])
def predict():
    text = request.get_json()["text"]
    prediction = MODEL.classify(text)
    return jsonify(prediction)


if __name__ == "__main__":
    # Load model
    MODEL = BertClassifier(f"{os.getcwd()}/models/bert-social.model")
    app.run(host="0.0.0.0", port=8080)
