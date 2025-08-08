# main.py
import asyncio
from snmp_client import SnmpService
from config import COMMUNITY, TARGET_IPS, TARGET_PORT, OIDS, MYSQL_CONFIG

if __name__ == "__main__":
    try:
        snmp_service = SnmpService(COMMUNITY, TARGET_IPS, TARGET_PORT, OIDS, MYSQL_CONFIG)
        asyncio.run(snmp_service.monitor())
    except KeyboardInterrupt:
        print("\n✅ Finalizado por el usuario.")