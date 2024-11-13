import sys
import time
import ujson
from DSRNode import DSRNode
from machine import Pin, Timer, SoftSPI, SoftI2C, RTC
from LoRa import LoRa

tim1 = Timer()
tim0 = Timer()
rtc = RTC()
#rtc.datetime((2024, 11, 7, 27, 34, 0, 0, 0))
print(rtc.datetime())
lora = 0
nodo = DSRNode("A", lora, rtc, tim1, qos=-80, role="master")

# Definir el diccionario de datos
query = {'RREP': [], 'RREQ': [['784317687', 'A', 'B'], ['784317689', 'A', 'B']], 'DATA': [], 'RESP': []}
data = "RESP:ORIGEN:DESTINATION:TIMESTAMP:ROUTE:35/195:CHECKSUM"

def envio(timer):
    print(data)

#tim0.init(period=2000, mode=Timer.PERIODIC, callback=envio)

def main():
    while True:
        try:
            comando = sys.stdin.readline().strip()  # Intentar leer un comando
            if comando:
                if comando.startswith('destino'):
                    try:
                        line = comando.split("/")
                        node.brocast_rreq(line[1])
                    except ValueError:
                        pass
                elif comando == 'CAMINOS':
                    print(nodo.routes)
                elif comando.startswith('datos'):
                    try:
                        line = comando.split("/")
                        node.request_data(line[1])
                    except ValueError:
                        pass
                elif comando == 'VECINOS':
                    print(nodo.neighbors)
                elif comando == 'OTHER':
                    pass

                else:
                    print('Comando no reconocido')

        except Exception as e:
            print("Error:", e)

        time.sleep(0.1)

main()
