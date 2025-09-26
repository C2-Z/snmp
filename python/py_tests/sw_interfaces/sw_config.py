# sw_config.py
import os
from dotenv import load_dotenv
import ast

load_dotenv()

# Configuración específica para switches
COMMUNITY = os.getenv("COMMUNITY")
SWITCH_IPS = [ip for ip in ast.literal_eval(os.getenv("TARGET_IPS")) if ip != "192.168.99.1"]  # Excluye el router
TARGET_PORT = int(os.getenv("TARGET_PORT"))

# OIDs relevantes para interfaces activas
OIDS_SWITCH = {
    "ifNumber": "1.3.6.1.2.1.2.1.0",  # Número total de interfaces
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",  # Estado operativo (1 = up)
    "ifInOctets": "1.3.6.1.2.1.2.2.1.10",  # Octetos entrantes
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",  # Octetos salientes
    "ifInUcastPkts": "1.3.6.1.2.1.2.2.1.11",  # Paquetes unicast entrantes
    "ifOutUcastPkts": "1.3.6.1.2.1.2.2.1.17"  # Paquetes unicast salientes
}