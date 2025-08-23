#!/usr/bin/env python3
"""
Configuración y estructuras de datos para el generador de datos sintéticos
"""

from dataclasses import dataclass
from typing import Dict
import logging
import os

# Configuración de logging con archivo para errores y warnings
def setup_logging():
    """Configura el sistema de logging con archivo para errores y warnings"""
    # Crear directorio de logs si no existe
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Archivo para errores y warnings
    error_log_file = os.path.join(log_dir, 'errors_warnings.txt')
    
    # Configurar logger principal
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remover handlers existentes para evitar duplicados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler para consola (todos los niveles)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # Handler para archivo (solo errores y warnings)
    file_handler = logging.FileHandler(error_log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Agregar handlers al logger principal
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return error_log_file

# Configurar logging al importar el módulo
log_file_path = setup_logging()

@dataclass
class DatabaseConfig:
    """Configuración de la base de datos"""
    host: str = 'localhost'
    database: str = 'remote_area_network'
    user: str = 'your_username'
    password: str = 'your_password'
    port: int = 3306

@dataclass
class SensorPattern:
    """Patrón de comportamiento de un sensor"""
    base_value: float
    variation_range: float
    trend_factor: float = 0.0
    seasonal_amplitude: float = 0.0
    noise_level: float = 0.1

class SensorPatterns:
    """Definición de patrones para cada tipo de sensor"""
    
    @staticmethod
    def get_patterns() -> Dict[str, SensorPattern]:
        """Define patrones realistas para cada tipo de sensor"""
        return {
            'Temperature': SensorPattern(
                base_value=22.0,
                variation_range=15.0,
                seasonal_amplitude=8.0,
                noise_level=0.3
            ),
            'Humidity': SensorPattern(
                base_value=60.0,
                variation_range=30.0,
                seasonal_amplitude=10.0,
                noise_level=2.0
            ),
            'Pressure': SensorPattern(
                base_value=1013.25,
                variation_range=50.0,
                seasonal_amplitude=20.0,
                noise_level=1.5
            )
        }

# Constantes del sistema
DEVICE_MODELS = [
    'nodo_plaza_lules', 'nodo_mercado_central_lules', 'nodo_hospital_lules'
]

UBI_DEVICE_MODELS = [
    (-26.922872, -65.337256), (-26.926746, -65.338210), (-26.929212, -65.338553)
]

# Diccionario para mapear nodos con sus ubicaciones
NODE_LOCATIONS = {
    'nodo_plaza_lules': (-26.922872, -65.337256),
    'nodo_mercado_central_lules': (-26.926746, -65.338210),
    'nodo_hospital_lules': (-26.929212, -65.338553)
}

NODE_ID_LOCATIONS = {
    64: (-26.922872, -65.337256),  # nodo_plaza_lules
    65: (-26.926746, -65.338210),  # nodo_mercado_central_lules
    66: (-26.929212, -65.338553)   # nodo_hospital_lules
}

SENSOR_TYPES_DATA = [
    ('Temperature', 'Sensor de temperatura ambiente', '°C', -40.0, 85.0, 2),
    ('Humidity', 'Sensor de humedad relativa', '%', 0.0, 100.0, 1),
    ('Pressure', 'Sensor de presión atmosférica', 'hPa', 300.0, 1100.0, 2),
    ('Latitud', 'Ubicacion del nodo', '°', -90.0, 90.0, 2),
    ('Longitud', 'Ubicacion del nodo', '°', -180.0, 180.0, 2)
]
