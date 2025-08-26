from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import datetime
import requests
import bcrypt
from deep_translator import GoogleTranslator
from openai import OpenAI
from langdetect import detect, DetectorFactory
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB setup - use environment variable
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['kuber']
users_collection = db['users']

# OpenAI setup - use environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
client_ai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Session memory
session_memory = {}
DetectorFactory.seed = 0

# Gold investment facts and keywords
gold_investment_facts = {
    "basic": "✨ Gold has always been a trusted way to secure your wealth. Digital Gold lets you invest easily, without worrying about storage or safety.",
    "purchase_suggestion": "💰 Would you like me to help you purchase some gold right now?"
}
keywords = [
    r"\bgold\b", r"\bdigital gold\b", r"\binvest\b", r"\bpurchase gold\b", r"\bbuy gold\b",
    r"\byellow metal\b", r"\bsona\b", r"\binvestment\b",
    r"\bसोना\b", r"\bडिजिटल गोल्ड\b"
]

# -------------------------
# Utility Functions
# -------------------------
def detect_language(query: str) -> str:
    try:
        return detect(query)
    except:
        return "en"

def is_gold_investment_query(query: str) -> bool:
    try:
        translated_query = GoogleTranslator(source='auto', target='en').translate(query).lower()
    except:
        translated_query = query.lower()
    return any(re.search(pattern, translated_query) for pattern in keywords)

def classify_query(query: str) -> str:
    try:
        if not client_ai:
            return "gold" if is_gold_investment_query(query) else "other"
        completion = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify the user query into one of: 'gold', 'finance_general', 'other'. Reply with one word only."},
                {"role": "user", "content": query}
            ],
            temperature=0
        )
        return completion.choices[0].message.content.strip().lower()
    except:
        return "other"

def ask_gpt(query: str, category: str, history: list) -> str:
    try:
        if not client_ai:
            detected_lang = detect_language(query)
            if category == "gold" or is_gold_investment_query(query):
                return "आप सोने में निवेश पर विचार कर रहे हैं। डिजिटल गोल्ड एक आसान और सुरक्षित विकल्प है।" if detected_lang == "hi" else "You are considering gold investment. Digital gold is an easy and safe option."
            return "मैं आपकी मदद के लिए यहाँ हूँ।" if detected_lang == "hi" else "I am here to help."
        detected_lang = detect_language(query)
        system_prompt = f"""
You are Kuber AI, a friendly financial assistant for digital gold investments.
IMPORTANT: Always respond in {detected_lang.upper()} language only.
- If user asks in English, respond in English
- If user asks in Hindi, respond in Hindi
- Be helpful, friendly, and professional
- Use emojis sparingly when appropriate
- Keep responses concise and clear
"""
        if category == "gold":
            system_prompt += "Focus on gold investments, digital gold benefits, and purchase guidance."
        elif category == "finance_general":
            system_prompt += "Provide helpful personal finance advice, savings tips, or investment guidance."

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-3:])
        messages.append({"role": "user", "content": query})

        completion = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        return completion.choices[0].message.content.strip()
    except:
        return "I'm here to help with your financial questions. Could you please rephrase your question?"

def get_gold_price_per_gram():
    try:
        response = requests.get("https://data-asg.goldprice.org/dbXRates/INR")
        data = response.json()
        price_per_gram = float(data['items'][0]['xauPrice']) / 31.1035
        return round(price_per_gram, 2)
    except:
        return 5000

# -------------------------
# AUTHENTICATION
# -------------------------
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not email or not password or not name:
        return jsonify({"error": "All fields are required"}), 400

    existing = users_collection.find_one({"email": email})
    if existing:
        return jsonify({"error": "Email already exists"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = {"email": email, "password": hashed, "name": name, "goldBalance": 0, "investmentHistory": []}
    users_collection.insert_one(user)
    return jsonify({"message": "Account created successfully"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = users_collection.find_one({"email": email})
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "name": user['name'], "goldBalance": round(user['goldBalance'],5), "email": email})

gold_investment_facts = {
    "basic": "✨ Gold has always been a trusted way to secure your wealth. Digital Gold lets you invest easily, without worrying about storage or safety.",
    "purchase_suggestion": "💰 Would you like me to help you purchase some gold right now?"
}

# -------------------------
# CHATBOT (Updated Messages)
# -------------------------
@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.json
    email = data.get("email")
    user_query = data.get("userQuery", "").strip()
    if not user_query:
        return jsonify({"message": "Please provide a valid query."}), 400

    if email not in session_memory:
        session_memory[email] = {"history": [], "last_intent": None, "last_redirect": False}
    history = session_memory[email]["history"]

    yes_patterns = [r"\byes\b", r"\bहाँ\b", r"\bhaan\b", r"\bहो\b"]
    no_patterns = [r"\bno\b", r"\bनहीं\b", r"\bnahin\b"]

    if session_memory[email]["last_redirect"]:
        if any(re.search(p, user_query, re.IGNORECASE) for p in yes_patterns):
            session_memory[email]["last_redirect"] = False
            history.append({"role": "user", "content": user_query})
            return jsonify({
                "message": "Great choice! 🚀 Let’s get started with your gold purchase. Just enter the amount in ₹ and I’ll calculate the gold grams for you.",
                "redirectToPurchase": True
            })
        elif any(re.search(p, user_query, re.IGNORECASE) for p in no_patterns):
            session_memory[email]["last_redirect"] = False
            history.append({"role": "user", "content": user_query})
            return jsonify({
                "message": "👍 Got it! No pressure. You can explore gold investments anytime you feel ready. Meanwhile, I’m here if you want to know more about savings, SIPs, or insurance. 😊",
                "redirectToPurchase": False
            })

    category = classify_query(user_query)

    if category == "gold" or is_gold_investment_query(user_query):
        session_memory[email]["last_intent"] = "gold_purchase"
        session_memory[email]["last_redirect"] = True
        history.append({"role": "user", "content": user_query})
        combined_message = f"{gold_investment_facts['basic']}\n{gold_investment_facts['purchase_suggestion']}"
        return jsonify({"message": combined_message, "redirectToPurchase": True})
    else:
        session_memory[email]["last_intent"] = category
        session_memory[email]["last_redirect"] = False
        history.append({"role": "user", "content": user_query})
        gpt_answer = ask_gpt(user_query, category, history)
        history.append({"role": "assistant", "content": gpt_answer})
        return jsonify({
            "message": gpt_answer,
            "previousContext": [msg["content"] for msg in history[-3:]],
            "redirectToPurchase": False
        })

# -------------------------
# PURCHASE (Updated Message)
# -------------------------
@app.route('/api/purchase-gold', methods=['POST'])
def purchase_gold():
    data = request.json
    email = data.get("email")
    amount = data.get("amount")
    price_per_gram = get_gold_price_per_gram()

    if not email or not amount or amount <= 0:
        return jsonify({"error": "Invalid input"}), 400

    grams_purchased = round(amount / price_per_gram, 5)
    user = users_collection.find_one({"email": email})

    if not user:
        return jsonify({"error": "User not found"}), 404

    new_balance = user['goldBalance'] + grams_purchased
    users_collection.update_one({"email": email}, {"$set": {"goldBalance": new_balance}})
    users_collection.update_one({"email": email}, {"$push": {"investmentHistory": {
        "amount": amount,
        "pricePerGram": price_per_gram,
        "grams": grams_purchased,
        "date": datetime.datetime.now()
    }}})

    return jsonify({
        "message": f"🎉 Success! You’ve purchased {grams_purchased:.5f} g of gold at ₹{price_per_gram}/g.\n"
                   f"✨ Your updated balance is {round(new_balance, 5)} g. Keep growing your golden savings! 🌟",
        "updatedGoldBalance": round(new_balance, 5)
    })
# -------------------------
# GOLD PRICE
# -------------------------
@app.route('/api/gold-price', methods=['GET'])
def gold_price():
    return jsonify({"pricePerGram": get_gold_price_per_gram()})

@app.route('/api/user', methods=['GET'])
def get_user():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "email required"}), 400
    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "name": user.get('name',''),
        "email": email,
        "goldBalance": round(user.get('goldBalance',0),5)
    })

# -------------------------
# STATIC FILES (Serve UI)
# -------------------------
@app.route('/')
def serve_index():
    # Serve the chat UI with no-cache headers
    response = send_from_directory('.', 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def serve_static(path):
    # Serve static assets like script.js and style.css with cache control
    response = send_from_directory('.', path)
    if path.endswith(('.js', '.css')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
