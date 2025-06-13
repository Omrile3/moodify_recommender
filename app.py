
# File: app.py

from flask import Flask, request, jsonify, render_template
import json
import random
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
import pickle
import os

nltk.download('punkt')
nltk.download('wordnet')

# Init app
app = Flask(__name__)

# Load assets
base_path = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_path, "files required", "intents.json")) as f:
    intents = json.load(f)

words = pickle.load(open(os.path.join(base_path, "files required", "words.pkl"), 'rb'))
classes = pickle.load(open(os.path.join(base_path, "files required", "classes.pkl"), 'rb'))
model = load_model(os.path.join(base_path, "files required", "chatbot_model.h5"))

lemmatizer = WordNetLemmatizer()

# Utilities
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    return [lemmatizer.lemmatize(word.lower()) for word in sentence_words]

def bow(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    p = bow(sentence, words)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return [{'intent': classes[r[0]], 'probability': str(r[1])} for r in results]

def get_response(intents_list, intents_json):
    if intents_list:
        tag = intents_list[0]['intent']
        for i in intents_json['intents']:
            if i['tag'] == tag:
                return random.choice(i['responses'])
    return "Sorry, I didn't understand that."

# Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat")
def chat():
    msg = request.args.get("msg")
    if not msg:
        return jsonify({"error": "Missing 'msg' parameter"})
    intents_list = predict_class(msg)
    response = get_response(intents_list, intents)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
