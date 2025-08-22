#!/usr/bin/env python3
"""
Generador de Datos Sintéticos para Remote Area Network
Genera datos realistas de sensores IoT para testing y desarrollo

Punto de entrada principal del sistema segmentado
"""

from config import DatabaseConfig
from user_interface import UserInterface

def main():
    """Función principal"""
    # Configuración de la base de datos
    db_config = DatabaseConfig(
        host='localhost',
        database='remote_area_network',
        user='root',  # Cambiar por tu usuario
        password='password',  # Cambiar por tu contraseña
        port=3306
    )
    
    # Iniciar interfaz de usuario
    ui = UserInterface(db_config)
    ui.start()

if __name__ == "__main__":
    main()