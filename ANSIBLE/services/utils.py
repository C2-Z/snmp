# services/utils.py
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='extract.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
extract_logger = logging.getLogger('extract')
classify_logger = logging.getLogger('classify')
classify_handler = logging.FileHandler('classify_ansible.log')
classify_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
classify_logger.addHandler(classify_handler)
classify_logger.setLevel(logging.INFO)

STATE_FILE = 'mitigation_state.json'
COUNTERS_FILE = 'interface_counters.json'

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
