"""
Red Mesh LoRa - Nodo Maestro con API
=====================================

Este módulo implementa el nodo maestro de la red mesh LoRa que actúa como gateway
entre la red de sensores y servicios externos via WiFi. 

Características principales:
- Protocolo DSR (Dynamic Source Routing) para enrutamiento mesh
- Sincronización automática de tiempo via API web
- Comunicación LoRa bidireccional con nodos esclavos
- Configuración modular via archivo config.py
- Manejo robusto de errores y reconexión automática

Autores: Francisco Fernández & Nahuel Ontivero
Universidad: UTN - Facultad Regional Tucumán
Fecha: 2024
Licencia: MIT
"""

import time
from machine import Pin, RTC, SoftSPI, Timer # type: ignore
from firmware.master_api.SOFWARE.DSRNode import DSRNode # type: ignore
import network # type: ignore
import _thread
import urequests # type: ignore
from LoRa import LoRa # type: ignore
from config import * # Importa todas las constantes de configuración

# ================================================================
# FUNCIONES DE CONFIGURACIÓN INICIAL
# ================================================================

def connect_to_wifi():
    """
    Establece conexión WiFi usando las credenciales del archivo config.py.
    
    La función intenta conectarse continuamente hasta lograr la conexión,
    mostrando el progreso en la consola. Una vez conectada, muestra la
    dirección IP asignada.
    
    Returns:
        None
        
    Raises:
        Exception: Si hay problemas con la configuración WiFi
        
    Note:
        Las credenciales WIFI_SSID y WIFI_PASSWORD deben estar definidas
        en el archivo config.py
    """
    print("=== CONFIGURACIÓN WIFI ===")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    print(f"Conectando a WiFi: {WIFI_SSID}")
    while not wlan.isconnected():
        print("Conectando a Wi-Fi...")
        time.sleep(0.5)
    
    ip_address = wlan.ifconfig()[0]
    print(f'✓ Conexión Wi-Fi establecida!')
    print(f'✓ Dirección IP: {ip_address}')
    print("=" * 30)

def sync_system_time():
    """
    Sincroniza el reloj del sistema (RTC) con una API de tiempo externa.
    
    Realiza múltiples intentos según MAX_TIME_SYNC_ATTEMPTS definido en config.py.
    Utiliza la API especificada en API_TIME_URL para obtener la hora actual
    y configurar el RTC del microcontrolador.
    
    Returns:
        None
        
    Raises:
        Exception: Si no se puede sincronizar después de los intentos máximos
        
    Note:
        El formato de hora esperado es ISO 8601 de WorldTimeAPI
    """
    print("=== SINCRONIZACIÓN DE TIEMPO ===")
    attempts = 0
    
    while attempts < MAX_TIME_SYNC_ATTEMPTS:
        try:
            print(f"Sincronizando hora con API... (Intento {attempts + 1}/{MAX_TIME_SYNC_ATTEMPTS})")
            response = urequests.get(API_TIME_URL)
            
            if response.status_code == 200:
                data = response.json()
                datetime_str = data["datetime"]
                
                # Parsear fecha y hora desde formato ISO 8601
                year, month, day = map(int, datetime_str[:10].split("-"))
                hour, minute, second = map(int, datetime_str[11:19].split(":"))
                sub_second = int(round(int(datetime_str[20:26]) / 10000))
                
                # Configurar RTC del microcontrolador
                rtc = RTC()
                rtc.datetime((year, month, day, 0, hour, minute, second, sub_second))
                
                print("✓ Hora sincronizada en el RTC.")
                print(f"✓ Fecha/Hora: {day:02d}/{month:02d}/{year} {hour:02d}:{minute:02d}:{second:02d}")
                print("=" * 30)
                return
            else:
                print(f"✗ Error HTTP {response.status_code} al obtener la hora desde la API.")
                
        except Exception as e:
            print(f"✗ Error sincronizando hora: {e}")
            
        attempts += 1
        if attempts < MAX_TIME_SYNC_ATTEMPTS:
            print(f"Reintentando en 2 segundos...")
            time.sleep(2)
    
    print(f"✗ No se pudo sincronizar la hora tras {MAX_TIME_SYNC_ATTEMPTS} intentos.")
    print("⚠ Continuando con hora local del RTC")
    print("=" * 30)

# ================================================================
# FUNCIONES DE COMUNICACIÓN LORA
# ================================================================

def handle_lora_messages():
    """
    Procesa mensajes LoRa entrantes y salientes de forma coordinada.
    
    Esta función maneja tanto la recepción de mensajes nuevos como 
    el procesamiento de respuestas pendientes. Es llamada periódicamente
    desde el bucle principal.
    
    Returns:
        None
        
    Note:
        Utiliza el objeto global dsr_node para el manejo de protocolos
    """
    try:
        # Procesar mensajes entrantes
        dsr_node.receive_message()
        
        # Verificar respuestas pendientes
        msg = dsr_node.waiting_for_response()
        if msg is not None:
            print(f'📨 Mensaje recibido: {msg}')
            # Aquí se podría procesar el mensaje recibido
            # por ejemplo, enviarlo a una API externa
            
    except Exception as e:
        print(f"✗ Error procesando mensajes LoRa: {e}")

def send_periodic_messages():
    """
    Hilo dedicado para el envío periódico de mensajes y mantenimiento de la red.
    
    Este hilo corre continuamente y se encarga de:
    - Procesar mensajes LoRa de forma regular
    - Mantener la comunicación con nodos vecinos
    - Actualizar datos de sensores (si están configurados)
    
    Returns:
        None
        
    Note:
        Ejecuta en un hilo separado para no bloquear el programa principal
    """
    print("🔄 Iniciando hilo de mensajes periódicos...")
    
    while True:
        try:
            # Si hay sensores conectados, actualizar sus valores
            # dsr_node.update_sensor('')  # Descomentar si se implementan sensores
            
            # Procesar comunicaciones LoRa
            handle_lora_messages()
            
            # Pausa corta para permitir otros procesos
            time.sleep(0.1)
            
        except Exception as e:
            print(f"✗ Error en hilo de mensajes periódicos: {e}")
            time.sleep(1)  # Pausa más larga en caso de error

def send_neighbor_announcement(timer):
    """
    Callback del temporizador para enviar anuncios HELLO periódicos.
    
    Esta función es llamada automáticamente por el temporizador para
    mantener la conectividad con nodos vecinos. Los mensajes HELLO
    permiten el descubrimiento automático de la topología de red.
    
    Args:
        timer: Objeto Timer que ejecuta esta función
        
    Returns:
        None
        
    Note:
        La frecuencia está definida por PERIODIC_VECINOS_INTERVAL en config.py
    """
    try:
        dsr_node.send_hello()
        print(f"📡 HELLO enviado desde nodo {NODE_ID}")
    except Exception as e:
        print(f"✗ Error enviando HELLO: {e}")

# ================================================================
# CONFIGURACIÓN E INICIALIZACIÓN DEL SISTEMA
# ================================================================

print("🚀 Iniciando Nodo Maestro LoRa Mesh")
print("=" * 50)

# Configuración inicial de conectividad
connect_to_wifi()
sync_system_time()

print("=== CONFIGURACIÓN LORA ===")
# Configuración del bus SPI para comunicación con módulo LoRa
spi = SoftSPI(
    baudrate=3000000,       # Velocidad de comunicación SPI
    polarity=0,             # Polaridad del reloj
    phase=0,                # Fase del reloj
    sck=Pin(SPI_SCK_PIN),   # Pin de reloj (Clock)
    mosi=Pin(SPI_MOSI_PIN), # Pin de datos maestro -> esclavo
    miso=Pin(SPI_MISO_PIN)  # Pin de datos esclavo -> maestro
)

# Inicialización del módulo LoRa
lora = LoRa(
    spi,                        # Bus SPI configurado
    cs_pin=Pin(LORA_CS_PIN),    # Pin Chip Select
    reset_pin=Pin(LORA_RST_PIN), # Pin de Reset
    dio0_pin=Pin(LORA_DIO0_PIN)  # Pin de interrupción DIO0
)

# Inicialización del RTC para timestamps
rtc = RTC()

print(f"✓ Módulo LoRa configurado (CS: GPIO{LORA_CS_PIN}, RST: GPIO{LORA_RST_PIN})")
print("=" * 30)

print("=== INICIALIZACIÓN DSR ===")
# Inicialización del nodo DSR con protocolo de enrutamiento
dsr_node = DSRNode(
    NODE_ID,                    # ID único del nodo
    lora,                       # Instancia del módulo LoRa
    rtc,                        # Reloj de tiempo real
    Timer(TIMER_ID_LORA),       # Temporizador para operaciones DSR
    qos=LORA_QOS               # Umbral de calidad de señal
)

print(f"✓ Nodo DSR inicializado (ID: {NODE_ID}, QoS: {LORA_QOS} dBm)")

# Configuración del temporizador para anuncios periódicos de vecinos
neighbor_timer = Timer(TIMER_ID_VECINOS)
neighbor_timer.init(
    period=PERIODIC_VECINOS_INTERVAL,  # Intervalo en milisegundos
    mode=Timer.PERIODIC,               # Modo periódico
    callback=send_neighbor_announcement # Función a ejecutar
)

print(f"✓ Temporizador de vecinos configurado ({PERIODIC_VECINOS_INTERVAL}ms)")
print("=" * 30)

# ================================================================
# INICIO DE HILOS DE EJECUCIÓN
# ================================================================

print("=== INICIANDO HILOS ===")
try:
    # Hilo para manejo de mensajes periódicos
    _thread.start_new_thread(send_periodic_messages, ())
    print("✓ Hilo de mensajes periódicos iniciado")
    
    # Aquí se pueden agregar otros hilos según necesidades:
    # - Hilo MQTT para comunicación con broker
    # - Hilo de API web para servidor HTTP
    # - Hilo de procesamiento de datos de sensores
    
except Exception as e:
    print(f"✗ Error al iniciar hilos: {e}")

print("=" * 30)

# ================================================================
# BUCLE PRINCIPAL DEL PROGRAMA
# ================================================================

print("🔄 Iniciando bucle principal...")
print("📡 Nodo maestro listo para comunicación")
print("=" * 50)

while True:
    handle_lora_messages()
    time.sleep(0.1)