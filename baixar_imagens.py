import requests
import os
import re

GEMINI_API_KEY = "CHAVE_PROTEGIDA_PELO_GITHUB"
PEXELS_API_KEY = "ZDVYI1O1R3OrviJOBBpaZ3T0uthdICSCNts6fRTBoyuJCxIlAJFpb1dg"

PASTA = "/sdcard/Download/ImagensIA"
os.makedirs(PASTA, exist_ok=True)

def otimizar_busca(tema):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{
                "text": f"Responda APENAS com uma frase curta em inglês para busca de imagens.\nTema: {tema}"
            }]
        }]
    }

    r = requests.post(url, json=payload)
    data = r.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip().split("\n")[0]
    except:
        return tema

def buscar_imagens(query, total=5):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": total}

    r = requests.get(url, headers=headers, params=params)
    return r.json().get("photos", [])

def limpar(nome):
    return re.sub(r'[\\/*?:"<>|]', "_", nome)

def baixar(url, destino):
    r = requests.get(url)
    with open(destino, "wb") as f:
        f.write(r.content)

tema = input("Tema da imagem: ")

print("\nOtimizando com Gemini...")
query = otimizar_busca(tema)

print("Busca:", query)

print("\nProcurando imagens...")

fotos = buscar_imagens(query, 5)

if not fotos:
    print("Nada encontrado.")
    exit()

tema_limpo = limpar(tema)

for i, foto in enumerate(fotos, 1):
    url = foto["src"]["large"]
    arquivo = f"{PASTA}/{tema_limpo}_{i}.jpg"

    print(f"Baixando {i}...")
    baixar(url, arquivo)

print("\nConcluído! Arquivos em:", PASTA)
