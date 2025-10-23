import pandas as pd
import numpy as np
import yaml
import subprocess
import time
import logging
import joblib
import os
from datetime import datetime

# Configurar logging
logging.basicConfig(filename='extract.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
extract_logger = logging.getLogger('extract')
classify_logger = logging.getLogger('classify')
classify_handler = logging.FileHandler('classify_ansible.log')
classify_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
classify_logger.addHandler(classify_handler)
classify_logger.setLevel(logging.INFO)

def extraer_datos_csv(last_timestamp, file_path='snmp_data.csv'):
    """
    Extrae datos 'nuevos' desde el archivo snmp_data.csv, filtrando por timestamp > last_timestamp.
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            extract_logger.error(f"El archivo {file_path} no existe")
            return None
        
        # Cargar datos
        data = pd.read_csv(file_path)
        
        # Convertir timestamp a datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # Filtrar datos con timestamp > last_timestamp
        if isinstance(last_timestamp, str):
            last_timestamp = pd.to_datetime(last_timestamp)
        data = data[data['timestamp'] > last_timestamp]
        
        if data.empty:
            extract_logger.info("No se encontraron datos nuevos en snmp_data.csv")
            return None
        
        extract_logger.info("Datos extraídos correctamente desde snmp_data.csv")
        return data
    except Exception as e:
        extract_logger.error(f"Error al extraer datos de snmp_data.csv: {str(e)}")
        return None

def classify_data(model, X, data_for_yaml):
    try:
        data_for_yaml['knn_prediction'] = model.predict(X)
        label_map = {0: 'Normal', 1: 'Malicioso'}
        data_for_yaml['knn_prediction'] = data_for_yaml['knn_prediction'].map(label_map)
        classify_logger.info("Predicciones generadas con el modelo KNN")
        return data_for_yaml
    except Exception as e:
        classify_logger.error(f"Error al clasificar datos: {str(e)}")
        return None

def generate_ansible_yaml(data):
    """
    Genera YAML para mitigar ataques en dispositivos con label=1 (atacados).
    """
    try:
        malicioso = data[data['knn_prediction'] == 'Malicioso']
        if malicioso.empty:
            classify_logger.info("No se detectaron dispositivos atacados. No se genera YAML.")
            return None
        
        timestamps = malicioso['timestamp'].unique()
        yaml_configs = []
        for ts in timestamps:
            malicioso_ts = malicioso[malicioso['timestamp'] == ts]
            tasks = []
            for _, row in malicioso_ts.iterrows():
                ip = row['device_ip']
                interface = row['if_name']
                sysName = row['sysName']
                tasks.append({
                    'name': f'Mitigar ataque en interface {interface} de {sysName} ({ip})',
                    'ios_config': {
                        'lines': [
                            f'interface {interface}',
                            'ip verify unicast source reachable-via rx',
                            'rate-limit input 1000000 187500 375000 conform-action transmit exceed-action drop'
                        ]
                    }
                })
            yaml_config = {
                'hosts': 'routers',
                'gather_facts': False,
                'tasks': tasks
            }
            yaml_configs.append(yaml_config)
        
        yaml_path = f'ansible_config_{int(time.time())}.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_configs, f, default_flow_style=False)
        classify_logger.info(f"YAML generado en {yaml_path}")
        return yaml_path
    except Exception as e:
        classify_logger.error(f"Error al generar YAML: {str(e)}")
        return None

def execute_ansible(yaml_path):
    try:
        result = subprocess.run([
            '/mnt/c/Users/Samir David Mercado/PF/SNMP/snmp_env/bin/ansible-playbook',
            '-i', 'inventory.yml',
            yaml_path
        ], capture_output=True, text=True)
        classify_logger.info(f"Ansible ejecutado. Salida: {result.stdout}")
        print(f"Ansible ejecutado. Salida:\n{result.stdout}")
        if result.stderr:
            classify_logger.error(f"Error en Ansible: {result.stderr}")
            print(f"Error en Ansible: {result.stderr}")
    except FileNotFoundError as e:
        classify_logger.error(f"Error: No se encontró el comando ansible-playbook: {str(e)}")
        print(f"Error: No se encontró el comando ansible-playbook: {str(e)}")
    except Exception as e:
        classify_logger.error(f"Error al ejecutar Ansible: {str(e)}")
        print(f"Error al ejecutar Ansible: {str(e)}")

def main():
    # Orden de los equipos
    device_order = ['R1.cisco.local', 'S1.cisco.local', 'S2.cisco.local', 'S3.cisco.local']
    
    # Configurar last_timestamp inicial
    last_timestamp = '2025-09-24 14:45:40'  # Ajusta según tu base de datos
    
    # Cargar el modelo KNN preentrenado
    model_path = 'model_knn.pkl'
    if not os.path.exists(model_path):
        print(f"Error: El archivo {model_path} no existe en la carpeta actual.")
        classify_logger.error(f"El archivo {model_path} no existe")
        exit(1)
    
    knn_model = joblib.load(model_path)
    classify_logger.info("Modelo KNN cargado desde 'model_knn.pkl'")
    print("✅ Modelo KNN cargado desde 'model_knn.pkl'")
    
    while True:
        # Extraer datos desde CSV
        data = extraer_datos_csv(last_timestamp, file_path='snmp_data.csv')
        
        if data is not None and not data.empty:
            # Forzar if_name a int si existe
            if 'if_name' in data.columns:
                data['if_name'] = data['if_name'].fillna(0).astype(int)
            # Filtrar por el timestamp más antiguo
            min_timestamp = data['timestamp'].min()
            data = data[data['timestamp'] == min_timestamp]
            # Ordenar por sysName
            data['sysName'] = pd.Categorical(data['sysName'], categories=device_order, ordered=True)
            data = data.sort_values('sysName')
            # Guardar en CSV
            data.to_csv('extracted_snmp_data.csv', index=False)
            extract_logger.info("Datos extraídos y guardados en 'extracted_snmp_data.csv'")
            print("Datos extraídos y guardados en 'extracted_snmp_data.csv':")
            print(data)
            print(f"Columnas extraídas: {list(data.columns)}")
            print(f"Total de filas: {len(data)}")
            
            # Actualizar last_timestamp
            last_timestamp = min_timestamp
            print(f"Nuevo last_timestamp para monitoreo continuo: {last_timestamp}")
            
            # Preparar datos para clasificación
            required_yaml_columns = ['device_ip', 'if_name', 'sysName', 'timestamp']
            missing_yaml_columns = [col for col in required_yaml_columns if col not in data.columns]
            if missing_yaml_columns:
                print(f"Error: Faltan columnas necesarias para YAML: {missing_yaml_columns}")
                classify_logger.error(f"Faltan columnas necesarias para YAML: {missing_yaml_columns}")
                continue
            data_for_yaml = data[required_yaml_columns].copy()
            
            # Seleccionar columnas numéricas para predicción (excluir columnas no numéricas)
            exclude_columns = ['device_ip', 'if_name', 'sysName', 'timestamp', 'id', 'label']
            feature_columns = [col for col in data.columns if col not in exclude_columns]
            if not feature_columns:
                print("Error: No se encontraron columnas numéricas para la predicción.")
                classify_logger.error("No se encontraron columnas numéricas para la predicción")
                continue
            classify_logger.info(f"Columnas usadas para predicción: {feature_columns}")
            X = data[feature_columns].copy()
            
            # Verificar valores nulos
            if X.isnull().any().any():
                null_columns = X.columns[X.isnull().any()].tolist()
                print(f"Advertencia: Valores nulos en columnas: {null_columns}. Eliminando filas...")
                classify_logger.warning(f"Valores nulos en columnas: {null_columns}")
                X = X.dropna()
                data_for_yaml = data_for_yaml.loc[X.index]
                if X.empty:
                    print("Error: El DataFrame está vacío después de eliminar nulos.")
                    classify_logger.error("El DataFrame está vacío después de eliminar nulos")
                    continue
            
            # Clasificar con el modelo KNN
            result = classify_data(knn_model, X, data_for_yaml)
            
            if result is not None:
                # Guardar resultados
                output_path = 'classified_traffic.csv'
                result.to_csv(output_path, index=False)
                print(f"\nClasificaciones guardadas en '{output_path}'")
                print(f"Columnas: {list(result.columns)}")
                print(f"Filas: {len(result)}")
                print(f"\nPrimeras filas de los datos clasificados:")
                print(result.head())
                print(f"\nDistribución de predicciones:")
                print(result['knn_prediction'].value_counts())
                
                # Generar y ejecutar YAML si hay dispositivos atacados
                yaml_path = generate_ansible_yaml(result)
                if yaml_path:
                    execute_ansible(yaml_path)
            else:
                print("Error al clasificar. Revisa 'classify_ansible.log'.")
        else:
            print("No se encontraron datos nuevos o error al extraer. Revisa 'extract.log'.")
        
        # Esperar 15 segundos
        extract_logger.info("Esperando 15 segundos para la siguiente extracción...")
        print("Esperando 15 segundos para la siguiente extracción...")
        time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Monitoreo detenido por el usuario.")
        extract_logger.info("Monitoreo detenido por el usuario.")
        classify_logger.info("Monitoreo detenido por el usuario.")

