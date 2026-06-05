import os
import json
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, db

app = Flask(__name__, template_folder='templates')
CORS(app)

# --- CONFIGURAÇÃO FIREBASE ---
service_account_path = '/etc/secrets/firebase-key.json'

if os.path.exists(service_account_path):
    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://cerebro-fba58-default-rtdb.firebaseio.com'
        })
        fs = firestore.client()
        rtdb = db.reference()
        print("✅ Firebase Conectado!")
    except Exception as e:
        print(f"❌ Erro Firebase: {e}")

# Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index(): return "IA Motor Ativo", 200

@app.route('/ping')
def ping(): return "PONG", 200

@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.json
    tema = data.get('tema', 'nature')
    uid = data.get('uid')
    
    # Tradução com Gemini
    try:
        response = model.generate_content(f"Translate '{tema}' to 1 english noun. Only the word.")
        keyword = response.text.strip().split()[0].replace('.', '').replace('"', '')
    except:
        keyword = "nature"
    
    # Busca Pexels
    headers = {"Authorization": os.environ.get("PEXELS_API_KEY")}
    try:
        pex_r = requests.get(f"https://api.pexels.com/v1/search?query={keyword}&per_page=1", headers=headers)
        image_url = pex_r.json()['photos'][0]['src']['large']
    except:
        image_url = f"https://loremflickr.com/1280/720/{keyword}"

    # Salvar Firebase
    if uid and firebase_admin._apps:
        try:
            fs.collection('usuarios').document(uid).collection('imagens').add({
                'url': image_url, 'tema': tema, 'timestamp': firestore.SERVER_TIMESTAMP
            })
            rtdb.child('historico').child(uid).push({
                'pesquisa': tema, 'timestamp': {".sv": "timestamp"}
            })
        except: pass

    return jsonify({'image_url': image_url, 'tema': tema})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
