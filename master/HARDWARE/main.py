import time
from umqtt.simple import MQTTClient # type: ignore
from machine import Pin, RTC, SPI, Timer # type: ignore
from DSRNode import DSRNode # type: ignore
import network # type: ignore
import _thread
import urequests # type: ignore
from LoRa import LoRa # type: ignore


# Configuración de nodos y red
NODE_ID = "A"
WIFI_SSID = "iPhone de Nahuel"
WIFI_PASSWORD = "12345678"
MQTT_BROKER = '15.228.205.212'
MQTT_PORT = 1883
MQTT_USER = 'espfran'
MQTT_PASSWORD = 'carpincho'

# Tópicos MQTT
MQTT_TOPIC_RESULT = f"{NODE_ID}/data"
MQTT_TOPIC_COMMANDS = f"{NODE_ID}/commands"
MQTT_TOPIC_REPORTS = f"{NODE_ID}/reports"


def connect_to_wifi():
    """Conecta el dispositivo a la red Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        print("Conectando a Wi-Fi...")
        time.sleep(0.5)
    print('Conexión Wi-Fi establecida! IP:', wlan.ifconfig()[0])


def sync_system_time():
    """Sincroniza el reloj del sistema con una API de tiempo."""
    try:
        print("Sincronizando hora con API...")
        url = "http://worldtimeapi.org/api/timezone/America/Argentina/Buenos_Aires"
        response = urequests.get(url)
        if response.status_code == 200:
            data = response.json()
            datetime_str = data["datetime"]
            year, month, day = map(int, datetime_str[:10].split("-"))
            hour, minute, second = map(int, datetime_str[11:19].split(":"))
            sub_second = int(round(int(datetime_str[20:26]) / 10000))
            
            rtc = RTC()
            rtc.datetime((year, month, day, 0, hour, minute, second, sub_second))
            print("Hora sincronizada en el RTC.")
        else:
            #print("Error al obtener la hora desde la API.")
            pass
    except Exception as e:
        time.sleep(0.5)
        sync_system_time()


def process_command(command):
    """Procesa los comandos recibidos a través de MQTT."""
    try:
        if command.startswith('DESTINO'):
            destination = command.split("/")[1]
            message = f"Solicitando caminos: {destination}"
            mqtt_client.publish(MQTT_TOPIC_REPORTS, message)
            dsr_node.broadcast_rreq(destination)
        elif command == 'CAMINOS':
            message = str(dsr_node.routes)
            mqtt_client.publish(MQTT_TOPIC_REPORTS, message)
        elif command.startswith('DATOS'):
            data_request = command.split("/")[1]
            message = "Solicitando datos"
            mqtt_client.publish(MQTT_TOPIC_REPORTS, message)
            dsr_node.request_data(data_request)
        elif command == 'VECINOS':
            message = str(dsr_node.neighbors)
            mqtt_client.publish(MQTT_TOPIC_REPORTS, message)
        elif command == 'TIEMPO':
            message = str(dsr_node.timestamp_message)
            mqtt_client.publish(MQTT_TOPIC_REPORTS, message)
        else:
            message = f"Comando desconocido: {command}"
            mqtt_client.publish(MQTT_TOPIC_REPORTS, message)
    except Exception as e:
        print(f"Error al procesar comando {command}: {e}")


def on_mqtt_message(topic, msg):
    """Callback para manejar mensajes MQTT."""
    topic_decoded = topic.decode()
    command = msg.decode()
    print(f"Mensaje recibido en {topic_decoded}: {command}")
    process_command(command)


def handle_lora_messages():
    """Procesa mensajes LoRa."""
    dsr_node.waiting_for_response()
    dsr_node.receive_message()


def send_periodic_messages():
    """Envía mensajes periódicos a través de LoRa."""
    while True:
        dsr_node.update_sensor('')
        handle_lora_messages()
        time.sleep(0.1)


def receive_mqtt_messages():
    while True:
        try:
            mqtt_client.check_msg()
        except Exception as e:
            print("Error al recibir mensaje MQTT:", e)
            try:
                print("Reconectando al broker MQTT...")
                mqtt_client.connect()
                mqtt_client.subscribe(MQTT_TOPIC_COMMANDS)
                print("Re-suscrito al tema:", MQTT_TOPIC_COMMANDS)
            except Exception as reconnection_error:
                print("Error al reconectar al broker MQTT:", reconnection_error)
        time.sleep(0.1)


def send_neighbor_announcement(timer):
    """Envia un anuncio periódico a los vecinos."""
    dsr_node.send_hello()


# Configuración inicial
connect_to_wifi()
sync_system_time()

# Configuración MQTT
mqtt_client = MQTTClient(
    client_id="esp32-client",
    server=MQTT_BROKER,
    port=MQTT_PORT,
    user=MQTT_USER,
    password=MQTT_PASSWORD,
    keepalive=300
)
mqtt_client.set_callback(on_mqtt_message)

# Configuración de LoRa
spi = SPI(2,baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(5), reset_pin=Pin(4), dio0_pin=Pin(2))
rtc = RTC()

# Inicialización de nodos y temporizadores
dsr_node = DSRNode(NODE_ID, lora, rtc, Timer(1), mqtt_client, MQTT_TOPIC_RESULT, qos=-75)
neighbor_timer = Timer(0)
neighbor_timer.init(period=10000, mode=Timer.PERIODIC, callback=send_neighbor_announcement)

# Conexión MQTT
try:
    print("Conectando al broker MQTT...")
    mqtt_client.connect()
    print(f"Subscribiéndose a: {MQTT_TOPIC_COMMANDS}")
    mqtt_client.subscribe(MQTT_TOPIC_COMMANDS)
    print("Conexión MQTT establecida!")
except Exception as e:
    print(f"No se pudo conectar o subscribir al broker MQTT: {e}")

# Inicia hilos para envío y recepción de mensajes
try:
    _thread.start_new_thread(send_periodic_messages, ())
    _thread.start_new_thread(receive_mqtt_messages, ())
except Exception as e:
    print(f"Error al iniciar hilos: {e}")

# Bucle principal
while True:
    handle_lora_messages()
    time.sleep(0.1)
