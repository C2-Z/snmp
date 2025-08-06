# main.py

import asyncio
from snmp_client import snmp_monitor

if __name__ == "__main__":
    try:
        asyncio.run(snmp_monitor())
    except KeyboardInterrupt:
        print("\n✅ Finalizado por el usuario.")
