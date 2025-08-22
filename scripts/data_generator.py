#!/usr/bin/env python3
"""
Generador de valores sintéticos realistas para sensores IoT
"""

import random
import datetime
import numpy as np
from typing import Dict
from config import SensorPattern, SensorPatterns

class DataGenerator:
    """Generador de datos sintéticos para sensores IoT"""
    
    def __init__(self):
        self.sensor_patterns = SensorPatterns.get_patterns()
    
    def generate_realistic_value(self, sensor_name: str, timestamp: datetime.datetime, node_id: int) -> float:
        """Genera un valor realista basado en patrones del sensor"""
        pattern = self.sensor_patterns.get(sensor_name)
        if not pattern:
            return random.uniform(0, 100)
        
        # Componente base
        value = pattern.base_value
        
        # Variación estacional (ciclo diario para temperatura/luz)
        if sensor_name in ['Temperature', 'Light']:
            hour_factor = np.sin((timestamp.hour - 6) * np.pi / 12)  # Pico al mediodía
            value += pattern.seasonal_amplitude * hour_factor
        
        # Variación por humedad (inversa a temperatura)
        if sensor_name == 'Humidity':
            temp_factor = -0.3 * np.sin((timestamp.hour - 6) * np.pi / 12)
            value += pattern.seasonal_amplitude * temp_factor
        
        # Trend temporal (para CO2)
        if pattern.trend_factor != 0:
            days_since_epoch = (timestamp - datetime.datetime(2024, 1, 1)).days
            value += pattern.trend_factor * days_since_epoch
        
        # Variación aleatoria
        variation = random.uniform(-pattern.variation_range/2, pattern.variation_range/2)
        value += variation
        
        # Ruido
        noise = random.gauss(0, pattern.noise_level)
        value += noise
        
        # Variación por nodo (cada nodo tiene características ligeramente diferentes)
        node_offset = (node_id * 17) % 100 / 1000 * pattern.variation_range
        value += node_offset
        
        # Aplicar límites del sensor
        value = self._apply_sensor_limits(sensor_name, value)
        
        return round(value, 2)
    
    def _apply_sensor_limits(self, sensor_name: str, value: float) -> float:
        """Aplica límites específicos por tipo de sensor"""
        limits = {
            'Temperature': (-40, 85),
            'Humidity': (0, 100),
            'Pressure': (300, 1100),
            'CO2': (0, 5000),
            'Light': (0, 100000),
            'Soil_Moisture': (0, 100)
        }
        
        if sensor_name in limits:
            min_val, max_val = limits[sensor_name]
            value = max(min_val, min(max_val, value))
        
        return value
