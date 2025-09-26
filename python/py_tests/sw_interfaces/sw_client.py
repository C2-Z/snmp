# switch_client.py
import asyncio
from pysnmp.hlapi.v1arch.asyncio import SnmpDispatcher, CommunityData, UdpTransportTarget, get_cmd, ObjectType, ObjectIdentity
from sw_config import COMMUNITY, SWITCH_IPS, TARGET_PORT, OIDS_SWITCH

class SwitchService:
    def __init__(self, community, switch_ips, target_port):
        """Inicializa el servicio para monitoreo de switches."""
        self.community = community
        self.switch_ips = switch_ips
        self.target_port = target_port
        self.target_if_range = range(10001, 10023)  # Rango de interés: 10001 a 10022
        self.snmp_dispatcher = SnmpDispatcher()  # Inicializamos el dispatcher aquí

    async def get_active_interfaces(self, ip):
        """Obtiene la lista de interfaces activas para un switch dado usando get_cmd."""
        community_data = CommunityData(self.community)
        transport_target = await UdpTransportTarget.create((ip, self.target_port))

        active_ifaces = []
        for if_index in self.target_if_range:
            oid = f"{OIDS_SWITCH['ifOperStatus']}.{if_index}"
            error_indication, error_status, error_index, var_binds = await get_cmd(
                self.snmp_dispatcher,
                community_data,
                transport_target,
                ObjectType(ObjectIdentity(oid))  # Único varBind
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
        """Obtiene datos de una interfaz específica."""
        community_data = CommunityData(self.community)
        transport_target = await UdpTransportTarget.create((ip, self.target_port))

        data = {}
        for metric, oid_base in OIDS_SWITCH.items():
            if metric not in ["ifNumber", "ifOperStatus"]:
                oid = f"{oid_base}.{if_index}"
                error_indication, error_status, error_index, var_binds = await get_cmd(
                    self.snmp_dispatcher,
                    community_data,
                    transport_target,
                    ObjectType(ObjectIdentity(oid))  # Único varBind
                )
                if not error_indication and not error_status:
                    try:
                        data[metric] = int(var_binds[0][1])
                    except (ValueError, IndexError, TypeError):
                        data[metric] = None
                else:
                    print(f"  Error en {ip} para {metric}.{if_index}: {error_indication or error_status.prettyPrint()}")

        return data

    async def monitor_switches(self):
        """Monitorea las interfaces activas de los switches."""
        for ip in self.switch_ips:
            print(f"Analizando switch {ip}...")
            active_ifaces = await self.get_active_interfaces(ip)
            if not active_ifaces:
                print(f"  No se encontraron interfaces activas en {ip}")
                continue

            print(f"  Interfaces activas en {ip}: {active_ifaces}")
            for if_index in active_ifaces:
                data = await self.get_interface_data(ip, if_index)
                if data:
                    print(f"  Datos de interfaz {if_index} en {ip}: {data}")

    async def close(self):
        """Cierra el dispatcher SNMP."""
        self.snmp_dispatcher.close()

async def main():
    switch_service = SwitchService(COMMUNITY, SWITCH_IPS, TARGET_PORT)
    try:
        await switch_service.monitor_switches()
    finally:
        await switch_service.close()

if __name__ == "__main__":
    asyncio.run(main())