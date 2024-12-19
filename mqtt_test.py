import paho.mqtt.client as mqtt
import json
import requests  # Importamos la librería requests

# Configuración del broker MQTT
MQTT_BROKER = "15.228.205.212"  # Cambia esto por tu broker
MQTT_PORT = 1883
MQTT_TOPIC = "A/data"  # Tema donde se enviarán los datos
MQTT_USER = "espnahuel"     # Usuario
MQTT_PASSWORD = "nahuel"    # Contraseña

# URL de la API donde se enviarán los datos
API_URL = "http://15.228.205.212:8000/node/list/"

# Función que se ejecuta cuando el cliente se conecta al broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conexión al broker MQTT exitosa!")
        client.subscribe(MQTT_TOPIC)  # Suscribirse al tema después de conectar
    else:
        print(f"Error al conectar al broker, código: {rc}")

# Función que se ejecuta cuando se recibe un mensaje
def on_message(client, userdata, msg):
    # Decodificar el mensaje recibido
    message = msg.payload.decode("utf-8")
    print(f"Mensaje recibido: {message}")
    
    # Verificar si el mensaje empieza con "RESP"
    if message.startswith("RESP"):
        # Separar el mensaje por los delimitadores ":"
        parts = message.split(":")
        
        # Verificar que el mensaje tiene el formato esperado
        if len(parts) == 7:
            try:
                # Desglosar la cadena en las partes correspondientes
                node = parts[1]
                timestamp = int(parts[3])
                latitude, longitude, temperature = parts[5].split("/")

                # Crear el diccionario con la información desglosada
                data = {
                    "node": node,
                    "longitude": float(longitude),
                    "latitude": float(latitude),
                    "temperature": round(float(temperature),2),
                    "humidity": int(1),
                    "pressure": int(400),
                    "altitude": int(400),
                    "timestamp": timestamp
                }
                
                # Mostrar el resultado en formato JSON
                print("Datos desglosados:")
                print(json.dumps(data, indent=4))

                # Enviar los datos a la API mediante un POST
                response = requests.post(API_URL, json=data)

                # Verificar la respuesta de la API
                if response.status_code == 200:
                    print("Datos enviados exitosamente a la API.")
                else:
                    print(f"Error al enviar datos a la API: {response.status_code}")

            except Exception as e:
                print(f"Error al desglosar los datos: {e}")
        else:
            print("Mensaje con formato incorrecto.")
    else:
        print("Mensaje no es del tipo RESP.")

# Crear un cliente MQTT
client = mqtt.Client("PythonClient")

# Configurar las credenciales de usuario y contraseña
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# Asignar las funciones de conexión y manejo de mensajes
client.on_connect = on_connect
client.on_message = on_message

# Conectar al broker
print("Conectando al broker MQTT...")
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

# Iniciar el loop del cliente para recibir mensajes
client.loop_forever()