# snmp_client.py
import asyncio
from pysnmp.hlapi.v1arch.asyncio import *
from db_handler import DatabaseService
from config import INTERFACES

class SnmpService:
    def __init__(self, community, target_ips, target_port, oids_base, mysql_config):
        """Inicializa el servicio SNMP y la conexión a la base de datos."""
        self.community = community
        self.target_ips = target_ips
        self.target_port = target_port
        self.oids_base = oids_base
        self.db_service = DatabaseService(mysql_config, oids_base)
        self.interfaces = INTERFACES

    async def monitor(self):
        """Monitorea datos SNMP para cada IP y los guarda en la base de datos cada 5 segundos."""
        snmp_dispatcher = SnmpDispatcher()
        community_data = CommunityData(self.community)

        try:
            while True:
                for target_ip in self.target_ips:
                    try:
                        # Verificar si la IP tiene una interfaz definida
                        if target_ip not in self.interfaces:
                            print(f" No se encontró interfaz para {target_ip}")
                            continue
                        interface_name, interface_index = self.interfaces[target_ip]
                        print(f"Consultando {target_ip} para interfaz (ifIndex={interface_index})")

                        # Construir OIDs específicos
                        oids = {}
                        for name, oid_base in self.oids_base.items():
                            if name.startswith('if'):
                                oids[name] = f"{oid_base}.{interface_index}"
                            else:
                                oids[name] = oid_base

                        transport_target = await UdpTransportTarget.create((target_ip, self.target_port))
                        object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids.values()]
                        error_indication, error_status, error_index, var_binds = await get_cmd(
                            snmp_dispatcher,
                            community_data,
                            transport_target,
                            *object_types
                        )

                        if error_indication:
                            print(f" {target_ip}: {error_indication}")
                            continue
                        if error_status:
                            print(f" {target_ip}: Error {error_status.prettyPrint()} at index {error_index}")
                            continue

                        data = {}
                        for var_bind in var_binds:
                            oid = str(var_bind[0])
                            value = str(var_bind[1])
                            data[oid] = value
                        if not data:
                            print(f" No se obtuvieron datos para {target_ip}")
                            continue

                        print(f"Datos SNMP obtenidos para {target_ip}")
                        self.db_service.insert_snmp_data(target_ip, data, oids)

                    except Exception as e:
                        print(f" Error en la consulta SNMP para {target_ip}: {e}")

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            print("Monitoreo cancelado.")
        finally:
            snmp_dispatcher.close()
            self.db_service.close()