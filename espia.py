import base_de_datos
import notificador
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. CONFIGURACIÓN DE LA MISIÓN (Acá pegás tus 5 URLs) ---
# Usamos una lista de diccionarios. Es la forma PRO de organizar datos.
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

# --- 2. FILTROS (Lógica de Negocio) ---
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

def es_mes_valido(texto_fecha):
    """
    Analiza si el texto (ej: 'Enero 2025') cae en meses prohibidos.
    Retorna True si podemos viajar, False si es fecha prohibida.
    """
    if not texto_fecha: return True # Ante la duda, dejamos pasar
    texto = texto_fecha.upper()
    
    for mes_malo in MESES_PROHIBIDOS:
        if mes_malo in texto:
            return False # Encontró un mes prohibido
    return True

# --- 3. EL ROBOT ---
def run_bot():
    print("🤖 INICIANDO VIBE TRAVEL BOT - MODO MULTI-DESTINO")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") # Descomentar para producción en GitHub
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    mensajes_alerta = [] # Acá vamos acumulando las buenas noticias

    try:
        # BUCLE PRINCIPAL: Recorremos cada destino de la lista
        for objetivo in VUELOS_TARGET:
            ciudad = objetivo["ciudad"]
            url = objetivo["url"]
            
            print(f"\n✈️  Destino: {ciudad} (Saliendo de MDZ)")
            print(f"    URL: {url[:60]}...") # Mostramos solo el principio para no ensuciar
            
            driver.get(url)
            
            # Esperamos a que cargue algo de precios
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "chart-price-text"))
                )
            except:
                print(f"⚠️  Timeout esperando gráfico en {ciudad}. Saltando...")
                continue # Pasa al siguiente destino sin romper todo

            # Capturamos precios Y FECHAS
            # OJO: En la vista de barras, a veces el mes está en un 'tooltip' o eje X.
            # Por ahora, vamos a scrapear el precio mínimo general del gráfico.
            # (Para filtrar por mes exacto necesitamos inspeccionar el eje X, 
            #  probemos primero capturar el precio global).
            
            elementos_precios = driver.find_elements(By.CLASS_NAME, "chart-price-text")
            precios_validos = []
            
            for el in elementos_precios:
                precio_limpio = limpiar_precio(el.get_attribute("textContent"))
                if precio_limpio > 1000: # Filtro anti-basura (por si lee un 0)
                    precios_validos.append(precio_limpio)
            
            if not precios_validos:
                print(f"❌ No encontré precios para {ciudad}.")
                continue

            mejor_precio_hoy = min(precios_validos)
            print(f"💰 Mejor precio detectado hoy: ${mejor_precio_hoy:,}")

            # --- CEREBRO: Comparar con Historia ---
            # Asumimos "MES FLEXIBLE" en la BD por ahora
            base_de_datos.guardar_precio("MDZ", ciudad, "FLEXIBLE", mejor_precio_hoy)
            
            min_historico = base_de_datos.obtener_mejor_precio_historico(ciudad)
            
            # Lógica de Oportunidad (Gatillo)
            # Si el precio de hoy es IGUAL o MENOR al histórico, es candidato
            if mejor_precio_hoy <= min_historico:
                print("🔥 ¡OJO! Está en su mínimo histórico.")
                mensajes_alerta.append(f"✅ *{ciudad}*: ${mejor_precio_hoy:,} (Récord!)")
            
            # Pequeña pausa para no saturar al navegador
            time.sleep(2)

        # --- REPORTE FINAL ---
        # Si juntamos alertas de varios destinos, mandamos UN SOLO mensaje
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
    # Asegurate que base_de_datos.py tenga la conexión a TiDB configurada
    run_bot()