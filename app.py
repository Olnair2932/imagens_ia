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

# CONFIGURAÇÃO FIREBASE
service_account_path = '/etc/secrets/firebase-key.json'
MAX_REGISTROS = 20

if os.path.exists(service_account_path):
    try:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://cerebro-fba58-default-rtdb.firebaseio.com'
        })
        fs = firestore.client()
        rtdb = db.reference()
        print("✅ Firebase conectado!")
    except Exception as e:
        print(f"❌ Erro Firebase: {e}")

# Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index(): 
    return "Motor de Busca IA Ativo", 200

@app.route('/ping')
def ping(): 
    return "PONG", 200

@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.json
    tema = data.get('tema', 'nature')
    uid = data.get('uid')
    
    try:
        prompt = f"Translate '{tema}' to 1 simple english noun. Only the word."
        response = model.generate_content(prompt)
        keyword = response.text.strip().split()[0].replace('.', '').replace('"', '')
    except:
        keyword = "nature"
    
    headers = {"Authorization": os.environ.get("PEXELS_API_KEY")}
    try:
        pex_url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1"
        pex_r = requests.get(pex_url, headers=headers)
        image_url = pex_r.json()['photos'][0]['src']['large']
    except:
        image_url = f"https://loremflickr.com/1280/720/{keyword}"

    if uid and firebase_admin._apps:
        try:
            # Firestore
            img_ref = fs.collection('usuarios').document(uid).collection('imagens')
            img_ref.add({
                'url': image_url, 
                'tema': tema, 
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            # Realtime
            rtdb.child('historico').child(uid).push({
                'pesquisa': tema, 
                'timestamp': {".sv": "timestamp"}
            })
            print(f"💾 Dados salvos para {uid}")
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")

    return jsonify({'image_url': image_url, 'tema': tema})

@app.route('/excluir_historico', methods=['POST'])
def excluir_historico():
    data = request.json
    rtdb.child('historico').child(data['uid']).child(data['id']).delete()
    return jsonify({'status': 'ok'})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
