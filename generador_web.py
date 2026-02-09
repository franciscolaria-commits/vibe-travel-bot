import base_de_datos
from datetime import datetime

# --- CONFIGURACIÓN DE LINKS ---
# Copiá acá las MISMAS URLs que pusiste en espia.py
# Esto sirve para que al hacer clic en la tarjeta, te lleve a comprar.
URLS_DESTINOS = {
    "MADRID": "https://www.turismocity.com.ar/vuelos-baratos-a-MAD-Barajas?currency=USD&flexDates=true&from=MDZ",
    "ROMA": "https://www.turismocity.com.ar/vuelos-baratos-a-ROM-Roma_Italia?currency=USD&flexDates=true&from=MDZ",
    "BARCELONA": "https://www.turismocity.com.ar/vuelos-baratos-a-BCN-Barcelona_Intl?currency=USD&flexDates=true&from=MDZ",
    "LONDRES": "https://www.turismocity.com.ar/vuelos-baratos-a-LON-Londres_Reino_Unido?currency=USD&flexDates=true&from=MDZ",
    "PARIS": "https://www.turismocity.com.ar/vuelos-baratos-a-PAR-Paris_Francia?currency=USD&flexDates=true&from=MDZ"
}

def generar_dashboard():
    print("🎨 Pintando el Dashboard V2 (Con Links)...")
    
    datos = base_de_datos.obtener_tablero_comandos()
    
    if not datos:
        print("❌ No hay datos para mostrar.")
        return

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VibeTravel Dashboard ✈️</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }}
            
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #1a1a1a; margin: 0; font-size: 1.8rem; }}
            .header p {{ color: #666; font-size: 0.9em; }}
            
            .container {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; 
                max-width: 1200px; 
                margin: 0 auto; 
            }}
            
            /* Hacemos que el link no parezca un link azul feo */
            a {{ text-decoration: none; color: inherit; display: block; }}
            
            .card {{ 
                background: white; 
                border-radius: 15px; 
                padding: 20px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                transition: transform 0.2s, box-shadow 0.2s;
                border-left: 5px solid #ccc;
                position: relative; /* Para acomodar etiquetas */
            }}
            
            /* Efecto al pasar el mouse: se levanta y brilla */
            .card:hover {{ 
                transform: translateY(-5px); 
                box-shadow: 0 10px 20px rgba(0,0,0,0.15);
                cursor: pointer;
            }}
            
            .card.winner {{ border-left-color: #00c851; background: linear-gradient(to right, #e8f5e9, #fff); }}
            .card.expensive {{ border-left-color: #ff4444; }}
            
            .destination {{ font-size: 1.4em; font-weight: 800; color: #333; display: flex; justify-content: space-between; align-items: center; }}
            .price {{ font-size: 2.2em; font-weight: 900; color: #2e7d32; margin: 10px 0; }}
            .date {{ font-size: 0.75em; color: #999; text-transform: uppercase; letter-spacing: 1px; }}
            .cta {{ font-size: 0.8em; color: #007bff; font-weight: bold; margin-top: 10px; display: block; }}
            
            .badge {{ 
                padding: 5px 10px; 
                border-radius: 20px; 
                font-size: 0.6em; 
                font-weight: bold; 
                color: white; 
                text-transform: uppercase;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            .badge-win {{ background-color: #00c851; }}
            
            .footer {{ text-align: center; margin-top: 50px; color: #aaa; font-size: 0.9em; font-weight: 500; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✈️ Tablero de Vuelos de Mamo</h1>
            <p>Salida: MENDOZA (MDZ) | Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="container">
    """

    precio_mas_bajo = datos[0]['precio'] 
    
    for vuelo in datos:
        destino = vuelo['destino']
        precio = vuelo['precio']
        fecha = vuelo['fecha_rastreo']
        
        # Buscamos la URL correspondiente (si no la encuentra, pone #)
        link_compra = URLS_DESTINOS.get(destino, "#")
        
        clase_css = "normal"
        etiqueta_html = ""
        texto_cta = "Ver oferta >"
        
        if precio == precio_mas_bajo:
            clase_css = "winner"
            etiqueta_html = '<span class="badge badge-win">🏆 MEJOR OPCIÓN</span>'
            texto_cta = "¡COMPRAR YA! 🔥"
        elif precio > precio_mas_bajo * 1.5: 
            clase_css = "expensive"
            
        html_content += f"""
        <a href="{link_compra}" target="_blank">
            <div class="card {clase_css}">
                <div class="destination">{destino} {etiqueta_html}</div>
                <div class="price">${precio:,}</div>
                <div class="date">Visto el: {fecha}</div>
                <span class="cta">{texto_cta}</span>
            </div>
        </a>
        """

    # Footer actualizado con tu firma
    html_content += """
        </div>
        <div class="footer">
            <p>Generado por Vibe Bot by Fran 🤖</p>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as file:
        file.write(html_content)
        
    print("✅ ¡Dashboard generado con links y firma!")

if __name__ == "__main__":
    generar_dashboard()