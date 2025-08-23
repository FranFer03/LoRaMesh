#!/usr/bin/env python3
"""
Interfaz simplificada para el generador de datos sintéticos
Ejecuta directamente la generación sin menú
"""

import logging
from .config import DatabaseConfig, log_file_path
from .database_manager import DatabaseManager
from .realtime_data_generator import RealtimeDataGenerator

logger = logging.getLogger(__name__)

class UserInterface:
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_manager = DatabaseManager(db_config)
        self.realtime_generator = RealtimeDataGenerator(self.db_manager)
    
    def start(self):
        print("Generador de Datos Sinteticos - Remote Area Network")
        print("=" * 60)
        print("Iniciando generación automatica de datos...")
        print("Cada nodo respetará su refresh_rate individual")
        print(f"Errores y warnings se guardan en: {log_file_path}")
        print("Presiona Ctrl+C para detener")
        print("=" * 60)
        
        try:
            logger.info("Iniciando aplicación de generación de datos sintéticos")
            self.realtime_generator.start_continuous_generation()
        except KeyboardInterrupt:
            print("\nPrograma interrumpido por el usuario")
            logger.warning("Programa interrumpido por el usuario")
        except Exception as e:
            logger.error(f"Error en la aplicación: {e}")
            print(f"Error: {e}")
        finally:
            print("\nCerrando aplicación...")
            logger.info("Cerrando aplicación")
            self.realtime_generator.stop_generation()