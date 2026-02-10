import base_de_datos
import notificador
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. CONFIGURACIÓN DE LA MISIÓN ---
VUELOS_TARGET = [
    {
        "ciudad": "MADRID",
        "url": "https://www.turismocity.com.ar/vuelos-baratos-a-MAD-Barajas?currency=USD&flexDates=true&from=MDZ" 
    },
    {
        "ciudad": "ROMA",
        "url": "https://www.turismocity.com.ar/vuelos-baratos-a-ROM-Roma_Italia?currency=USD&flexDates=true&from=MDZ"
    },
    {
        "ciudad": "BARCELONA",
        "url": "https://www.turismocity.com.ar/vuelos-baratos-a-BCN-Barcelona_Intl?currency=USD&flexDates=true&from=MDZ"
    },
    {
        "ciudad": "LONDRES",
        "url": "https://www.turismocity.com.ar/vuelos-baratos-a-LON-Londres_Reino_Unido?currency=USD&flexDates=true&from=MDZ"
    },
    {
        "ciudad": "PARIS",
        "url": "https://www.turismocity.com.ar/vuelos-baratos-a-PAR-Paris_Francia?currency=USD&flexDates=true&from=MDZ"
    }
]

# --- 2. FILTROS ---
MESES_PROHIBIDOS = ["JULIO", "JUL", "DICIEMBRE", "DIC", "DECEMBER", "JULY"]

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
    print("🤖 INICIANDO VIBE TRAVEL BOT - MODO MULTI-DESTINO")
    
    # --- CONFIGURACIÓN CHROME (MODO NUBE CAMUFLADO) ---
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # No abrir ventana
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # 🎭 EL DISFRAZ (Clave para que no nos bloqueen)
    # 1. User-Agent: Decimos que somos un Windows 10 común y corriente
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    
    # 2. Idioma: Decimos que hablamos Español de Argentina (importante para los precios)
    options.add_argument("--lang=es-AR")
    
    # 3. Ocultar que es automatizado (Truco avanzado)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Ejecutar script para engañar a las protecciones de JavaScript
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    mensajes_alerta = [] 

    try:
        for objetivo in VUELOS_TARGET:
            ciudad = objetivo["ciudad"]
            url = objetivo["url"]
            
            print(f"\n✈️  Destino: {ciudad} (Saliendo de MDZ)")
            
            driver.get(url)
            
            # --- DEBUG Y ESTRATEGIA 0 (EL TÍTULO) ---
            titulo = driver.title
            print(f"   👀 Título detectado: {titulo}")
            
            precios_validos = []
            
            # INTENTO 0: Leer el precio directo del título (Suele ser el más barato)
            # Busca patrones como "USD 839", "USD839", "$839"
            try:
                match = re.search(r'(?:USD|\$)\s*([\d\.]+)', titulo)
                if match:
                    precio_str = match.group(1).replace('.', '')
                    precio_titulo = int(precio_str)
                    if precio_titulo > 500: # Filtro básico
                        precios_validos.append(precio_titulo)
                        print(f"   🎯 Estrategia 0 (Título) encontró: ${precio_titulo}")
            except Exception as e:
                print(f"   ⚠️ No pude sacar precio del título: {e}")

            # Si el título nos dio un precio, genial. Pero igual cargamos la web por si hay más.
            print("⏳ Cargando página... (Esperando 8s)")
            time.sleep(8) 

            # ESTRATEGIA 1: Buscar en el Gráfico de Barras
            try:
                barras = driver.find_elements(By.CLASS_NAME, "chart-price-text")
                for el in barras:
                    p = limpiar_precio(el.get_attribute("textContent"))
                    if p > 500: precios_validos.append(p)
                
                if barras:
                    print(f"   📊 Estrategia 1 (Gráfico) encontró precios adicionales.")
            except:
                pass

            # ESTRATEGIA 2: Buscar en la lista (Plan C)
            if not precios_validos:
                try:
                    elementos_lista = driver.find_elements(By.XPATH, "//span[contains(text(), '$') or contains(text(), 'USD')]")
                    for el in elementos_lista:
                        p = limpiar_precio(el.get_attribute("textContent"))
                        if p > 500 and p < 10000000: 
                            precios_validos.append(p)
                    print(f"   📋 Estrategia 2 (Lista) buscó precios.")
                except:
                    pass

            if not precios_validos:
                print(f"❌ FALLÓ: No encontré precio para {ciudad} ni en el título ni en la web.")
                continue

            # --- ELEGIR EL MEJOR ---
            mejor_precio_hoy = min(precios_validos)
            print(f"💰 MEJOR PRECIO FINAL: ${mejor_precio_hoy:,}")

            base_de_datos.guardar_precio("MDZ", ciudad, "FLEXIBLE", mejor_precio_hoy)
            min_historico = base_de_datos.obtener_mejor_precio_historico(ciudad)
            
            if mejor_precio_hoy <= min_historico:
                print("🔥 ¡RÉCORD HISTÓRICO!")
                mensajes_alerta.append(f"✅ *{ciudad}*: ${mejor_precio_hoy:,}")
            
            time.sleep(2)

        # --- REPORTE FINAL ---
        if mensajes_alerta:
            print("\n🚨 MANDANDO RESUMEN A MAMÁ...")
            cuerpo_mensaje = "\n".join(mensajes_alerta)
            texto_ws = f"🤖 *VibeTravel Report* ✈️\nOrigen: Mendoza\n\n{cuerpo_mensaje}\n\n¡Entrá a la web para ver fechas!"
            notificador.enviar_mensaje(texto_ws)
        else:
            print("\n💤 Nada interesante hoy en ningún destino.")

    except Exception as e:
        print(f"🔥 Error Crítico del Bot: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_bot()