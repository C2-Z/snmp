#main.py
import asyncio
import threading
from snmp_client import SnmpService
from config import *
from detection.detection import main as detection_main

if __name__ == "__main__":
    try:
        # 1️⃣ Iniciar detection.py en hilo separado (no bloquea asyncio)
        detection_thread = threading.Thread(target=detection_main, daemon=True)
        detection_thread.start()
        print("✅ Sistema de detección iniciado.")

        # 2️⃣ Ejecutar el servicio SNMP original con asyncio
        snmp_service = SnmpService(COMMUNITY, TARGET_IPS, TARGET_PORT, MYSQL_CONFIG)
        asyncio.run(snmp_service.monitor())

        # 3️⃣ Mantener el hilo de detection vivo (aunque asyncio termine)
        detection_thread.join()

    except KeyboardInterrupt:
        print("\nFinalizado por el usuario.")