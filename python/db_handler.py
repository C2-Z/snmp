# db_service.py
import mysql.connector
from mysql.connector import Error

def extract_device_name(sys_descr):
    """Extrae el nombre del dispositivo desde sysDescr (segunda palabra)."""
    try:
        parts = sys_descr.split()
        return parts[1] if len(parts) > 1 else "Unknown"
    except Exception as e:
        print(f"Error al extraer nombre del dispositivo: {e}")
        return "Unknown"

class DatabaseService:
    def __init__(self, config):
        """Inicializa la conexión a MySQL."""
        self.config = config
        self.connection = None
        self.connect()

    def connect(self):
        """Establece la conexión a MySQL."""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                print("Conexión a MySQL exitosa.")
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")

    def insert_snmp_data(self, snmp_data):
        """Inserta los datos SNMP en la tabla snmp_data."""
        try:
            cursor = self.connection.cursor()
            
            device_name = extract_device_name(snmp_data.get('1.3.6.1.2.1.1.1.0', ''))
            
            insert_query = """
            INSERT INTO snmp_data (
                device_name,
                sysUpTime,
                ifNumber,
                ifAdminStatus_2,
                ifOperStatus_1
            ) VALUES (%s, %s, %s, %s, %s)
            """
            values = (
                device_name,
                int(snmp_data.get('1.3.6.1.2.1.1.3.0', 0)),
                int(snmp_data.get('1.3.6.1.2.1.2.1.0', 0)),
                int(snmp_data.get('1.3.6.1.2.1.2.2.1.7.2', 0)),
                int(snmp_data.get('1.3.6.1.2.1.2.2.1.8.1', 0))
            )
            
            cursor.execute(insert_query, values)
            self.connection.commit()
            print("Datos insertados exitosamente.")
        except Error as e:
            print(f"Error al insertar datos: {e}")
        finally:
            cursor.close()

    def close(self):
        """Cierra la conexión a MySQL."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a MySQL cerrada.")