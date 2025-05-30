import time
from machine import Pin, RTC, SoftSPI, Timer # type: ignore
from firmware.master_api.SOFWARE.DSRNode import DSRNode # type: ignore
import network # type: ignore
import _thread
import urequests # type: ignore
from LoRa import LoRa # type: ignore
from config import * # Importa las constantes

def connect_to_wifi():
    """
    Conecta el dispositivo a la red Wi-Fi usando las credenciales definidas en config.py.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        print("Conectando a Wi-Fi...")
        time.sleep(0.5)
    print('Conexión Wi-Fi establecida! IP:', wlan.ifconfig()[0])

def sync_system_time():
    """
    Sincroniza el reloj del sistema con una API de tiempo.
    Reintenta hasta MAX_TIME_SYNC_ATTEMPTS veces si falla.
    """
    attempts = 0
    while attempts < MAX_TIME_SYNC_ATTEMPTS:
        try:
            print(f"Sincronizando hora con API... (Intento {attempts + 1})")
            response = urequests.get(API_TIME_URL)
            if response.status_code == 200:
                data = response.json()
                datetime_str = data["datetime"]
                year, month, day = map(int, datetime_str[:10].split("-"))
                hour, minute, second = map(int, datetime_str[11:19].split(":"))
                sub_second = int(round(int(datetime_str[20:26]) / 10000))
                rtc = RTC()
                rtc.datetime((year, month, day, 0, hour, minute, second, sub_second))
                print("Hora sincronizada en el RTC.")
                return
            else:
                print("Error al obtener la hora desde la API.")
        except Exception as e:
            print(f"Error sincronizando hora: {e}")
        attempts += 1
        time.sleep(0.5)
    print("No se pudo sincronizar la hora tras varios intentos.")

def handle_lora_messages():
    """
    Procesa mensajes LoRa: espera respuestas y recibe mensajes nuevos.
    """
    dsr_node.receive_message()
    msg = dsr_node.waiting_for_response()
    if msg is not None:
        print(f'Mesaje recibido: {msg}')

def send_periodic_messages():
    """
    Envía mensajes periódicos a través de LoRa y procesa mensajes entrantes.
    """
    while True:
        # Si tienes sensores, aquí puedes actualizar sus valores
        # dsr_node.update_sensor('')  # Descomenta si tienes este método implementado
        handle_lora_messages()
        time.sleep(0.1)

def send_neighbor_announcement(timer):
    """
    Envía un anuncio periódico a los vecinos usando LoRa.
    """
    dsr_node.send_hello()

# --- Configuración inicial ---
connect_to_wifi()
sync_system_time()

# --- Configuración de LoRa ---
spi = SoftSPI(
    baudrate=3000000,
    polarity=0,
    phase=0,
    sck=Pin(SPI_SCK_PIN),
    mosi=Pin(SPI_MOSI_PIN),
    miso=Pin(SPI_MISO_PIN)
)
lora = LoRa(
    spi,
    cs_pin=Pin(LORA_CS_PIN),
    reset_pin=Pin(LORA_RST_PIN),
    dio0_pin=Pin(LORA_DIO0_PIN)
)
rtc = RTC()

# --- Inicialización de nodos y temporizadores ---
dsr_node = DSRNode(NODE_ID, 
                   lora, 
                   rtc, 
                   Timer(TIMER_ID_LORA), 
                   qos=LORA_QOS)

# Temporizador para enviar anuncios de vecinos
neighbor_timer = Timer(TIMER_ID_VECINOS)

neighbor_timer.init(period=PERIODIC_VECINOS_INTERVAL, 
                    mode=Timer.PERIODIC, 
                    callback=send_neighbor_announcement)

# --- Inicia hilos para envío y recepción de mensajes ---
try:
    _thread.start_new_thread(send_periodic_messages, ())
    # Puedes agregar aquí otros hilos, como MQTT, si lo necesitas
except Exception as e:
    print(f"Error al iniciar hilos: {e}")

# --- Bucle principal ---
while True:
    handle_lora_messages()
    time.sleep(0.1)