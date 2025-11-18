# services/db_handler.py
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import timedelta
from services.utils import extract_logger

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}')

def extraer_bloque_db(last_timestamp):
    """
    Extrae un bloque de filas desde MySQL (usando SQLAlchemy) correspondientes
    al mismo ciclo de timestamp, tolerando ±1 segundo.
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

        # Filtramos por tolerancia ±1 segundo (como en tu versión)
        df = df_nuevos[
            (df_nuevos['timestamp'] >= min_ts - pd.Timedelta(seconds=1)) &
            (df_nuevos['timestamp'] <= min_ts + pd.Timedelta(seconds=1))
        ]

        # Actualizamos last_timestamp
        last_timestamp = df['timestamp'].max()

        return df, last_timestamp

    except Exception as e:
        extract_logger.error(f"Error conectando a MySQL: {e}")
        return None, last_timestamp
