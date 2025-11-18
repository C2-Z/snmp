# main.py
import os
import time

import pandas as pd

# Import servicios
from services.utils import extract_logger, classify_logger, load_json_file, save_json_file, INTERFACE_MAP
from services.db_handler import extraer_bloque_db
from services.counters import load_counters_state, save_counters_state, update_counters_all
from services.classifier import classify_data, load_model_autogluon
from services.mitigation import execute_playbook, load_mitigation_state, save_mitigation_state

# Mostrar todas las columnas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 200)

def main():

    counters_state = {}
    if os.path.exists('interface_counters.json'):
        os.remove('interface_counters.json')
    device_order = ['R1.cisco.local', 'S1.cisco.local', 'S2.cisco.local', 'S3.cisco.local']
    last_timestamp = '2025-10-01 17:05:21'
    
    model_path = "models_autogluon/20251116_195305_ROUTER" 

    if not os.path.exists(model_path):
        print(f"Error: La carpeta del modelo {model_path} no existe.")
        classify_logger.error(f"La carpeta del modelo {model_path} no existe")
        exit(1)

    model = load_model_autogluon(model_path)
    print(f"Modelo AutoGluon cargado desde '{model_path}'")
    classify_logger.info(f"Modelo AutoGluon cargado desde '{model_path}'")

    classify_logger.info("Modelo cargado desde Autogluon")
    
    mitigation_state = load_mitigation_state()
    counters_state = load_counters_state()

    while True:
        # extraer datos
        data, last_timestamp = extraer_bloque_db(last_timestamp)
        if data is not None:
            print("=== Datos extraídos ===")
            print(data[['timestamp', 'device_ip', 'sysName', 'if_name', 'label']].to_string())
        else:
            print("No se extrajo ningún dato")
        if data is not None and not data.empty:
            data['if_name'] = data['if_name'].fillna(0).astype(int)
            data['sysName'] = pd.Categorical(data['sysName'], categories=device_order, ordered=True)
            data = data.sort_values('sysName')

            # === actualizar deltas para toda la red ===
            delta_data = update_counters_all(data, counters_state)

            # elegir columnas para el modelo
            feature_columns = [col for col in delta_data.columns if col.startswith('delta_')]
            X = delta_data[feature_columns].copy()

            # === prediccion modelo ===
            print("\n=== Realizando predicción... ===")
            result = classify_data(model, X, delta_data[['timestamp', 'device_ip', 'sysName', 'if_name']].copy())
            print("\n=== Resultados de la clasificación ===")

            if result is None or result.empty:
                print("⚠️ Predicción omitida: datos incompletos (primera lectura sin deltas).")
            else:
                print(result.to_string())

            if result is not None:
                # === detección solo si label = 1 (TCP SYN FLOOD) ===
                ataque_tcp_syn = result[result['prediction'] == 1]

                if not ataque_tcp_syn.empty:
                    print("⚠️ Ataque detectado: TCP SYN FLOOD")

                    # mitigación SOLO revisa deltas de S1 y S2 (siempre)
                    switches_objetivo = result[result['sysName'].isin(['S1.cisco.local', 'S2.cisco.local'])].copy()

                    if switches_objetivo.empty:
                        print("⚠️ No hay datos de S1 o S2 disponibles. No se puede mitigar.")
                    else:
                        deltas = []
                        for _, row in switches_objetivo.iterrows():
                            key = f"{row['sysName'].split('.')[0]}_{row['if_name']}"
                            delta = counters_state.get(key, {}).get("delta")
                            if delta is not None:
                                deltas.append((row['sysName'], INTERFACE_MAP.get(row['if_name'], row['if_name']), delta))

                        if not deltas:
                            print("ℹ️ Sin deltas previos aún en S1/S2.")
                        else:
                            device, interface, max_delta = max(deltas, key=lambda x: x[2])
                            print(f"➡️ Mayor delta detectado en {device}, interfaz {interface} (Δ={max_delta}).")

                            safe_interface = str(interface).replace("/", "_")
                            yaml_path = f'temp_playbooks/temp_play_{device}_{safe_interface}_{int(time.time())}_shutdown.yaml'

                            yaml_content = f"""---
- name: Apagar interfaz {interface} en {device}
  hosts: {device.split('.')[0]}
  gather_facts: no
  connection: network_cli

  tasks:
    - name: Apagar interfaz {interface} en {device}
      ios_config:
        parents: interface {interface}
        lines:
          - shutdown
"""
                            with open(yaml_path, 'w', encoding='utf-8') as f:
                                f.write(yaml_content)

                            print(f"✅ Playbook generado para apagar puerto {interface} en {device}")
                            execute_playbook(yaml_path, mitigation_state)

                ataque_ftp = result[result['prediction'] == 2]

                if not ataque_ftp.empty:
                    print("⚠️ Ataque detectado: FTP BRUTE FORCE")

                    # mitigación SOLO revisa deltas de salida para S1/S2
                    switches_objetivo = result[result['sysName'].isin(['S1.cisco.local', 'S2.cisco.local'])].copy()

                    if switches_objetivo.empty:
                        print("⚠️ No hay datos de S1 o S2 disponibles. No se puede mitigar.")

                    else:
                        deltas_out = []
                        for _, row in switches_objetivo.iterrows():
                            key = f"{row['sysName'].split('.')[0]}_{row['if_name']}"
                            delta_out = counters_state.get(key, {}).get("delta_out")
                            if delta_out is not None:
                                iface = INTERFACE_MAP.get(row['if_name'], row['if_name'])
                                deltas_out.append((row['sysName'], iface, delta_out))

                        if not deltas_out:
                            print("ℹ️ Primera lectura: no hay datos previos para calcular deltas de salida.")

                        else:
                            device, interface, max_delta_out = max(deltas_out, key=lambda x: x[2])
                            print(f"➡️ Mayor delta de ifOutOctets en {device}, interfaz {interface} (Δ={max_delta_out}).")

                            safe_interface = str(interface).replace("/", "_")
                            yaml_path = f'temp_playbooks/temp_play_{device}_{safe_interface}_{int(time.time())}_shutdown.yaml'

                            yaml_content = f"""---
- name: Apagar interfaz {interface} en {device}
  hosts: {device.split('.')[0]}
  gather_facts: no
  connection: network_cli

  tasks:
    - name: Apagar interfaz {interface} en {device}
      ios_config:
        parents: interface {interface}
        lines:
          - shutdown
"""
                            with open(yaml_path, 'w', encoding='utf-8') as f:
                                f.write(yaml_content)

                            print(f"✅ Playbook generado para apagar puerto {interface} en {device}")
                            execute_playbook(yaml_path, mitigation_state)

                else:
                    pass
        print("Esperando 15 segundos para la siguiente extracción...")
        time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Monitoreo detenido por el usuario.")
