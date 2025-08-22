#!/usr/bin/env python3
"""
Generador de datos históricos para el sistema LoRaMesh
"""

import datetime
import logging
import random
from datetime import timedelta
from typing import List, Tuple
from database_manager import DatabaseManager
from data_generator import DataGenerator

logger = logging.getLogger(__name__)

class HistoricalDataGenerator:
    """Generador de datos históricos para sensores IoT"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.data_generator = DataGenerator()
    
    def generate_historical_data(self, days_back: int = 7, measurements_per_hour: int = 4):
        """Genera datos históricos para los últimos N días"""
        nodes, sensors = self.db_manager.get_active_nodes_and_sensors()
        
        if not nodes or not sensors:
            logger.warning("⚠️ No hay nodos activos o sensores disponibles")
            return
        
        logger.info(f"🚀 Generando datos históricos para {len(nodes)} nodos y {len(sensors)} sensores")
        logger.info(f"📅 Período: {days_back} días, {measurements_per_hour} mediciones/hora")
        
        start_time = datetime.datetime.now() - timedelta(days=days_back)
        end_time = datetime.datetime.now()
        
        total_records = 0
        batch_size = 1000
        measurements_batch = []
        
        try:
            # Para cada nodo
            for node_id, model, refresh_rate in nodes:
                logger.info(f"📡 Generando datos para nodo {node_id} ({model})")
                
                # Para cada tipo de sensor (cada nodo tiene todos los tipos de sensores)
                for sensor_type_id, sensor_name in sensors:
                    
                    # Generar timestamps basados en refresh_rate
                    current_time = start_time
                    interval_minutes = max(refresh_rate // 60, 1)  # Mínimo 1 minuto
                    
                    while current_time <= end_time:
                        # Generar valor realista
                        value = self.data_generator.generate_realistic_value(sensor_name, current_time, node_id)
                        
                        # Agregar al batch
                        measurements_batch.append((
                            node_id,
                            sensor_type_id,
                            value,
                            current_time,
                            current_time
                        ))
                        
                        # Insertar batch cuando alcance el tamaño
                        if len(measurements_batch) >= batch_size:
                            self.db_manager.insert_measurements_batch(measurements_batch)
                            total_records += len(measurements_batch)
                            measurements_batch = []
                            
                            if total_records % 10000 == 0:
                                logger.info(f"📊 Insertados {total_records} registros...")
                        
                        # Avanzar al siguiente timestamp
                        current_time += timedelta(minutes=interval_minutes)
                        
                        # Pequeña variación aleatoria en el intervalo (±10%)
                        if random.random() < 0.3:
                            variation = random.randint(-interval_minutes//10, interval_minutes//10)
                            current_time += timedelta(minutes=variation)
            
            # Insertar registros restantes
            if measurements_batch:
                self.db_manager.insert_measurements_batch(measurements_batch)
                total_records += len(measurements_batch)
            
            logger.info(f"✅ Generación completada: {total_records} registros insertados")
            
        except Exception as e:
            logger.error(f"❌ Error generando datos históricos: {e}")
            raise
