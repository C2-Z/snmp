# db_service.py
import mysql.connector
from mysql.connector import Error
from config import NUMERIC_COLUMNS

class DatabaseService:
    def __init__(self, config, oids):
        """Inicializa la conexión a MySQL y almacena los OIDs."""
        self.config = config
        self.oids = oids
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
        """Inserta los datos SNMP en la tabla snmp_data dinámicamente."""
        try:
            cursor = self.connection.cursor()
            
            # Usar todas las claves de OIDS como columnas
            columns = list(self.oids.keys())
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO snmp_data ({columns_str}) VALUES ({placeholders})"
            
            values = []
            for col in columns:
                oid = self.oids.get(col, '')
                value = snmp_data.get(oid, '0' if col in NUMERIC_COLUMNS else '')
                try:
                    values.append(int(value) if col in NUMERIC_COLUMNS else value)
                except ValueError as e:
                    print(f"Error convirtiendo valor para {col} (OID {oid}): {value}. Usando valor por defecto.")
                    values.append(0 if col in NUMERIC_COLUMNS else '')
            values = tuple(values)
            
            cursor.execute(insert_query, values)
            self.connection.commit()
            print("Datos insertados exitosamente:", values)
        except Error as e:
            print(f"Error al insertar datos: {e}")
        finally:
            cursor.close()

    def close(self):
        """Cierra la conexión a MySQL."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a MySQL cerrada.")