import serial
import time
import json
import threading

# Configura el puerto serie (ajusta el nombre del puerto según tu sistema operativo)
ser = serial.Serial('COM3', 115200, timeout=1)  # En Windows
# ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)  # En Linux o Mac

# Intentar abrir el puerto serie
try:
    if not ser.is_open:
        ser.open()
    print("Conectado")
except:
    print("No se pudo conectar")

# Mostrar menú
def mostrar_menu():
    print("\n--- Menú ---")
    print("1- Buscar rutas")
    print("2- Mostrar caminos")
    print("3- Vecinos")
    print("4- Send hello")
    print("5- Salir")

# Enviar comando a la Raspberry Pi Pico
def enviar_comando(opcion):
    if opcion == 1:
        ser.write(b'RUTAS\n')
    elif opcion == 2:
        ser.write(b'CAMINOS\n')
    elif opcion == 3:
        ser.write(b'VECINOS\n')
    elif opcion == 4:
        ser.write(b'ENVIAR_QUERY\n')

# Escuchar respuestas de la Raspberry Pi Pico
def escuchar_respuesta():
    print("Escuchando respuestas de la Raspberry Pi Pico...")
    while True:
        if ser.in_waiting > 0:  # Si hay datos disponibles en el buffer
            # Leer la línea y decodificar
            linea = ser.readline().decode('utf-8').strip()
            print("Respuesta:", linea)  # Imprimir la respuesta recibida
            if 'FIN' in linea:  # Modifica esta línea si necesitas otro criterio de fin
                break

# Convierte un mensaje JSON a un diccionario
def recibir_y_convertir_mensaje(mensaje_json):
    try:
        # Convertir el mensaje JSON a un diccionario
        diccionario = json.loads(mensaje_json)
        return diccionario
    except json.JSONDecodeError:
        print("Error: El mensaje recibido no es un JSON válido.")
        return None

# Función principal para manejar el menú y la lógica de comandos
def menu_principal():
    while True:
        mostrar_menu()
        try:
            opcion = int(input("Selecciona una opción: "))
        except ValueError:
            print("Por favor, introduce un número válido.")
            continue

        if opcion == 5:  # Opción para salir del programa
            print("Saliendo del programa.")
            ser.close()
            break
        else:
            # Enviar el comando en un hilo separado
            enviar_hilo = threading.Thread(target=enviar_comando, args=(opcion,))
            enviar_hilo.start()

            # Pequeña pausa para evitar colisiones en el puerto serial
            time.sleep(0.1)

# Crear y ejecutar el hilo para escuchar respuestas
escuchar_hilo = threading.Thread(target=escuchar_respuesta)
escuchar_hilo.daemon = True  # Hilo en segundo plano para que se detenga al cerrar el programa
escuchar_hilo.start()

# Ejecutar el menú principal
menu_principal()
