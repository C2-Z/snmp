import asyncio
from pysnmp.hlapi.v1arch.asyncio import *

async def run():
    snmp_dispatcher = SnmpDispatcher()
    community_data = CommunityData('public')
    transport_target = await UdpTransportTarget.create(('127.0.0.1', 161))

    try:
        while True:
            try:
                error_indication, error_status, error_index, var_binds = await get_cmd(
                    snmp_dispatcher,
                    community_data,
                    transport_target,
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),  # sysDescr
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.1.3.0')),  # sysUpTime
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.1.0')),  
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.7.0')),  #ifAdminStatus
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.2.2.1.8.0')) #ifOperStatus
                )

                if error_indication:
                    print("❌", error_indication)
                elif error_status:
                    print(f"⚠️ Error {error_status.prettyPrint()} at index {error_index}")
                else:
                    for var_bind in var_binds:
                        print(f"{var_bind[0]} = {var_bind[1]}")
            except Exception as e:
                print(f"Error en la consulta SNMP: {e}")

            await asyncio.sleep(5)

    except asyncio.CancelledError:
        print("🛑 Monitoreo cancelado.")
    finally:
        snmp_dispatcher.close()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n✅ Finalizado por el usuario.")
