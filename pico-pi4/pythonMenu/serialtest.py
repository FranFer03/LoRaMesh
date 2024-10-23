import serial
import time

# Configuración del puerto serie (ajusta el nombre del puerto según tu sistema operativo)
# En Windows podría ser 'COM3', 'COM4', etc.
# En Linux o MacOS probablemente sea algo como '/dev/ttyUSB0' o '/dev/ttyACM0'
puerto = 'COM3'  # Cambia esto según corresponda
baudrate = 115200         # Velocidad de transmisión (asegúrate de que coincida con el valor configurado en la Raspberry Pi Pico)

# Abre el puerto serie
try:
    ser = serial.Serial(puerto, baudrate, timeout=1)
    print(f"Conectado a {puerto}")
except serial.SerialException as e:
    print(f"No se pudo abrir el puerto: {e}")
    exit()

def enviar_comando():
    while True:
        # Enviar el comando "TIEMPO"
        ser.write(b'TIEMPO\n')  # Envía el comando como bytes (terminado con salto de línea)
        
        # Leer la respuesta desde la Raspberry Pi Pico
        respuesta = ser.readline().decode('utf-8').strip()  # Leer la respuesta y decodificarla
        
        # Mostrar la respuesta en la consola
        if respuesta:
            print(f"Respuesta desde la Raspberry Pi Pico: {respuesta}")
        
        time.sleep(1)  # Esperar 1 segundo antes de volver a enviar el comando

if __name__ == "__main__":
    enviar_comando()
