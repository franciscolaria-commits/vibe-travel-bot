import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno (para cuando corrés en local)
load_dotenv()

# --- CONFIGURACIÓN DE META (Leída desde variables de entorno) ---
TOKEN = os.getenv("META_TOKEN")
PHONE_ID = os.getenv("META_PHONE_ID")
NUMERO_DESTINO = os.getenv("META_RECIPIENT_PHONE")

def enviar_mensaje(texto):
    """
    Envía un mensaje de texto usando la API Oficial de WhatsApp (Meta).
    """
    # Verificación de seguridad básica
    if not TOKEN or not PHONE_ID or not NUMERO_DESTINO:
        print("❌ ERROR: Faltan configurar las variables de entorno de Meta.")
        return False

    print(f"📨 Enviando mensaje a Meta...")
    
    url = f"https://graph.facebook.com/v17.0/{PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": NUMERO_DESTINO,
        "type": "text",
        "text": {
            "body": texto,
            "preview_url": True
        }
    }
    
    try:
        respuesta = requests.post(url, headers=headers, data=json.dumps(payload))
        datos_respuesta = respuesta.json()
        
        if respuesta.status_code == 200:
            print("✅ ¡Mensaje entregado a Meta!")
            return True
        else:
            print(f"❌ Error de Meta: {respuesta.status_code}")
            print(datos_respuesta)
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión fatal: {e}")
        return False

if __name__ == "__main__":
    enviar_mensaje("🤖 *Hola Dev!* Prueba de seguridad exitosa. 🔐")