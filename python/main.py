#main.py
import asyncio
from snmp_client import SnmpService
from config import *

if __name__ == "__main__":
    try:
        snmp_service = SnmpService(COMMUNITY, TARGET_IPS, TARGET_PORT, MYSQL_CONFIG)
        asyncio.run(snmp_service.monitor())
    except KeyboardInterrupt:
        print("\nFinalizado por el usuario.")