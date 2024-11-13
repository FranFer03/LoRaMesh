import sys
import time
from DSRNode import DSRNode
from machine import Pin, Timer, SoftSPI, SoftI2C, RTC
from LoRa import LoRa

spi = SoftSPI(baudrate=3000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(18), reset_pin=Pin(14), dio0_pin=Pin(26))

tim1 = Timer(0)
rtc = RTC()
rtc.datetime((2024, 11, 13, 15, 23, 0, 0, 0))
print(rtc.datetime())
nodo = DSRNode("A", lora, rtc, tim1, qos=-80, role="master")


def main():
    while True:
        try:
            comando = sys.stdin.readline().strip()
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