#!/usr/bin/env python3
"""
Generador de datos en tiempo real para el sistema LoRaMesh
"""

import datetime
import time
import threading
import logging
from typing import List, Tuple, Dict
from .database_manager import DatabaseManager
from .data_generator import DataGenerator
from .config import NODE_ID_LOCATIONS

logger = logging.getLogger(__name__)

class RealtimeDataGenerator:
    """Generador de datos en tiempo real para sensores IoT que respeta el refresh_rate individual de cada nodo"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.data_generator = DataGenerator()
        self.running = False
        self.node_threads = {}
        self.total_records = 0
        self.records_lock = threading.Lock()  # Lock para proteger el contador
    
    def get_node_location(self, node_id: int) -> Tuple[float, float]:
        """Obtiene la ubicación de un nodo por su ID"""
        return NODE_ID_LOCATIONS.get(node_id, (0.0, 0.0))
    
    def generate_node_data(self, node_id: int, model: str, refresh_rate: int, sensors: List):
        """Genera datos para un nodo específico respetando su refresh_rate"""
        logger.info(f"Iniciando generación para nodo {node_id} ({model}) - Intervalo: {refresh_rate} minutos")
        
        # Crear conexión independiente para este thread
        node_db_manager = DatabaseManager(self.db_manager.config)
        if not node_db_manager.connect():
            logger.error(f"No se pudo conectar a la base de datos para el nodo {node_id}")
            return
        
        try:
            while self.running:
                try:
                    current_timestamp = datetime.datetime.now()
                    lat, lon = self.get_node_location(node_id)
                    batch = []
                    
                    # Generar datos para todos los sensores del nodo
                    for sensor_type_id, sensor_name in sensors:
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
                        node_db_manager.insert_measurements_batch(batch)
                        with self.records_lock:
                            self.total_records += len(batch)
                        logger.info(f"Nodo {node_id} ({model}) - Ubicación: ({lat}, {lon}) - {len(batch)} mediciones enviadas - Total: {self.total_records}")
                    
                    # Esperar el tiempo de refresh específico del nodo (en minutos)
                    time.sleep(refresh_rate * 60)
                    
                except Exception as e:
                    logger.error(f"Error generando datos para nodo {node_id}: {e}")
                    time.sleep(60)  # Esperar 1 minuto antes de reintentar
        finally:
            node_db_manager.disconnect()
            logger.info(f"Conexión cerrada para nodo {node_id}")
    
    def start_continuous_generation(self):
        """Inicia la generación continua de datos para todos los nodos activos"""
        # Configurar datos iniciales usando la conexión principal
        if not self.db_manager.connect():
            logger.error("No se pudo conectar a la base de datos")
            return
        
        try:
            self.db_manager.setup_initial_data()
            nodes, sensors = self.db_manager.get_active_nodes_and_sensors()
        finally:
            # Cerrar la conexión principal después de obtener los datos iniciales
            self.db_manager.disconnect()
        
        if not nodes or not sensors:
            logger.warning("No hay nodos activos o sensores disponibles")
            return
        
        logger.info(f"Iniciando generación continua para {len(nodes)} nodos activos")
        logger.info("Cada nodo respetará su refresh_rate individual configurado")
        
        self.running = True
        
        # Crear thread para cada nodo
        for node_id, model, refresh_rate in nodes:
            thread = threading.Thread(
                target=self.generate_node_data,
                args=(node_id, model, refresh_rate, sensors),
                daemon=True
            )
            thread.start()
            self.node_threads[node_id] = thread
            logger.info(f"Thread iniciado para nodo {node_id} con refresh_rate de {refresh_rate} minutos")
        
        try:
            # Mantener el programa ejecutándose
            while self.running:
                time.sleep(10)  # Verificar cada 10 segundos
        except KeyboardInterrupt:
            logger.info("Generación interrumpida por el usuario")
            self.stop_generation()
    
    def stop_generation(self):
        """Detiene la generación de datos"""
        logger.info("Deteniendo generación de datos...")
        self.running = False
        
        # Esperar a que terminen todos los threads
        for node_id, thread in self.node_threads.items():
            thread.join(timeout=5)
            logger.info(f"Thread del nodo {node_id} terminado")
        
        with self.records_lock:
            total = self.total_records
        logger.info(f"Generación completada - Total de registros: {total}")

    def get_node_data_with_location(self, node_id: int) -> dict:
        """Obtiene datos del nodo incluyendo su ubicación"""
        lat, lon = self.get_node_location(node_id)
        current_timestamp = datetime.datetime.now()
        
        # Generar datos de sensores actuales
        sensors_data = {}
        nodes, sensors = self.db_manager.get_active_nodes_and_sensors()
        
        for sensor_type_id, sensor_name in sensors:
            value = self.data_generator.generate_realistic_value(sensor_name, current_timestamp, node_id)
            sensors_data[sensor_name] = value
        
        return {
            'node_id': node_id,
            'latitude': lat,
            'longitude': lon,
            'timestamp': current_timestamp.isoformat(),
            'sensors': sensors_data
        }
