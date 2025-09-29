#config.py
import os
from dotenv import load_dotenv
import ast

load_dotenv()

COMMUNITY = os.getenv("COMMUNITY")
TARGET_IPS = ast.literal_eval(os.getenv("TARGET_IPS"))
INTERFACES = ast.literal_eval(os.getenv("INTERFACES"))
TARGET_PORT = int(os.getenv("TARGET_PORT"))

# OIDs de interfaz (requieren índice de interfaz)
INTERFACE_OIDS = {
    "ifInOctets": "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",
    "ifOutDiscards": "1.3.6.1.2.1.2.2.1.19",
    "ifInUcastPkts": "1.3.6.1.2.1.2.2.1.11",
    "ifInDiscards": "1.3.6.1.2.1.2.2.1.13",
    "ifOutUcastPkts": "1.3.6.1.2.1.2.2.1.17"
}

# OIDs escalares (no requieren índice de interfaz)
SCALAR_OIDS = {
    "sysName": "1.3.6.1.2.1.1.5.0",
    "ipInReceives": "1.3.6.1.2.1.4.3.0",
    "ipInDelivers": "1.3.6.1.2.1.4.9.0",
    "ipOutRequests": "1.3.6.1.2.1.4.10.0",
    "ipOutDiscards": "1.3.6.1.2.1.4.11.0",
    "ipInDiscards": "1.3.6.1.2.1.4.8.0",
    "ipForwDatagrams": "1.3.6.1.2.1.4.6.0",
    "ipOutNoRoutes": "1.3.6.1.2.1.4.12.0",
    "ipInAddrErrors": "1.3.6.1.2.1.4.5.0"
}

MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "port": 3306,
    "database": os.getenv("DB_NAME")
}