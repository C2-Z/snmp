#snmp_client.py
import asyncio
from pysnmp.hlapi.v1arch.asyncio import SnmpDispatcher, CommunityData, UdpTransportTarget, get_cmd, ObjectType, ObjectIdentity
from db_handler import DatabaseService
from config import INTERFACES, INTERFACE_OIDS, SCALAR_OIDS

class SnmpService:
    def __init__(self, community, target_ips, target_port, mysql_config):
        """Inicializa el servicio SNMP y la conexión a la base de datos."""
        self.community = community
        self.target_ips = target_ips
        self.target_port = target_port
        self.interface_oids = INTERFACE_OIDS
        self.scalar_oids = SCALAR_OIDS
        self.db_service = DatabaseService(mysql_config, {**INTERFACE_OIDS, **SCALAR_OIDS})
        self.interfaces = INTERFACES
        self.snmp_dispatcher = SnmpDispatcher()

    async def get_active_interfaces(self, ip):
        """Obtiene la lista de interfaces activas para un switch dado."""
        community_data = CommunityData(self.community)
        transport_target = await UdpTransportTarget.create((ip, self.target_port))

        active_ifaces = []
        for if_index in range(10001, 10023):  # Rango de interés: 10001 a 10022 puertos 1 al 22
            oid = f"1.3.6.1.2.1.2.2.1.8.{if_index}"  # ifOperStatus para cada índice
            error_indication, error_status, error_index, var_binds = await get_cmd(
                self.snmp_dispatcher,
                community_data,
                transport_target,
                ObjectType(ObjectIdentity(oid))
            )

            if not error_indication and not error_status:
                try:
                    status = int(var_binds[0][1])
                    if status == 1:  # 1 = up
                        active_ifaces.append(if_index)
                except (ValueError, IndexError, TypeError):
                    print(f"  Error al procesar estado para {ip}, ifIndex {if_index}")
            else:
                print(f"  Error en {ip} para ifIndex {if_index}: {error_indication or error_status.prettyPrint()}")

        return active_ifaces

    async def get_interface_data(self, ip, if_index):
        """Obtiene datos de una interfaz específica usando OIDs separados."""
        community_data = CommunityData(self.community)
        transport_target = await UdpTransportTarget.create((ip, self.target_port))

        data = {}

        # Consultar OIDs escalares (sin índice)
        if self.scalar_oids:
            object_types = [ObjectType(ObjectIdentity(oid)) for oid in self.scalar_oids.values()]
            error_indication, error_status, error_index, var_binds = await get_cmd(
                self.snmp_dispatcher,
                community_data,
                transport_target,
                *object_types
            )
            if not error_indication and not error_status:
                for var_bind in var_binds:
                    oid = str(var_bind[0])
                    metric = next((k for k, v in self.scalar_oids.items() if str(v) in oid), None)
                    if metric:
                        try:
                            if metric in ["sysName"]:  # Manejar sysName como texto
                                data[oid] = str(var_bind[1]) if var_bind[1] is not None else None
                            else:  # Otros escalares como enteros
                                data[oid] = int(var_bind[1]) if var_bind[1] is not None else None
                        except (ValueError, TypeError):
                            data[oid] = None

        # Consultar OIDs de interfaz (con índice)
        if self.interface_oids:
            object_types = [ObjectType(ObjectIdentity(f"{oid}.{if_index}")) for oid in self.interface_oids.values()]
            error_indication, error_status, error_index, var_binds = await get_cmd(
                self.snmp_dispatcher,
                community_data,
                transport_target,
                *object_types
            )
            if not error_indication and not error_status:
                for var_bind in var_binds:
                    oid = str(var_bind[0])
                    try:
                        data[oid] = int(var_bind[1]) if var_bind[1] is not None else None
                    except (ValueError, TypeError):
                        data[oid] = None

        print(f"  Datos de interfaz {if_index} en {ip}: {data}")
        return data

    async def monitor(self):
        """Monitorea datos SNMP para cada IP y los guarda en la base de datos cada 15 segundos."""
        try:
            while True:
                for target_ip in self.target_ips:
                    try:
                        # Verificar si la IP tiene una interfaz predefinida (solo router)
                        if target_ip in self.interfaces:
                            interface_name, interface_index = self.interfaces[target_ip]
                            print(f"Consultando {target_ip} para interfaz predefinida (ifIndex={interface_index})")

                            # Construir OIDs específicos para la interfaz predefinida
                            oids = {**self.scalar_oids, **self.interface_oids}
                            for name, oid_base in self.interface_oids.items():
                                oids[name] = f"{oid_base}.{interface_index}"

                            transport_target = await UdpTransportTarget.create((target_ip, self.target_port))
                            object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids.values()]
                            error_indication, error_status, error_index, var_binds = await get_cmd(
                                self.snmp_dispatcher,
                                CommunityData(self.community),
                                transport_target,
                                *object_types
                            )

                            if not error_indication and not error_status:
                                data = {str(var_bind[0]): str(var_bind[1]) for var_bind in var_binds}
                                print(f"Datos SNMP obtenidos para {target_ip} (interfaz {interface_index})")
                                self.db_service.insert_snmp_data(target_ip, data, oids, int(interface_index))
                            else:
                                print(f" {target_ip}: Error {error_indication or error_status.prettyPrint()}")

                        # Monitoreo de interfaces activas para switches
                        else:
                            print(f"Analizando switch {target_ip} para interfaces activas...")
                            active_ifaces = await self.get_active_interfaces(target_ip)
                            if not active_ifaces:
                                print(f"  No se encontraron interfaces activas en {target_ip}")
                                continue

                            print(f"  Interfaces activas en {target_ip}: {active_ifaces}")
                            for if_index in active_ifaces:
                                data = await self.get_interface_data(target_ip, if_index)
                                if data:
                                    # Usar oids_base combinado, ya que get_interface_data maneja los índices
                                    oids = {**self.scalar_oids, **self.interface_oids}
                                    self.db_service.insert_snmp_data(target_ip, data, oids, if_index)

                    except Exception as e:
                        print(f"Error en la consulta SNMP para {target_ip}: {e}")

                await asyncio.sleep(15)  # Tiempo de espera entre consultas

        except asyncio.CancelledError:
            print("Monitoreo cancelado.")
        finally:
            self.snmp_dispatcher.close()
            self.db_service.close()