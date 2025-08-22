#!/usr/bin/env python3
"""
Configuración y estructuras de datos para el generador de datos sintéticos
"""

from dataclasses import dataclass
from typing import Dict
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
            ),
            'CO2': SensorPattern(
                base_value=400.0,
                variation_range=300.0,
                trend_factor=0.1,  # Incremento gradual
                noise_level=10.0
            ),
            'Light': SensorPattern(
                base_value=1000.0,
                variation_range=800.0,
                seasonal_amplitude=600.0,
                noise_level=50.0
            ),
            'Soil_Moisture': SensorPattern(
                base_value=45.0,
                variation_range=25.0,
                seasonal_amplitude=15.0,
                noise_level=1.0
            )
        }

# Constantes del sistema
DEVICE_MODELS = [
    'ESP32-WROOM-32', 'Arduino-Uno-WiFi', 'Raspberry-Pi-4B',
    'NodeMCU-V3', 'ESP8266-12E', 'STM32-IoT-Node'
]

SENSOR_TYPES_DATA = [
    ('Temperature', 'Sensor de temperatura ambiente', '°C', -40.0, 85.0, 2),
    ('Humidity', 'Sensor de humedad relativa', '%', 0.0, 100.0, 1),
    ('Pressure', 'Sensor de presión atmosférica', 'hPa', 300.0, 1100.0, 2),
    ('CO2', 'Sensor de dióxido de carbono', 'ppm', 0.0, 5000.0, 0),
    ('Light', 'Sensor de intensidad lumínica', 'lux', 0.0, 100000.0, 0),
    ('Soil_Moisture', 'Sensor de humedad del suelo', '%', 0.0, 100.0, 1)
]
