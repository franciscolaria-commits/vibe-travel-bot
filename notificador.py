import requests
import json

# --- CONFIGURACIÓN DE META (Sacá esto de la web de developers) ---
# 1. El Token larguísimo que empieza con EAA...
TOKEN = "EAAVl9jv0l9EBQtFQfSWBqW7blVBnYG3oFxGfj65QAbtqQ6YmByFzLtLKYpUagrHY3iiYU6tTXalEedYMbLoG7Qghj6gMeK73yfD9ZB9qUIvmcCoTZCCtHMvmSzsH3t4zt2xIWzdH1Ii7E64SKZC5jClu3UjcfZB3VfMAytc8fykPR8pXtjU5EtVB6mkVlQZDZD"

# 2. El "Identificador del número de teléfono" (Phone Number ID)
PHONE_ID = "948544151679718"

# 3. Tu número verificado (Al que le llega el mensaje)
# Formato: 54 + 9 + codigo + numero (Ej: 549264xxxxxxx)
NUMERO_DESTINO = "54264154517903" 

def enviar_mensaje(texto):
    """
    Envía un mensaje de texto usando la API Oficial de WhatsApp (Meta).
    Doc: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
    """
    print(f"📨 Enviando mensaje a Meta...")
    
    # URL Oficial de la API (v17.0 o superior)
    url = f"https://graph.facebook.com/v17.0/{PHONE_ID}/messages"
    
    # Cabeceras de seguridad (Authorization)
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # El cuerpo del mensaje (JSON)
    # Meta es estricto con esta estructura. No le erres a las llaves.
    payload = {
        "messaging_product": "whatsapp",
        "to": NUMERO_DESTINO,
        "type": "text",
        "text": {
            "body": texto,
            "preview_url": True # Permite ver una miniatura si mandás un link
        }
    }
    
    try:
        # Hacemos el POST
        respuesta = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Analizamos qué pasó
        datos_respuesta = respuesta.json()
        
        if respuesta.status_code == 200:
            print("✅ ¡Mensaje entregado a Meta!")
            # print(datos_respuesta) # Descomentá si querés ver el ID del mensaje
            return True
        else:
            print(f"❌ Error de Meta: {respuesta.status_code}")
            print(datos_respuesta) # Esto te dice QUÉ falló (ej: token vencido)
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión fatal: {e}")
        return False

# Prueba unitaria
if __name__ == "__main__":
    enviar_mensaje("🤖 *Hola Dev!* Esta es la API Oficial de Meta funcionando. 🚀")