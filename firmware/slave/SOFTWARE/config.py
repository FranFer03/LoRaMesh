"""
Archivo de Configuración - Nodo Esclavo LoRa Mesh
================================================

Este archivo contiene todas las constantes y parámetros de configuración
para el nodo esclavo de la red mesh LoRa. Modifica estos valores según
tu configuración de hardware y sensores conectados.

Autores: Francisco Fernández & Nahuel Ontivero
Universidad: UTN - Facultad Regional Tucumán
"""

# ================================================================
# CONFIGURACIÓN DE NODO E IDENTIFICACIÓN
# ================================================================

NODE_ID = "C"  # ID único del nodo esclavo en la red mesh (cambiar para cada nodo)

# ================================================================
# CONFIGURACIÓN DEL PROTOCOLO LORA
# ================================================================

# Umbral de calidad de señal (RSSI) para considerar un nodo como vecino
# Valores típicos: -60 (señal fuerte) a -120 (señal débil)
LORA_QOS = -90  

# ================================================================
# CONFIGURACIÓN DE PINES GPIO (ESP32)
# ================================================================

# Pines para comunicación SPI con módulo LoRa
SPI_SCK_PIN = 5     # Pin de reloj SPI (Serial Clock)
SPI_MOSI_PIN = 27   # Pin de datos Master Out Slave In
SPI_MISO_PIN = 19   # Pin de datos Master In Slave Out

# Pines específicos del módulo LoRa
LORA_CS_PIN = 18    # Pin Chip Select (CS/NSS)
LORA_RST_PIN = 14   # Pin de Reset del módulo
LORA_DIO0_PIN = 26  # Pin de interrupción DIO0

# ================================================================
# CONFIGURACIÓN DE SENSORES
# ================================================================

# Pin para sensor de temperatura DS18B20
DS18B20_PIN = 12    # Pin de datos del sensor de temperatura

# Configuración del módulo GPS
GPS_UART_ID = 2     # ID del puerto UART para GPS
GPS_BAUDRATE = 9600 # Velocidad de comunicación del GPS
GPS_RX_PIN = 16     # Pin RX para recepción de datos GPS
GPS_TIMEZONE = -3   # Zona horaria (UTC-3 para Argentina)

# ================================================================
# CONFIGURACIÓN DE TEMPORIZADORES
# ================================================================

# IDs de temporizadores disponibles en ESP32 (0-3)
TIMER_ID_DSR = 0        # Temporizador para operaciones DSR
TIMER_ID_SENSORS = 1    # Temporizador para lecturas de sensores
TIMER_ID_GPS = 2        # Temporizador para procesamiento GPS

# Intervalo para lecturas de sensores (en segundos)
SENSOR_READ_INTERVAL = 30

# ================================================================
# CONFIGURACIÓN AVANZADA DEL PROTOCOLO DSR
# ================================================================

# Tiempo máximo de espera para respuestas (en segundos)
DSR_TIMEOUT = 62

# Intervalo entre reintentos de envío (en segundos)  
DSR_RETRY_INTERVAL = 30

# Número máximo de intentos de reenvío
DSR_MAX_ATTEMPTS = 2

# Tiempo de vida de entradas en caché (en segundos)
DSR_CACHE_TIMEOUT = 180

# ================================================================
# CONFIGURACIÓN DE DATOS DE SENSORES
# ================================================================

# Precisión decimal para coordenadas GPS
GPS_DECIMAL_PRECISION = 6

# Rango de temperaturas esperadas (para validación)
TEMP_MIN_RANGE = -40.0  # Temperatura mínima esperada (°C)
TEMP_MAX_RANGE = 85.0   # Temperatura máxima esperada (°C)

# Formato de datos de sensores para transmisión
SENSOR_DATA_FORMAT = "temp:{temp:.1f},gps_lat:{lat},gps_lon:{lon}"
