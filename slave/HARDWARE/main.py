import time
from machine import Pin, Timer, SPI, RTC
from LoRa import LoRa
import json
from DSRNode import DSRNode

spi = SPI(2,baudrate=3000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(5), reset_pin=Pin(4), dio0_pin=Pin(2))

tim0 = Timer(0)
tim1 = Timer(1)
rtc = RTC()
rtc.datetime((2024, 11, 13, 15, 9, 0, 0, 0))
print(rtc.datetime())

nodo = DSRNode("B", lora, rtc, tim0, qos=-80, role="slave")

def hello(timer):
    nodo.send_hello()
    print("Hello enviado")

tim1.init(period=5000, mode=Timer.PERIODIC, callback=hello)

while True:
    nodo.waiting_for_response()
    nodo.receive_message()
    time.sleep(1)
