#db_handler.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

class DatabaseService:
    def __init__(self, mysql_config, oids_base):
        """Inicializa la conexión a la base de datos."""
        self.mysql_config = mysql_config
        self.oids_base = oids_base
        self.connection = None
        try:
            self.connection = mysql.connector.connect(**self.mysql_config)
            print("Conexión a MySQL exitosa.")
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")

    def insert_snmp_data(self, device_ip, snmp_data, device_oids, if_name):
        """Inserta datos SNMP en la tabla snmp_data_test."""
        if not self.connection or not self.connection.is_connected():
            print("No hay conexión activa a la base de datos.")
            return

        cursor = self.connection.cursor()

        # Mapear los datos SNMP a las columnas basadas en los OIDs
        values = {}
        for oid, value in snmp_data.items():
            for metric, base_oid in device_oids.items():
                if oid.startswith(base_oid):
                    if metric in self.oids_base and value is not None:
                        if metric in ["sysName"]:
                            values[metric] = value
                        else:
                            values[metric] = int(value)

        # Preparar la consulta SQL
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO snmp_data (timestamp, device_ip, {columns}, label, if_name) VALUES (%s, %s, {placeholders}, %s, %s)"

        # Valores a insertar
        timestamp = datetime.now()
        data_values = [timestamp, device_ip] + list(values.values()) + [0, if_name]

        try:
            cursor.execute(query, data_values)
            self.connection.commit()
            print(f"Datos guardados para {device_ip}, interfaz {if_name}")
        except Error as e:
            print(f"Error al insertar datos para {device_ip}: {e}")
        finally:
            cursor.close()

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a MySQL cerrada.")