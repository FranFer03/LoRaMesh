#!/usr/bin/env python3
"""
Utilidades para mostrar estadísticas de la base de datos
"""

import logging
from typing import Dict, List, Tuple
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class StatisticsReporter:
    """Generador de reportes y estadísticas de la base de datos"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def display_database_statistics(self):
        """Muestra estadísticas de la base de datos"""
        try:
            tables_stats, sensor_stats = self.db_manager.get_database_statistics()
            
            # Mostrar estadísticas
            print("\n" + "="*60)
            print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
            print("="*60)
            
            print("\n📋 Registros por tabla:")
            for table, count in tables_stats.items():
                print(f"  {table:15} : {count:,}")
            
            print(f"\n📈 Mediciones por tipo de sensor:")
            for name, count, first, last in sensor_stats:
                print(f"  {name:15} : {count:,} mediciones")
                print(f"  {'':15}   Desde: {first}")
                print(f"  {'':15}   Hasta: {last}")
                print()
            
            return tables_stats, sensor_stats
            
        except Exception as e:
            logger.error(f"❌ Error mostrando estadísticas: {e}")
            return {}, []
