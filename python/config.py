import os
from dotenv import load_dotenv

load_dotenv()

COMMUNITY = os.getenv("COMMUNITY")
TARGET_IP = os.getenv("TARGET_IP")
TARGET_PORT = int(os.getenv("TARGET_PORT"))

OIDS = {
    "sysDescr": '1.3.6.1.2.1.1.1.0',
    "sysUpTime": '1.3.6.1.2.1.1.3.0',
    "ifNumber": '1.3.6.1.2.1.2.1.0',
    "ifAdminStatus": '1.3.6.1.2.1.2.2.1.7.2',
    "ifOperStatus": '1.3.6.1.2.1.2.2.1.8.1'
}

# Configuración de MySQL
MYSQL_CONFIG = {
    "host":  os.getenv("DB_HOST"),
    "user":  os.getenv("DB_USER"),
    "password":  os.getenv("DB_PASS"),
    "port": 3306,
    "database": os.getenv("DB_NAME")
}
