import base_de_datos

def limpiar():
    print("🧹 Iniciando limpieza de datos de prueba...")
    
    conn = base_de_datos.obtener_conexion()
    cursor = conn.cursor()
    
    # SQL: Borrar todo lo que tenga precio 100 o que el destino sea "MENDOZA" (que era el test)
    query = "DELETE FROM precios_vuelos WHERE precio = 100 OR destino = 'MENDOZA'"
    
    cursor.execute(query)
    conn.commit() # Confirmar cambios
    
    filas_borradas = cursor.rowcount
    print(f"✅ Se eliminaron {filas_borradas} registros basura.")
    
    conn.close()

if __name__ == "__main__":
    limpiar()