import os
from dotenv import load_dotenv
import ast
load_dotenv()

COMMUNITY = os.getenv("COMMUNITY")
TARGET_IPS = ast.literal_eval(os.getenv("TARGET_IPS"))  # Convierte cadena a lista
TARGET_PORT = int(os.getenv("TARGET_PORT"))

# OIDs para monitoreo
OIDS = {
    "sysName": "1.3.6.1.2.1.1.5.0",
    "ifInOctets_1": "1.3.6.1.2.1.2.2.1.10.1",
    "ifOutOctets_1": "1.3.6.1.2.1.2.2.1.16.1",
    "ifOutDiscards_1": "1.3.6.1.2.1.2.2.1.19.1",
    "ifInUcastPkts_1": "1.3.6.1.2.1.2.2.1.11.1",
    "ifInNUcastPkts_1": "1.3.6.1.2.1.2.2.1.12.1",
    "ifInDiscards_1": "1.3.6.1.2.1.2.2.1.13.1",
    "ifOutUcastPkts_1": "1.3.6.1.2.1.2.2.1.17.1",
    "ifOutNUcastPkts_1": "1.3.6.1.2.1.2.2.1.18.1",
    "ipInReceives": "1.3.6.1.2.1.4.3.0",
    "ipInDelivers": "1.3.6.1.2.1.4.9.0",
    "ipOutRequests": "1.3.6.1.2.1.4.10.0",
    "ipOutDiscards": "1.3.6.1.2.1.4.11.0",
    "ipInDiscards": "1.3.6.1.2.1.4.8.0",
    "ipForwDatagrams": "1.3.6.1.2.1.4.6.0",
    "ipOutNoRoutes": "1.3.6.1.2.1.4.12.0",
    "ipInAddrErrors": "1.3.6.1.2.1.4.5.0"
}
NUMERIC_COLUMNS = [
    "ifInOctets_1", "ifOutOctets_1", "ifOutDiscards_1", "ifInUcastPkts_1",
    "ifInNUcastPkts_1", "ifInDiscards_1", "ifOutUcastPkts_1", "ifOutNUcastPkts_1",
    "ipInReceives", "ipInDelivers", "ipOutRequests", "ipOutDiscards",
    "ipInDiscards", "ipForwDatagrams", "ipOutNoRoutes", "ipInAddrErrors"
]

MYSQL_CONFIG = {
    "host":  os.getenv("DB_HOST"),
    "user":  os.getenv("DB_USER"),
    "password":  os.getenv("DB_PASS"),
    "port": 3306,
    "database": os.getenv("DB_NAME")
}
