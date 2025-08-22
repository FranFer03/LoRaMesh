#!/usr/bin/env python3
"""
Interfaz de usuario para el generador de datos sintéticos
"""

import logging
from config import DatabaseConfig
from database_manager import DatabaseManager
from historical_data_generator import HistoricalDataGenerator
from realtime_data_generator import RealtimeDataGenerator
from statistics_reporter import StatisticsReporter

logger = logging.getLogger(__name__)

class UserInterface:
    """Interfaz de línea de comandos para el generador de datos"""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_manager = DatabaseManager(db_config)
        self.historical_generator = HistoricalDataGenerator(self.db_manager)
        self.realtime_generator = RealtimeDataGenerator(self.db_manager)
        self.statistics_reporter = StatisticsReporter(self.db_manager)
    
    def start(self):
        """Inicia la interfaz de usuario"""
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                return
            
            print("🚀 Generador de Datos Sintéticos - Remote Area Network")
            print("=" * 55)
            
            self._main_menu()
            
        except KeyboardInterrupt:
            print("\n⏹️ Programa interrumpido por el usuario")
        finally:
            self.db_manager.disconnect()
    
    def _main_menu(self):
        """Muestra el menú principal y maneja las opciones"""
        while True:
            print("\n📋 OPCIONES:")
            print("1. Configurar datos iniciales (nodos y sensores)")
            print("2. Generar datos históricos")
            print("3. Generar datos en tiempo real")
            print("4. Ver estadísticas de la base de datos")
            print("5. Salir")
            
            choice = input("\n🔸 Selecciona una opción (1-5): ").strip()
            
            if choice == '1':
                self._setup_initial_data()
            elif choice == '2':
                self._generate_historical_data()
            elif choice == '3':
                self._generate_realtime_data()
            elif choice == '4':
                self._show_statistics()
            elif choice == '5':
                print("\n👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Intenta nuevamente.")
    
    def _setup_initial_data(self):
        """Configura datos iniciales"""
        print("\n⚙️ Configurando datos iniciales...")
        self.db_manager.setup_initial_data()
    
    def _generate_historical_data(self):
        """Genera datos históricos con parámetros del usuario"""
        days = input("📅 Días de historia (default 7): ").strip()
        days = int(days) if days.isdigit() else 7
        
        freq = input("⏱️ Mediciones por hora (default 4): ").strip()
        freq = int(freq) if freq.isdigit() else 4
        
        print(f"\n📊 Generando {days} días de datos históricos...")
        self.historical_generator.generate_historical_data(days, freq)
    
    def _generate_realtime_data(self):
        """Genera datos en tiempo real con parámetros del usuario"""
        duration = input("⏱️ Duración en minutos (default 60): ").strip()
        duration = int(duration) if duration.isdigit() else 60
        
        interval = input("🔄 Intervalo en segundos (default 30): ").strip()
        interval = int(interval) if interval.isdigit() else 30
        
        print(f"\n📈 Iniciando generación en tiempo real...")
        self.realtime_generator.generate_realtime_data(duration, interval)
    
    def _show_statistics(self):
        """Muestra estadísticas de la base de datos"""
        print("\n📊 Obteniendo estadísticas...")
        self.statistics_reporter.display_database_statistics()
