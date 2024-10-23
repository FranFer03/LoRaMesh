import serial
import time

# Configura el puerto serie (ajusta el nombre del puerto según tu sistema operativo)
ser = serial.Serial('COM3', 115200, timeout=1)  # En Windows
# ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)  # En Linux o Mac

try:
    ser.open()
    print("Conectado")
except:
    if(ser.isOpen()):
        print("Conectado")
    else:
        print("No conectado")

# Mostrar menú
def mostrar_menu():
    print("\n--- Menú ---")
    print("1- Descubrir redes")
    print("2- Mostrar caminos")
    print("3- Enviar paquete")
    print("4- Sincronizar tiempo")
    print("5- Salir")

# Enviar comando a la Raspberry Pi Pico
def enviar_comando(opcion):
    if opcion == 1:
        ser.write(b'REDES\n')
    elif opcion == 2:
        ser.write(b'CAMINOS\n')
    elif opcion == 3:
        ser.write(b'PAQUETE\n')
    elif opcion == 4:
        ser.write(b'SINCRONIZAR\n')

# Escuchar respuesta de la Raspberry Pi Pico
def escuchar_respuesta():
    respuesta = ser.readline().decode('utf-8').strip()
    print("Respuesta de la Raspberry Pi Pico: \n", respuesta)

while True:
    mostrar_menu()
    opcion = int(input("Selecciona una opción: "))
    
    if opcion == 5:  # Opción para salir del programa
        print("Saliendo del programa.")
        break
    
    enviar_comando(opcion)
    time.sleep(0.1)
    escuchar_respuesta()
    time.sleep(1)
    
