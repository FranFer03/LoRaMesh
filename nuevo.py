import time 
from umqtt.simple import MQTTClient
from machine import Pin,RTC
import network
import _thread
import urequests
from LoRa import lora

node = "A"

WIFI_SSID = "TP-Link_4796"
WIFI_PASSWORD = "29792245"

MQTT_BROKER = '15.228.205.212'
MQTT_PORT = 1883
MQTT_USER = 'espfran'
MQTT_PASSWORD = 'carpincho'

MQTT_TOPIC = node + "/data"
MQTT_NODE = node + "/commands"
MQTT_REPORT = node + "/reports"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        print("Conectando a Wi-Fi...")
        time.sleep(0.5)
    print('Conexión Wi-Fi establecida! IP:', wlan.ifconfig()[0])

def sync_time():
    try:
        print("Sincronizando hora con API...")
        url = "http://worldtimeapi.org/api/timezone/America/Argentina/Buenos_Aires" 
        response = urequests.get(url)
        if response.status_code == 200:
            data = response.json()
            fecha_hora = str(data["datetime"])
            año = int(fecha_hora[0:4])
            mes = int(fecha_hora[5:7])
            día = int(fecha_hora[8:10])
            hora = int(fecha_hora[11:13])
            minutos = int(fecha_hora[14:16])
            segundos = int(fecha_hora[17:19])
            sub_segundos = int(round(int(fecha_hora[20:26]) / 10000))
            
            rtc = RTC()
            rtc.datetime((año, mes, día, 0, hora, minutos, segundos, sub_segundos))
            print("Hora sincronizada en el RTC.")
        else:
            print("Error al obtener la hora desde la API.")
    except:
        time.sleep(0.5)
        sync_time()
        

def is_leap_year(year):
    return (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))

def days_in_month(month, year):
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and is_leap_year(year):
        return 29
    return days_per_month[month - 1]

def calculate_days_since_epoch(year, month, day, hour, minute, second):
    days = (year - 1970) * 365 + (year - 1969) // 4 
    for m in range(1, month):
        days += days_in_month(m, year)
    days += day - 1
    total_seconds = days * 86400
    total_seconds += hour * 3600 + minute * 60 + second
    
    return total_seconds

def process_destination(command):
    try:
        line = command.split("/")
        message = "Data to {line[1]}"
        client.publish(MQTT_REPORT, message)
    except ValueError:
        print("Error processing DESTINATION command")

def process_routes():
    message = "[a,b]"
    client.publish(MQTT_REPORT, message)

def process_data(command):
    try:
        line = command.split("/")
        message = f"Processing data: {line[1]}"
        client.publish(MQTT_REPORT, message)
    except ValueError:
        print("Error processing DATA command")

def process_neighbors():
    message = "Neighbors are: [neighbor1, neighbor2]"
    client.publish(MQTT_REPORT, message)

def process_other():
    message = "OTHER command received, no action defined."
    client.publish(MQTT_REPORT, message)

def unknown_command(command):
    message = f"Unknown command: {command}"
    client.publish(MQTT_REPORT, message)

def on_message(topic, msg):
    print(f"Message received on {topic.decode()}: {msg.decode()}")
    command = msg.decode()
    if command.startswith('DESTINO'):
        process_destination(command)
    elif command == 'CAMINOS':
        process_routes()
    elif command.startswith('DATOS'):
        process_data(command)
    elif command == 'VECINOS':
        process_neighbors()
    elif command == 'OTHER':
        process_other()
    else:
        unknown_command(command)



def send_messages():
    rtc = RTC()
    while True:
        try:
            rtc_time = rtc.datetime()
            # Obtener la hora en formato (año, mes, día, semana, hora, minuto, segundo, milisegundo)
            
            year, month, day, hour, minute, second = rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[4], rtc_time[5], rtc_time[6]
            print(f"Fecha y hora actual: {year}-{month}-{day} {hour}:{minute}:{second}")
            timestamp_message = calculate_days_since_epoch(year, month, day, hour, minute, second)
            print(timestamp_message)
            # Crear mensaje MQTT
            message = f"RESP:A:C:{timestamp_message}:B:48.85341/2.3488/30/80/800/1200:54"
            client.publish(MQTT_TOPIC, message)
            time.sleep(10)
        except Exception as e:
            print("Error al enviar mensaje:", e)
            
def receive_messages():
    while True:
        try:
            client.check_msg()
            time.sleep(0.1)
        except Exception as e:
            print("Error al recibir mensaje:", e)


client = MQTTClient(
    client_id="esp32-client",
    server=MQTT_BROKER,
    port=MQTT_PORT,
    user=MQTT_USER,
    password=MQTT_PASSWORD,
    keepalive=120
)

client.set_callback(on_message)

connect_wifi()
sync_time()

time.sleep(5)


try:
    print("Conectando al broker MQTT...")
    client.connect()
    print(f"Subscribiéndose a: {MQTT_NODE}")
    client.subscribe(MQTT_NODE)
    print("Conexión MQTT establecida!")
except Exception as e:
    print("No se pudo conectar o subscribir:", e)
    
try:
    _thread.start_new_thread(send_messages, ())
    _thread.start_new_thread(receive_messages, ())
except Exception as e:
    print("Error al iniciar los hilos:", e)


while True:
    pass
