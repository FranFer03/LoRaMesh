#!/usr/bin/env python3
"""
Generador de datos en tiempo real para el sistema LoRaMesh
"""

import datetime
import time
import logging
import random
from typing import List, Tuple
from database_manager import DatabaseManager
from data_generator import DataGenerator

logger = logging.getLogger(__name__)

class RealtimeDataGenerator:
    """Generador de datos en tiempo real para sensores IoT"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.data_generator = DataGenerator()
    
    def generate_realtime_data(self, duration_minutes: int = 60, interval_seconds: int = 30):
        """Genera datos en tiempo real por un período determinado"""
        nodes, sensors = self.db_manager.get_active_nodes_and_sensors()
        
        if not nodes or not sensors:
            logger.warning("⚠️ No hay nodos activos o sensores disponibles")
            return
        
        logger.info(f"⏱️ Iniciando generación en tiempo real por {duration_minutes} minutos")
        logger.info(f"🔄 Intervalo: {interval_seconds} segundos")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        record_count = 0
        
        try:
            while time.time() < end_time:
                current_timestamp = datetime.datetime.now()
                batch = []
                
                # Generar medición para cada combinación nodo-sensor
                for node_id, model, refresh_rate in nodes:
                    # Solo algunos sensores por ciclo (simula refresh_rate)
                    if random.random() < 0.7:  # 70% probabilidad de medición
                        sensor_type_id, sensor_name = random.choice(sensors)
                        value = self.data_generator.generate_realistic_value(sensor_name, current_timestamp, node_id)
                        
                        batch.append((
                            node_id,
                            sensor_type_id,
                            value,
                            current_timestamp,
                            current_timestamp
                        ))
                
                # Insertar batch
                if batch:
                    self.db_manager.insert_measurements_batch(batch)
                    record_count += len(batch)
                    logger.info(f"📈 {len(batch)} nuevas mediciones - Total: {record_count}")
                
                # Esperar hasta el próximo intervalo
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("⏹️ Generación en tiempo real interrumpida por el usuario")
        except Exception as e:
            logger.error(f"❌ Error en generación tiempo real: {e}")
        
        logger.info(f"✅ Generación en tiempo real completada: {record_count} registros")
