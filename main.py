from datos_sinteticos.config import DatabaseConfig
from datos_sinteticos.user_interface import UserInterface

def main():
    # Configuración de la base de datos
    db_config = DatabaseConfig(
        host='***',
        database='***',
        user='admin', 
        password='***',
        port=3306
    )
    
    # Iniciar interfaz de usuario
    ui = UserInterface(db_config)
    ui.start()

if __name__ == "__main__":
    main()