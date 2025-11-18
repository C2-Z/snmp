# services/mitigation.py
import os
import subprocess
import shutil
import time
from datetime import datetime
from services.utils import classify_logger, load_json_file, save_json_file

STATE_FILE = 'mitigation_state.json'

def load_mitigation_state():
    state = load_json_file(STATE_FILE)
    classify_logger.info(f"Estado de mitigación cargado desde {STATE_FILE}")
    return state

def save_mitigation_state(state):
    save_json_file(STATE_FILE, state)
    classify_logger.info(f"Estado de mitigación guardado en {STATE_FILE}")

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
