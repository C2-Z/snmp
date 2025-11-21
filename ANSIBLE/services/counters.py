# services/counters.py
import os
import json
import pandas as pd
from services.utils import classify_logger, save_json_file, load_json_file

STATE_FILE = 'mitigation_state.json'
COUNTERS_FILE = 'interface_counters.json'
COUNTER_MAX = 2**32

def load_mitigation_state():
    return load_json_file(STATE_FILE)

def save_mitigation_state(state):
    save_json_file(STATE_FILE, state)

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
        return curr + (counter_max - prev)

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
