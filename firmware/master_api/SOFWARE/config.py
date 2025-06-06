"""
Archivo de Configuración - Red Mesh LoRa
========================================

Este archivo contiene todas las constantes y parámetros de configuración
para el nodo maestro de la red mesh LoRa. Modifica estos valores según
tu configuración de hardware y requerimientos de red.

Autores: Francisco Fernández & Nahuel Ontivero
Universidad: UTN - Facultad Regional Tucumán
"""

# ================================================================
# CONFIGURACIÓN DE NODO E IDENTIFICACIÓN
# ================================================================

NODE_ID = 1  # ID único del nodo en la red mesh (cambiar para cada nodo)

# ================================================================
# CONFIGURACIÓN DE CONECTIVIDAD WIFI
# ================================================================

WIFI_SSID = "TU_SSID"          # Nombre de la red WiFi
WIFI_PASSWORD = "TU_PASSWORD"   # Contraseña de la red WiFi

# ================================================================
# CONFIGURACIÓN DEL PROTOCOLO LORA
# ================================================================

# Umbral de calidad de señal (RSSI) para considerar un nodo como vecino
# Valores típicos: -60 (señal fuerte) a -120 (señal débil)
LORA_QOS = -90  

# Número máximo de intentos para sincronizar la hora con API externa
MAX_TIME_SYNC_ATTEMPTS = 5

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
# CONFIGURACIÓN DE TEMPORIZADORES
# ================================================================

# IDs de temporizadores disponibles en ESP32 (0-3)
TIMER_ID_LORA = 1      # Temporizador para operaciones DSR
TIMER_ID_VECINOS = 0   # Temporizador para anuncios de vecinos

# Intervalo para envío de mensajes HELLO a vecinos (en milisegundos)
# Valores recomendados: 5000-15000 ms
PERIODIC_VECINOS_INTERVAL = 10000

# ================================================================
# CONFIGURACIÓN DE APIs EXTERNAS
# ================================================================

# URL de la API para sincronización de tiempo (WorldTimeAPI)
# Cambia la zona horaria según tu ubicación
API_TIME_URL = "http://worldtimeapi.org/api/timezone/America/Argentina/Buenos_Aires"

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
