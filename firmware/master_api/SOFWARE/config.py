# Configuración general y credenciales

NODE_ID = 1
WIFI_SSID = "TU_SSID"
WIFI_PASSWORD = "TU_PASSWORD"
LORA_QOS = -90  # Umbral de calidad de señal para vecinos
MAX_TIME_SYNC_ATTEMPTS = 5  # Número máximo de intentos para sincronizar la hora

# Pines para SPI y LoRa
SPI_SCK_PIN = 5
SPI_MOSI_PIN = 27
SPI_MISO_PIN = 19
LORA_CS_PIN = 18
LORA_RST_PIN = 14
LORA_DIO0_PIN = 26

# Seleccion de Timer
TIMER_ID_LORA = 1  # ID del temporizador para LoRa
TIMER_ID_VECINOS = 0 
PERIODIC_VECINOS_INTERVAL = 10000  # Intervalo para detectar vecinos (en ms)

# API
API_TIME_URL = "http://worldtimeapi.org/api/timezone/America/Argentina/Buenos_Aires"  # URL de la API para sincronizar la hora
