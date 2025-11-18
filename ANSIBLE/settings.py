# settings.py
from dotenv import load_dotenv
import os
load_dotenv()

MYSQL_CONFIG = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASS"),
    'host': os.getenv("DB_HOST"),
    'port': os.getenv("DB_PORT"),
    'database': os.getenv("DB_NAME"),
}

# Tiempo máximo permitido entre ciclos del data collector
TOLERANCIA_SEG = 1

# ====================== MAPEO DE INTERFACES ==========================
INTERFACE_MAP = {
    10001: "FastEthernet0/1",
    10002: "FastEthernet0/2",
    10003: "FastEthernet0/3",
    10004: "FastEthernet0/4",
    10005: "FastEthernet0/5",
    10006: "FastEthernet0/6",
    10007: "FastEthernet0/7",
    10008: "FastEthernet0/8",
    10009: "FastEthernet0/9",
    10010: "FastEthernet0/10",
    10011: "FastEthernet0/11",
    10012: "FastEthernet0/12",
    10013: "FastEthernet0/13",
    10014: "FastEthernet0/14",
    10015: "FastEthernet0/15",
    10016: "FastEthernet0/16",
    10017: "FastEthernet0/17",
    10018: "FastEthernet0/18",
    10019: "FastEthernet0/19",
    10020: "FastEthernet0/20",
    10021: "FastEthernet0/21",
    10022: "FastEthernet0/22"
}

# Dispositivos involucrados en mitigación
SWITCHES_MONITOREADOS = ["S1.cisco.local", "S2.cisco.local"]

# Ruta de modelo
MODEL_PATH ="models_autogluon/20251116_195305_ROUTER"
