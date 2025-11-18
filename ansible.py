import pandas as pd
import numpy as np
import yaml
import subprocess
import time
import logging
import joblib
import os
import json
import shutil
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from autogluon.tabular import TabularPredictor
from jinja2 import Environment, FileSystemLoader

load_dotenv()

# Mostrar todas las columnas
pd.set_option('display.max_columns', None)
# Mostrar todas las filas (si quieres)
pd.set_option('display.max_rows', None)
# Opcional: mostrar todo el ancho de cada columna
pd.set_option('display.width', 200)

def render_yaml_template(template_name, context):
    """
    Carga y renderiza una plantilla YAML desde /playbooks/
    """
    template_dir = os.path.join(os.path.dirname(__file__), "playbooks")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(context)


# ====================== CONFIGURACIÓN DE LOGGING ======================
logging.basicConfig(filename='extract.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
extract_logger = logging.getLogger('extract')
classify_logger = logging.getLogger('classify')
classify_handler = logging.FileHandler('classify_ansible.log')
classify_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
classify_logger.addHandler(classify_handler)
classify_logger.setLevel(logging.INFO)

# ====================== ARCHIVOS DE ESTADO ===========================
STATE_FILE = 'mitigation_state.json'
COUNTERS_FILE = 'interface_counters.json'
ROLLBACK_AFTER_MINUTES = 5
COUNTER_MAX = 2**32  # cambia a 2**64 si usas contadores SNMP de 64 bits
# ====================== EJECUTAR PLAYBOOK ============================
def execute_playbook(yaml_path, mitigation_state, is_rollback=False):
    try:
        ansible_bin = shutil.which('ansible-playbook') or 'ansible-playbook'

        result = subprocess.run([
            ansible_bin,
            '-i', 'inventory.yml',
            yaml_path,
            '--timeout', '30'
        ], capture_output=True, text=True)

        filename = os.path.basename(yaml_path)
        print(f"\n--- EJECUTANDO: {filename} ---")
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")

        success = result.returncode == 0 and "failed=0" in result.stdout
        status = 'removed' if is_rollback and success else 'applied' if success else 'failed'

        parts = filename.replace('.yaml', '').split('_')
        host = parts[2] if len(parts) > 2 else parts[1] if len(parts)>1 else 'unknown'
        interface = parts[3] if len(parts) > 3 else None
        key = f"{host}_{interface}" if interface else host

        if is_rollback and success:
            if key in mitigation_state:
                del mitigation_state[key]
                classify_logger.info(f"Rollback exitoso: {key}")
        else:
            mitigation_state[key] = mitigation_state.get(key, {})
            mitigation_state[key].update({
                'interface': interface,
                'last_mitigated': datetime.now().isoformat(),
                'yaml_path': yaml_path,
                'status': status
            })

        classify_logger.info(f"Resultado en {host}: {status}")
        save_mitigation_state(mitigation_state)

    except Exception as e:
        classify_logger.error(f"Error ejecutando {yaml_path}: {str(e)}")

# ====================== MAPEO DE INTERFACES ==========================
INTERFACE_MAP = {
    10001: "FastEthernet0/1",
    10002: "FastEthernet0/2",
    10003: "FastEthernet0/3",
    10004: "FastEthernet0/4",
    10005: "FastEthernet0/5",
    10006: "FastEthernet0/6",
    10007: "FastEthernet0/7",
    10008: "FastEthernet0/8",
    10009: "FastEthernet0/9",
    10010: "FastEthernet0/10",
    10011: "FastEthernet0/11",
    10012: "FastEthernet0/12",
    10013: "FastEthernet0/13",
    10014: "FastEthernet0/14",
    10015: "FastEthernet0/15",
    10016: "FastEthernet0/16",
    10017: "FastEthernet0/17",
    10018: "FastEthernet0/18",
    10019: "FastEthernet0/19",
    10020: "FastEthernet0/20",
    10021: "FastEthernet0/21",
    10022: "FastEthernet0/22"
}

def load_json_file(path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            classify_logger.error(f"Error al leer {path}: {e}")
            return {}
    else:
        with open(path, 'w') as f:
            json.dump({}, f)
        return {}

def save_json_file(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        classify_logger.error(f"Error al guardar {path}: {e}")

def load_mitigation_state():
    state = load_json_file(STATE_FILE)
    classify_logger.info(f"Estado de mitigación cargado desde {STATE_FILE}")
    return state

def save_mitigation_state(state):
    save_json_file(STATE_FILE, state)
    classify_logger.info(f"Estado de mitigación guardado en {STATE_FILE}")

def load_counters_state():
    counters = load_json_file(COUNTERS_FILE)
    classify_logger.info(f"Contadores cargados desde {COUNTERS_FILE}")
    return counters

def save_counters_state(counters):
    save_json_file(COUNTERS_FILE, counters)
    classify_logger.info(f"Contadores guardados en {COUNTERS_FILE}")

def counter_delta(prev, curr, counter_max=COUNTER_MAX):
    if prev is None:
        return None
    prev = float(prev)
    curr = float(curr)
    if curr >= prev:
        return curr - prev
    else:
        # contador reiniciado
        return curr + (counter_max - prev)
    
# ====================== ACTUALIZAR DELTAS ==========================
def update_counters_all(data, counters_state, counter_max=COUNTER_MAX):
    """
    Calcula deltas para todos los contadores numéricos de todos los dispositivos.
    Devuelve un DataFrame solo con las columnas de deltas.
    Además, añade 'delta' (ifInOctets) y 'delta_out' (ifOutOctets) al counters_state.
    """
    delta_data = pd.DataFrame()
    
    for _, row in data.iterrows():
        sysname = row['sysName']
        if pd.isna(sysname):
            continue
        key = f"{sysname.split('.')[0]}_{row['if_name']}"
        if key not in counters_state:
            counters_state[key] = {}

        delta_row = {}
        for col in data.columns:
            if col in ['device_ip', 'if_name', 'sysName', 'timestamp', 'id', 'label']:
                continue
            if pd.isna(row[col]):
                continue
            curr_val = float(row[col])
            prev_val = counters_state[key].get(col)
            delta_val = counter_delta(prev_val, curr_val, counter_max)
            
            # Actualizamos el valor actual siempre
            counters_state[key][col] = curr_val

            # Si no hay valor previo, dejamos vacío en lugar de 0
            delta_row[f"delta_{col}"] = delta_val if prev_val is not None else None

            # === añadir delta y delta_out para ifInOctets / ifOutOctets ===
            if col == 'ifInOctets':
                counters_state[key]['delta'] = delta_val if prev_val is not None else None
            elif col == 'ifOutOctets':
                counters_state[key]['delta_out'] = delta_val if prev_val is not None else None

        # añadir info básica
        delta_row['device_ip'] = row['device_ip']
        delta_row['if_name'] = row['if_name']
        delta_row['sysName'] = row['sysName']
        delta_row['timestamp'] = row['timestamp']
        delta_data = pd.concat([delta_data, pd.DataFrame([delta_row])], ignore_index=True)
    
    # guardar counters_state actualizado
    save_counters_state(counters_state)

    # devolver solo columnas delta + info básica
    delta_cols = [c for c in delta_data.columns if c.startswith('delta_')] + ['device_ip', 'if_name', 'sysName', 'timestamp']
    return delta_data[delta_cols]


# ====================== EXTRACCIÓN DE DATOS =========================

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# Creamos la conexión con SQLAlchemy
engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}')

# ==================== Función de extracción de bloque ====================
def extraer_bloque_db(last_timestamp):
    """
    Extrae un bloque de filas desde MySQL (usando SQLAlchemy) correspondientes
    al mismo ciclo de timestamp, tolerando ±tolerancia_seg segundos.
    """
    try:
        # Convertimos last_timestamp a string compatible con SQL
        if isinstance(last_timestamp, pd.Timestamp):
            last_ts_str = last_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        elif last_timestamp is None:
            last_ts_str = '1970-01-01 00:00:00'
        else:
            last_ts_str = str(last_timestamp)

        # Query para tomar solo filas mayores que last_timestamp
        query = f"""
        SELECT *
        FROM snmp_data_multi
        WHERE timestamp > '{last_ts_str}'
        ORDER BY timestamp ASC
        """

        df_nuevos = pd.read_sql(query, engine)

        if df_nuevos.empty:
            return None, last_timestamp

        # Convertimos timestamp a datetime
        df_nuevos['timestamp'] = pd.to_datetime(df_nuevos['timestamp'])

        # Timestamp mínimo
        min_ts = df_nuevos['timestamp'].min()

        # Filtramos por tolerancia ±tolerancia_seg segundos
        df = df_nuevos[
            (df_nuevos['timestamp'] >= min_ts - pd.Timedelta(seconds=1)) &
            (df_nuevos['timestamp'] <= min_ts + pd.Timedelta(seconds=1))
        ]

        # Actualizamos last_timestamp
        last_timestamp = df['timestamp'].max()

        return df, last_timestamp

    except Exception as e:
        print(f"Error conectando a MySQL: {e}")
        return None, last_timestamp


# ====================== CLASIFICACIÓN ===============================
def classify_data(model, X, data_for_yaml):
    try:
        # 1) Revisar si hay None o NaN en X
        if X.isnull().any().any():
            classify_logger.warning("Datos incompletos (None/NaN). No se realiza la predicción todavía.")
            return None

        # 2) Predicción normal
        y_pred = model.predict(X)
        data_for_yaml['prediction'] = y_pred

        # 3) Mapeo
        label_map = {0: 'Normal', 1: 'TCP SYN FLOOD', 2: 'FTP BRUTE FORCE'}
        data_for_yaml['prediction_label'] = data_for_yaml['prediction'].map(label_map)

        classify_logger.info("Predicciones generadas correctamente")
        return data_for_yaml

    except Exception as e:
        classify_logger.error(f"Error al clasificar datos: {str(e)}")
        return None


# =========================== MAIN ===================================
def main():

    counters_state = {}
    if os.path.exists('interface_counters.json'):
        os.remove('interface_counters.json')
    device_order = ['R1.cisco.local', 'S1.cisco.local', 'S2.cisco.local', 'S3.cisco.local']
    last_timestamp = '2025-11-14 15:43:00'
    
    # model_path = 'model_knn_multi.pkl'
    # if not os.path.exists(model_path):
    #     print(f"Error: El archivo {model_path} no existe en la carpeta actual.")
    #     classify_logger.error(f"El archivo {model_path} no existe")
    #     exit(1)
    
    # knn_model = joblib.load(model_path)
    # print("Modelo KNN cargado desde 'model_knn_multi.pkl'")

    model_path = "ANSIBLE/models_autogluon/20251116_195305_ROUTER" 

    if not os.path.exists(model_path):
        print(f"Error: La carpeta del modelo {model_path} no existe.")
        classify_logger.error(f"La carpeta del modelo {model_path} no existe")
        exit(1)

    model = TabularPredictor.load(model_path)
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
       # muestra las primeras 5 filas
            #print(data.columns.tolist())  # muestra los nombres de las columnas
            #print(data.shape)         # muestra (filas, columnas)
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

            # DEBUG
            # print("\n=== Datos que se pasan al modelo KNN ===")
            # print(X.to_string())

            # === prediccion modelo ===
            print("\n=== Realizando predicción... ===")
            result = classify_data(model, X, delta_data[['timestamp', 'device_ip', 'sysName', 'if_name']].copy())
            print("\n=== Resultados de la clasificación ===")

            if result is None or result.empty:
                print("⚠️ Predicción omitida: (primera lectura).")
            else:
                print(result.to_string())

            
            if result is not None:

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
                            yaml_path = f'temp_play_{device}_{safe_interface}_{int(time.time())}_shutdown.yaml'

                            context = {
                                "device": device,
                                "interface": interface,
                                "host": device.split('.')[0]
                            }

                            yaml_content = render_yaml_template("syn_flood.yml", context)

                            with open(yaml_path, 'w', encoding='utf-8') as f:
                                f.write(yaml_content)

                            print(f"✅ Playbook generado para apagar puerto {interface} en {device}")
                            execute_playbook(yaml_path, mitigation_state)

                ataque_ftp = result[result['prediction'] == 2]

                if not ataque_ftp.empty:

                        print("⚠️ Ataque detectado: FTP BRUTE FORCE")

                        playbook_path = "playbooks/ftp_mitigation.yml"

                        print("➡️ Ejecutando playbook de mitigación FTP...")
                        execute_playbook(playbook_path, mitigation_state)

#                     # mitigación SOLO revisa deltas de salida para S1/S2
#                     switches_objetivo = result[result['sysName'].isin(['S1.cisco.local', 'S2.cisco.local'])].copy()

#                     if switches_objetivo.empty:
#                         print("⚠️ No hay datos de S1 o S2 disponibles. No se puede mitigar.")

#                     else:
#                         deltas_out = []
#                         for _, row in switches_objetivo.iterrows():
#                             key = f"{row['sysName'].split('.')[0]}_{row['if_name']}"
#                             delta_out = counters_state.get(key, {}).get("delta_out")
#                             if delta_out is not None:
#                                 iface = INTERFACE_MAP.get(row['if_name'], row['if_name'])
#                                 deltas_out.append((row['sysName'], iface, delta_out))

#                         if not deltas_out:
#                             print("ℹ️ Primera lectura: no hay datos previos para calcular deltas de salida.")

#                         else:
#                             device, interface, max_delta_out = max(deltas_out, key=lambda x: x[2])
#                             print(f"➡️ Mayor delta de ifOutOctets en {device}, interfaz {interface} (Δ={max_delta_out}).")

#                             safe_interface = str(interface).replace("/", "_")
#                             yaml_path = f'temp_play_{device}_{safe_interface}_{int(time.time())}_shutdown.yaml'

#                             yaml_content = f"""---
# - name: Apagar interfaz {interface} en {device}
#   hosts: {device.split('.')[0]}
#   gather_facts: no
#   connection: network_cli

#   tasks:
#     - name: Apagar interfaz {interface} en {device}
#       ios_config:
#         parents: interface {interface}
#         lines:
#           - shutdown
# """
#                             with open(yaml_path, 'w', encoding='utf-8') as f:
#                                 f.write(yaml_content)

#                             print(f"✅ Playbook generado para apagar puerto {interface} en {device}")
#                             execute_playbook(yaml_path, mitigation_state)
                else:
                    pass
        print("Esperando 15 segundos para la siguiente extracción...")
        time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Monitoreo detenido por el usuario.")