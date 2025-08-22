#!/usr/bin/env python3
"""
Gestor de conexión y operaciones de base de datos
"""

import mysql.connector
from mysql.connector import Error
import logging
import random
from typing import List, Tuple, Dict
from config import DatabaseConfig, DEVICE_MODELS, SENSOR_TYPES_DATA

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor de conexión y operaciones básicas de base de datos"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
    
    def connect(self) -> bool:
        """Conecta a la base de datos"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.host,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                port=self.config.port
            )
            logger.info("✅ Conexión a la base de datos exitosa")
            return True
        except Error as e:
            logger.error(f"❌ Error conectando a MySQL: {e}")
            return False
    
    def disconnect(self):
        """Desconecta de la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("🔌 Desconectado de la base de datos")
    
    def setup_initial_data(self):
        """Configura datos iniciales (nodos y tipos de sensores)"""
        try:
            cursor = self.connection.cursor()
            
            # Insertar tipos de sensores si no existen
            sensor_types_query = """
            INSERT IGNORE INTO sensor_types 
            (name, description, unit_of_measure, min_value, max_value, precision_digits) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(sensor_types_query, SENSOR_TYPES_DATA)
            
            # Insertar nodos de dispositivos si no existen
            devices_query = """
            INSERT IGNORE INTO device_nodes 
            (model, refresh_rate, status) 
            VALUES (%s, %s, %s)
            """
            
            device_data = [
                (model, random.randint(30, 300), random.choice(['active', 'active', 'active', 'inactive']))
                for model in DEVICE_MODELS
            ]
            
            cursor.executemany(devices_query, device_data)
            self.connection.commit()
            
            logger.info(f"✅ Configuración inicial completada: {len(SENSOR_TYPES_DATA)} tipos de sensores, {len(device_data)} dispositivos")
            
        except Error as e:
            logger.error(f"❌ Error en configuración inicial: {e}")
            self.connection.rollback()
        finally:
            cursor.close()
    
    def get_active_nodes_and_sensors(self) -> Tuple[List, List]:
        """Obtiene nodos activos y tipos de sensores disponibles"""
        try:
            cursor = self.connection.cursor()
            
            # Obtener nodos activos
            cursor.execute("SELECT node_id, model, refresh_rate FROM device_nodes WHERE status = 'active'")
            nodes = cursor.fetchall()
            
            # Obtener tipos de sensores
            cursor.execute("SELECT sensor_type_id, name FROM sensor_types WHERE is_active = TRUE")
            sensors = cursor.fetchall()
            
            cursor.close()
            return nodes, sensors
            
        except Error as e:
            logger.error(f"❌ Error obteniendo datos: {e}")
            return [], []
    
    def insert_measurements_batch(self, measurements_batch: List[Tuple]):
        """Inserta un lote de mediciones"""
        try:
            cursor = self.connection.cursor()
            insert_query = """
            INSERT INTO measurements 
            (node_id, sensor_type_id, value, timestamp, created_at) 
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, measurements_batch)
            self.connection.commit()
            cursor.close()
        except Error as e:
            logger.error(f"❌ Error insertando mediciones: {e}")
            self.connection.rollback()
            raise
    
    def get_database_statistics(self) -> Tuple[Dict, List]:
        """Obtiene estadísticas de la base de datos"""
        try:
            cursor = self.connection.cursor()
            
            # Contar registros por tabla
            tables_stats = {}
            for table in ['device_nodes', 'sensor_types', 'measurements']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_stats[table] = count
            
            # Estadísticas de mediciones por sensor
            cursor.execute("""
                SELECT st.name, COUNT(*) as count, 
                       MIN(m.timestamp) as first_measurement,
                       MAX(m.timestamp) as last_measurement
                FROM measurements m
                JOIN sensor_types st ON m.sensor_type_id = st.sensor_type_id
                GROUP BY st.sensor_type_id, st.name
                ORDER BY count DESC
            """)
            sensor_stats = cursor.fetchall()
            
            cursor.close()
            return tables_stats, sensor_stats
            
        except Error as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}, []
