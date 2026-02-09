import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv 

load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = "vibe_travel_db"

def obtener_conexion():
    """Conecta a la base de datos en la nube TiDB"""
    try:
        conexion = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            auth_plugin='mysql_native_password'
        )
        return conexion
    except Exception as e:
        # Si falla porque la base no existe, intentamos conectar sin base para crearla
        if "Unknown database" in str(e):
            conexion = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
                auth_plugin='mysql_native_password'
            )
            cursor = conexion.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"✅ Base de datos {DB_NAME} creada en la nube.")
            conexion.database = DB_NAME
            return conexion
        else:
            print(f"🔥 Error de conexión a BD: {e}")
            raise e

def crear_tablas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla mejorada para soportar múltiples destinos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios_vuelos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fecha_rastreo DATETIME,
            origen VARCHAR(10),
            destino VARCHAR(50),
            mes_viaje VARCHAR(20),
            precio INT
        )
    ''')
    conn.commit()
    conn.close()
    print(" Tabla verificada en la nube.")

def guardar_precio(origen, destino, mes_viaje, precio):
    conn = obtener_conexion()
    cursor = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sql = "INSERT INTO precios_vuelos (fecha_rastreo, origen, destino, mes_viaje, precio) VALUES (%s, %s, %s, %s, %s)"
    val = (fecha_hoy, origen, destino, mes_viaje, precio)
    
    cursor.execute(sql, val)
    conn.commit()
    conn.close()
    print(f"  Guardado en Nube: {destino} ({mes_viaje}) -> ${precio}")

def obtener_mejor_precio_historico(destino):
    """Devuelve el precio mínimo histórico para un destino"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    # Buscamos el mínimo precio JAMÁS visto para ese destino
    cursor.execute("SELECT MIN(precio) FROM precios_vuelos WHERE destino = %s", (destino,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado and resultado[0]:
        return resultado[0]
    return 999999999 # Si no hay historia, devolvemos un número gigante
def obtener_tablero_comandos():
    """
    Recupera el ÚLTIMO precio registrado para cada destino.
    Devuelve una lista de diccionarios con la info para el Dashboard.
    """
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True) # Importante: dictionary=True para acceder por nombre
    
    # Esta Query es nivel Dios. 
    # Busca el registro más reciente (MAX id) para cada destino agrupado.
    query = """
    SELECT p.destino, p.precio, p.fecha_rastreo
    FROM precios_vuelos p
    INNER JOIN (
        SELECT destino, MAX(id) as max_id
        FROM precios_vuelos
        GROUP BY destino
    ) ultimos ON p.id = ultimos.max_id
    ORDER BY p.precio ASC;
    """
    
    cursor.execute(query)
    resultados = cursor.fetchall()
    conn.close()
    return resultados

if __name__ == "__main__":
    print("🧪 Iniciando prueba de conexión segura...")
    
    try:
        # 1. Probamos crear la tabla (esto valida usuario/pass)
        crear_tablas()
        
        # 2. Probamos guardar un dato falso
        guardar_precio("TEST", "MENDOZA", "PRUEBA_DB", 100)
        
        # 3. Probamos leer el historial
        precio = obtener_mejor_precio_historico("MENDOZA")
        print(f"✅ ¡Lectura exitosa! Mejor precio histórico: {precio}")
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")