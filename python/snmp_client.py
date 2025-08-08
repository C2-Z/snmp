# snmp_service.py
import asyncio
from pysnmp.hlapi.v1arch.asyncio import *
from db_handler import DatabaseService

class SnmpService:
    def __init__(self, community, target_ips, target_port, oids, mysql_config):
        """Inicializa el servicio SNMP y la conexión a la base de datos."""
        self.community = community
        self.target_ips = target_ips
        self.target_port = target_port
        self.oids = oids
        self.db_service = DatabaseService(mysql_config, oids)

    async def monitor(self):
        """Monitorea datos SNMP para cada IP y los guarda en la base de datos cada 5 segundos."""
        snmp_dispatcher = SnmpDispatcher()
        community_data = CommunityData(self.community)

        try:
            while True:
                for target_ip in self.target_ips:  
                    try:
                        transport_target = await UdpTransportTarget.create((target_ip, self.target_port))
                        object_types = [ObjectType(ObjectIdentity(oid)) for oid in self.oids.values()]
                        error_indication, error_status, error_index, var_binds = await get_cmd(
                            snmp_dispatcher,
                            community_data,
                            transport_target,
                            *object_types
                        )

                        if error_indication:
                            print(f"❌ {target_ip}: {error_indication}")
                        elif error_status:
                            print(f"{target_ip}: Error {error_status.prettyPrint()} at index {error_index}")
                        else:
                            data = {}
                            for var_bind in var_binds:
                                oid = str(var_bind[0])
                                value = str(var_bind[1])
                                data[oid] = value
                            print(f"Datos SNMP obtenidos para {target_ip}")
                            self.db_service.insert_snmp_data(target_ip, data)
                    except Exception as e:
                        print(f"Error en la consulta SNMP para {target_ip}: {e}")

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            print("Monitoreo cancelado.")
        finally:
            snmp_dispatcher.close()
            self.db_service.close()