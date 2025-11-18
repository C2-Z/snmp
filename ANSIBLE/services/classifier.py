# services/classifier.py
from autogluon.tabular import TabularPredictor
from services.utils import classify_logger
import pandas as pd

def load_model_autogluon(model_path):
    model = TabularPredictor.load(model_path)
    return model

def classify_data(model, X, data_for_yaml):
    try:
        # 1) Revisar si hay None o NaN en X
        if X.isnull().any().any():
            classify_logger.warning("Primera extracción.")
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
