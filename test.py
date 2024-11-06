def calculate_checksum(message):
    # Convertimos el mensaje en bytes
    message_bytes = message.encode('utf-8')
    
    # Inicializamos la suma
    checksum = 0
    
    # Procesamos el mensaje en bloques de 16 bits (2 bytes)
    for i in range(0, len(message_bytes), 2):
        # Tomamos cada par de bytes
        word = message_bytes[i]
        
        # Si hay un segundo byte en el par, lo agregamos
        if i + 1 < len(message_bytes):
            word = (word << 8) + message_bytes[i + 1]
        
        # Sumamos al checksum
        checksum += word
        
        # Verificamos si hay un acarreo y lo sumamos
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    
    # Tomamos el complemento de uno
    checksum = ~checksum & 0xFFFF
    
    return checksum


def generate_message(data, source, destination, msg_id, route, temp, hum):
    # Crear el mensaje sin checksum
    message = f'{data}:{source}:{destination}:{msg_id}:{route}:temp:{temp},hum={hum}'
    
    # Calcular el checksum
    checksum = calculate_checksum(message)
    
    # Añadir el checksum al mensaje
    message_with_checksum = f'{message}:{checksum}'
    
    return message_with_checksum


def verify_checksum(message_with_checksum):
    # Separar el mensaje y el checksum
    *message_parts, received_checksum = message_with_checksum.rsplit(":", 1)
    message = ":".join(message_parts)
    
    # Calcular el checksum nuevamente
    calculated_checksum = calculate_checksum(message)
    
    # Comparar checksums
    return int(received_checksum) == calculated_checksum


# Ejemplo de uso
# Generamos un mensaje con los datos especificados
data = "DATA"
source = "E"
destination = "A"
msg_id = "1730922753"
route = "D-B"
temp = 40
hum = 30

# Generar mensaje con checksum
message_with_checksum = generate_message(data, source, destination, msg_id, route, temp, hum)
print("Mensaje con checksum:", message_with_checksum)

# Verificar la integridad del mensaje
is_valid = verify_checksum(message_with_checksum)
print("¿El mensaje es válido?", is_valid)
