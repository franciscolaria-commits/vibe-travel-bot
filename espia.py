import base_de_datos
import notificador
import os
import time
import random # <--- NUEVO: Para tiempos humanos
import re     # <--- NUEVO: Para leer el título
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. CONFIGURACIÓN DE LA MISIÓN ---
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

# --- 3. EL ROBOT ---
def run_bot():
    print("🤖 INICIANDO VIBE TRAVEL BOT - MODO ANTI-CLOUDFLARE 🛡️")
    
    # --- CONFIGURACIÓN CHROME CAMUFLADO ---
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Disfraz de Humano
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--lang=es-AR")
    
    # Trucos para ocultar que es automatizado
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Truco JavaScript extra para ocultar Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    mensajes_alerta = [] 

    try:
        for objetivo in VUELOS_TARGET:
            ciudad = objetivo["ciudad"]
            url = objetivo["url"]
            
            # PAUSA HUMANIZADA ENTRE CIUDADES (Para no saturar y parecer humano)
            tiempo_espera = random.uniform(3, 7)
            print(f"\n💤 Descansando {tiempo_espera:.1f}s antes de ir a {ciudad}...")
            time.sleep(tiempo_espera)

            print(f"✈️  Destino: {ciudad}")
            driver.get(url)
            
            # --- LÓGICA ANTI-BLOQUEO "JUST A MOMENT" ---
            titulo = driver.title
            if "Just a moment" in titulo or "Attention Required" in titulo:
                print("🛡️ Cloudflare nos frenó. Esperando 15s a que nos deje pasar...")
                time.sleep(15) # Esperamos a que la sala de espera nos redirija automáticamente
                titulo = driver.title # Volvemos a leer el título
            
            print(f"   👀 Título Final: {titulo}")
            
            precios_validos = []
            
            # ESTRATEGIA 0: El Título (La más efectiva)
            try:
                # Busca patrones como "USD 1.200" o "$1200" o "USD1200" en el título de la pestaña
                match = re.search(r'(?:USD|\$)\s*([\d\.]+)', titulo)
                if match:
                    precio_str = match.group(1).replace('.', '')
                    precio_titulo = int(precio_str)
                    if precio_titulo > 500: 
                        precios_validos.append(precio_titulo)
                        print(f"   🎯 Estrategia 0 (Título) encontró: ${precio_titulo}")
            except Exception as e:
                print(f"   ⚠️ Error leyendo título: {e}")

            # Si el título falló, cargamos la web completa
            if not precios_validos:
                print("⏳ Título sin precio. Cargando web completa (Esperando 8s)...")
                time.sleep(8) 

                # ESTRATEGIA 1: Gráfico
                try:
                    barras = driver.find_elements(By.CLASS_NAME, "chart-price-text")
                    for el in barras:
                        p = limpiar_precio(el.get_attribute("textContent"))
                        if p > 500: precios_validos.append(p)
                    if barras: print(f"   📊 Estrategia 1 (Gráfico) encontró precios.")
                except: pass

                # ESTRATEGIA 2: Lista (Plan C)
                if not precios_validos:
                    try:
                        lista = driver.find_elements(By.XPATH, "//span[contains(text(), '$') or contains(text(), 'USD')]")
                        for el in lista:
                            p = limpiar_precio(el.get_attribute("textContent"))
                            if p > 500 and p < 10000000: precios_validos.append(p)
                        if lista: print(f"   📋 Estrategia 2 (Lista) buscó precios.")
                    except: pass

            if not precios_validos:
                print(f"❌ FALLÓ: Cloudflare ganó esta ronda en {ciudad}.")
                continue

            # --- PROCESAMIENTO ---
            mejor_precio_hoy = min(precios_validos)
            print(f"💰 MEJOR PRECIO FINAL: ${mejor_precio_hoy:,}")

            base_de_datos.guardar_precio("MDZ", ciudad, "FLEXIBLE", mejor_precio_hoy)
            min_historico = base_de_datos.obtener_mejor_precio_historico(ciudad)
            
            if mejor_precio_hoy <= min_historico:
                print("🔥 ¡RÉCORD HISTÓRICO!")
                mensajes_alerta.append(f"✅ *{ciudad}*: ${mejor_precio_hoy:,}")

        # --- REPORTE FINAL ---
        if mensajes_alerta:
            print("\n🚨 MANDANDO NOTIFICACIÓN...")
            cuerpo = "\n".join(mensajes_alerta)
            texto = f"🤖 *VibeTravel Report* ✈️\nOrigen: Mendoza\n\n{cuerpo}\n\n¡Mirá la web para más detalles!"
            notificador.enviar_mensaje(texto)
        else:
            print("\n💤 Nada interesante hoy.")

    except Exception as e:
        print(f"🔥 Error Crítico: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()