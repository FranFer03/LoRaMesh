import time
from machine import Pin, Timer, SoftSPI, SoftI2C
from LoRa import LoRa
from ssd1306 import SSD1306_I2C
import json

# Configuración SPI para LoRa
spi = SoftSPI(baudrate=3000000, polarity=0, phase=0, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
lora = LoRa(spi, cs_pin=Pin(18), reset_pin=Pin(14), dio0_pin=Pin(26))

# Configuración de la pantalla OLED
oledSDA = Pin(15, Pin.OUT, Pin.PULL_UP)
oledSCL = Pin(4, Pin.OUT, Pin.PULL_UP)
oledRST = Pin(16, Pin.OUT)
oledRST.value(1)
i2c = SoftI2C(oledSDA, oledSCL)
oled = SSD1306_I2C(128, 64, i2c)

while True:
    oled.fill(0)  # Limpia la pantalla en cada iteración
    if lora.is_packet_received():
        message = lora.get_packet(rssi=False)
        oled.text("Mensaje Recibido", 0, 10)
        if len(message) > 0 :
            oled.text(message.get("payload")[:20], 0, 30)  # Mostrar los primeros 20 caracteres del mensaje
        print(f"Se recibió el mensaje: {message}")
        oled.show()  # Refrescar la pantalla para mostrar el mensaje
    time.sleep(1)  # Pausa para evitar un ciclo continuo demasiado rápido