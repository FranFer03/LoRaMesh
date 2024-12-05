import asyncio
import json
import requests

# Configuración del broker MQTT
MQTT_BROKER = "mqtt://15.228.205.212"  # Cambia esto por tu broker
MQTT_TOPIC = "A/data"  # Tema donde se enviarán los datos
MQTT_USER = "espnahuel"     # Usuario
MQTT_PASSWORD = "nahuel"    # Contraseña

# URL de la API donde se enviarán los datos
API_URL = "http://54.232.229.75:8000/node/list/"

# Función para procesar los mensajes
async def process_message(message):
    try:
        # Decodificar el mensaje recibido
        message = message.data.decode("utf-8")
        print(f"Mensaje recibido: {message}")

        # Verificar si el mensaje empieza con "RESP"
        if message.startswith("RESP"):
            # Separar el mensaje por los delimitadores ":"
            parts = message.split(":")
            
            # Verificar que el mensaje tiene el formato esperado
            if len(parts) == 7:
                # Desglosar la cadena en las partes correspondientes
                node = parts[1]
                timestamp = int(parts[3])
                latitude, longitude, temperature = parts[5].split("/")

                # Crear el diccionario con la información desglosada
                data = {
                    "node": node,
                    "longitude": float(longitude),
                    "latitude": float(latitude),
                    "temperature": int(temperature),
                    "humidity": int(0),
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
                if response.status_code == 201:
                    print("Datos enviados exitosamente a la API.")
                else:
                    print(f"Error al enviar datos a la API: {response.status_code}")
            else:
                print("Mensaje con formato incorrecto.")
        else:
            print("Mensaje no es del tipo RESP.")
    except Exception as e:
        print(f"Error procesando el mensaje: {e}")

# Función principal del cliente MQTT
async def mqtt_client():
    from hbmqtt.client import MQTTClient, ConnectException
    
    client = MQTTClient()
    try:
        print("Conectando al broker MQTT...")
        await client.connect(MQTT_BROKER, username=MQTT_USER, password=MQTT_PASSWORD)
        print("Conexión al broker MQTT exitosa!")
        await client.subscribe([(MQTT_TOPIC, 0)])

        print("Esperando mensajes...")
        while True:
            message = await client.deliver_message()
            await process_message(message.publish_packet.payload)
    except ConnectException as e:
        print(f"Error al conectar al broker: {e}")
    finally:
        await client.disconnect()

# Iniciar el cliente MQTT
if __name__ == "__main__":
    asyncio.run(mqtt_client())
