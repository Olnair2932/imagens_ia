import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, db

app = Flask(__name__, template_folder='templates')
CORS(app) # Importante para o Firebase Hosting conseguir falar com o Render

# --- CONFIGURAÇÃO FIREBASE ---
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
        print("✅ Firebase conectado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao iniciar Firebase: {e}")
else:
    print("⚠️ Arquivo /etc/secrets/firebase-key.json não encontrado!")

# Configuração Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index(): return "Servidor IA Ativo", 200

@app.route('/buscar', methods=['POST', 'OPTIONS'])
def buscar():
    if request.method == 'OPTIONS': return '', 204
    
    data = request.json
    tema = data.get('tema')
    uid = data.get('uid')
    
    print(f"🔎 Buscando tema: {tema} para o UID: {uid}")

    try:
        response = model.generate_content(f"Translate '{tema}' to 1 english noun.")
        keyword = response.text.strip().split()[0].replace('.', '').replace('"', '')
    except:
        keyword = "nature"
    
    image_url = f"https://loremflickr.com/1280/720/{keyword}"

    # GRAVAÇÃO NOS BANCOS DE DADOS
    if uid and firebase_admin._apps:
        try:
            # 1. Firestore
            fs.collection('usuarios').document(uid).collection('imagens').add({
                'url': image_url, 'tema': tema, 'timestamp': firestore.SERVER_TIMESTAMP
            })
            # 2. Realtime
            rtdb.child('historico').child(uid).push({
                'pesquisa': tema, 'timestamp': {".sv": "timestamp"}
            })
            print("💾 Dados salvos no Firebase!")
        except Exception as e:
            print(f"❌ Erro ao salvar no Firebase: {e}")

    return jsonify({'image_url': image_url, 'tema': tema})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
