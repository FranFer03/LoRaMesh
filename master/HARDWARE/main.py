import sys
import _thread
import time
from DSRNode import DSRNode
from machine import Pin, Timer, SPI, RTC
from LoRa import LoRa

spi = SPI(2,baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(5), reset_pin=Pin(4), dio0_pin=Pin(2))

tim1 = Timer(0)
rtc = RTC()
rtc.datetime((2024, 11, 13, 15, 23, 0, 0, 0))

# Inicialización del nodo
nodo = DSRNode("A", lora, rtc, tim1, qos=-75, role="master")
nodo.send_hello()

# Función para manejar la espera y recepción de mensajes
def manejar_respuesta():
    while True:
        nodo.waiting_for_response()
        nodo.receive_message()
        time.sleep(0.1)  # Pausa breve para evitar consumo excesivo de CPU

# Función para manejar los comandos
def manejar_comandos():
    while True:
        try:
            comando = sys.stdin.readline().strip()  # Leer comando directamente
            if comando:
                if comando.startswith('DESTINO'):
                    try:
                        line = comando.split("/")
                        nodo.broadcast_rreq(line[1])  # Cambiado 'node' por 'nodo'
                    except ValueError:
                        pass
                elif comando == 'CAMINOS':
                    print(nodo.routes)
                elif comando.startswith('DATOS'):
                    try:
                        line = comando.split("/")
                        nodo.request_data(line[1])  # Cambiado 'node' por 'nodo'
                    except ValueError:
                        pass
                elif comando == 'VECINOS':
                    print(nodo.neighbors)
                elif comando == 'OTHER':
                    pass
                else:
                    print('Comando no reconocido')
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.1)  # Pausa breve para evitar consumo excesivo de CPU

# Iniciar los hilos utilizando _thread
try:
    _thread.start_new_thread(manejar_respuesta, ())
    _thread.start_new_thread(manejar_comandos, ())
except Exception as e:
    print(f"Error al iniciar hilos: {e}")

# Mantener el programa principal en ejecución
while True:
    time.sleep(1)  # Mantener el bucle principal corriendo para que los hilos sigan activos
