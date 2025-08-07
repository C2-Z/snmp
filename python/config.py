import os
from dotenv import load_dotenv

load_dotenv()

COMMUNITY = os.getenv("COMMUNITY")
TARGET_IP = os.getenv("TARGET_IP")
TARGET_PORT = int(os.getenv("TARGET_PORT"))

OIDS = {
    "sysName": "1.3.6.1.2.1.1.5.0",          
    "sysUpTime": "1.3.6.1.2.1.1.3.0",       
    "ifNumber": "1.3.6.1.2.1.2.1.0",         
    "ifAdminStatus_2": "1.3.6.1.2.1.2.2.1.7.2", 
    "ifOperStatus_1": "1.3.6.1.2.1.2.2.1.8.1",   
    "ifInOctets_1": "1.3.6.1.2.1.2.2.1.10.1",    
    "ifOutOctets_1": "1.3.6.1.2.1.2.2.1.16.1",   
    "ifInDiscards_1": "1.3.6.1.2.1.2.2.1.13.1",  
    "ifOutDiscards_1": "1.3.6.1.2.1.2.2.1.19.1", 
    "ifInUcastPkts_1": "1.3.6.1.2.1.2.2.1.11.1", 
    "ifInNUcastPkts_1": "1.3.6.1.2.1.2.2.1.12.1",
    "ifInErrors_1": "1.3.6.1.2.1.2.2.1.14.1"     
}
NUMERIC_COLUMNS = [
    "sysUpTime", "ifNumber", "ifAdminStatus_2", "ifOperStatus_1",
    "ifInOctets_1", "ifOutOctets_1", "ifInDiscards_1", "ifOutDiscards_1",
    "ifInUcastPkts_1", "ifInNUcastPkts_1", "ifInErrors_1"
]

MYSQL_CONFIG = {
    "host":  os.getenv("DB_HOST"),
    "user":  os.getenv("DB_USER"),
    "password":  os.getenv("DB_PASS"),
    "port": 3306,
    "database": os.getenv("DB_NAME")
}
