# snmp_client.py

import asyncio
from pysnmp.hlapi.v1arch.asyncio import *
from config import COMMUNITY, TARGET_IP, TARGET_PORT, OIDS

async def snmp_monitor():
    snmp_dispatcher = SnmpDispatcher()
    community_data = CommunityData(COMMUNITY)
    transport_target = await UdpTransportTarget.create((TARGET_IP, TARGET_PORT))

    try:
        while True:
            try:
                # OIDs List
                object_types = [ObjectType(ObjectIdentity(oid)) for oid in OIDS.values()]

                error_indication, error_status, error_index, var_binds = await get_cmd(
                    snmp_dispatcher,
                    community_data,
                    transport_target,
                    *object_types
                )

                if error_indication:
                    print("❌", error_indication)
                elif error_status:
                    print(f" Error {error_status.prettyPrint()} at index {error_index}")
                else:
                    data = {}
                    for var_bind in var_binds:
                        oid = str(var_bind[0])
                        value = str(var_bind[1])
                        data[oid] = value
                    print(data)
            except Exception as e:
                print(f"Error en la consulta SNMP: {e}")

            await asyncio.sleep(5)

    except asyncio.CancelledError:
        print("Monitoreo cancelado.")
    finally:
        snmp_dispatcher.close()
