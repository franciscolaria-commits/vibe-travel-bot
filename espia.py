import base_de_datos
import notificador
import os
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. CONFIGURACIÓN ---
VUELOS_TARGET = [
    { "ciudad": "MADRID", "url": "https://www.turismocity.com.ar/vuelos-baratos-a-MAD-Barajas?currency=USD&flexDates=true&from=MDZ" },
    { "ciudad": "ROMA", "url": "https://www.turismocity.com.ar/vuelos-baratos-a-ROM-Roma_Italia?currency=USD&flexDates=true&from=MDZ" },
    { "ciudad": "BARCELONA", "url": "https://www.turismocity.com.ar/vuelos-baratos-a-BCN-Barcelona_Intl?currency=USD&flexDates=true&from=MDZ" },
    { "ciudad": "LONDRES", "url": "https://www.turismocity.com.ar/vuelos-baratos-a-LON-Londres_Reino_Unido?currency=USD&flexDates=true&from=MDZ" },
    { "ciudad": "PARIS", "url": "https://www.turismocity.com.ar/vuelos-baratos-a-PAR-Paris_Francia?currency=USD&flexDates=true&from=MDZ" }
]

def limpiar_precio(texto_sucio):
    if not texto_sucio: return 99999999
    texto = texto_sucio.upper()
    basura = ["US", "ARG", "$", ".", " ", "\n", "\t", "DESDE"]
    for b in basura:
        texto = texto.replace(b, "")
    try:
        return int(texto)
    except ValueError:
        return 99999999

# --- 2. EL ROBOT ---
def run_bot():
    print("🤖 INICIANDO VIBE TRAVEL BOT - PROTOCOLO F5 🔄")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # User Agent Rotativo (Básico)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--lang=es-AR")
    
    # Evasión de detección
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    mensajes_alerta = [] 

    try:
        for objetivo in VUELOS_TARGET:
            ciudad = objetivo["ciudad"]
            url = objetivo["url"]
            
            # Descanso aleatorio
            sleep_time = random.uniform(5, 10)
            print(f"\n💤 Descansando {sleep_time:.1f}s antes de atacar {ciudad}...")
            time.sleep(sleep_time)

            print(f"✈️  Destino: {ciudad}")
            driver.get(url)
            
            # --- LÓGICA DE EVASIÓN REFORZADA (REFRESH) ---
            titulo = driver.title
            
            # Si nos frena Cloudflare...
            if "Just a moment" in titulo or "Attention Required" in titulo:
                print("🛡️ ¡ALERTA! Cloudflare detectado.")
                print("   ⏳ Esperando 5s antes de contraatacar...")
                time.sleep(5)
                
                print("   🔄 ¡REFRESCANDO PÁGINA (F5)!...")
                driver.refresh() # <--- EL SECRETO: Recargar suele validar la sesión
                
                print("   ⏳ Esperando 20s a que nos dejen pasar...")
                time.sleep(20) # Le damos tiempo de sobra
                titulo = driver.title # Volvemos a leer
            
            print(f"   👀 Título Final: {titulo}")
            
            precios_validos = []
            
            # 1. INTENTO POR TÍTULO
            try:
                match = re.search(r'(?:USD|\$)\s*([\d\.]+)', titulo)
                if match:
                    p = int(match.group(1).replace('.', ''))
                    if p > 500: 
                        precios_validos.append(p)
                        print(f"   🎯 Título cantó el precio: ${p}")
            except: pass

            # 2. INTENTO POR HTML (Si el título falló)
            if not precios_validos:
                if "Just a moment" not in titulo: # Solo buscamos si pasamos el filtro
                    print("   🔎 Buscando en el contenido HTML...")
                    try:
                        # Buscamos en Gráfico
                        barras = driver.find_elements(By.CLASS_NAME, "chart-price-text")
                        for el in barras:
                            p = limpiar_precio(el.get_attribute("textContent"))
                            if p > 500: precios_validos.append(p)
                        
                        # Buscamos en Lista
                        if not precios_validos:
                            lista = driver.find_elements(By.XPATH, "//span[contains(text(), '$')]")
                            for el in lista:
                                p = limpiar_precio(el.get_attribute("textContent"))
                                if p > 500 and p < 10000000: precios_validos.append(p)
                    except: pass
                else:
                    print("   ❌ Seguimos bloqueados. Saltando...")

            if not precios_validos:
                print(f"❌ FALLÓ: No pudimos obtener precio de {ciudad}.")
                continue

            # --- ÉXITO ---
            mejor = min(precios_validos)
            print(f"💰 PRECIO CONFIRMADO: ${mejor:,}")

            base_de_datos.guardar_precio("MDZ", ciudad, "FLEXIBLE", mejor)
            min_hist = base_de_datos.obtener_mejor_precio_historico(ciudad)
            
            if mejor <= min_hist:
                mensajes_alerta.append(f"✅ *{ciudad}*: ${mejor:,}")

        # --- NOTIFICACIÓN ---
        if mensajes_alerta:
            print("\n🚨 PREPARANDO NOTIFICACIÓN...")
            cuerpo = "\n".join(mensajes_alerta)
            texto = f"🤖 *VibeTravel* ✈️\n\n{cuerpo}\n\nLink: https://franciscolaria-commits.github.io/vibe-travel-bot/"
            try:
                notificador.enviar_mensaje(texto)
            except:
                print("❌ Falló el envío de WhatsApp (Revisar token/número)")
        else:
            print("\n💤 Precios estables. Sin novedades.")

    except Exception as e:
        print(f"🔥 Error General: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()