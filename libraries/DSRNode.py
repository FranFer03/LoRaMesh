import time
from machine import Timer
import random
class DSRNode:
    MAX_ATTEMPTS = 2
    RETRY_INTERVAL = 5
    TIMEOUT = 20
    CACHE_TIMEOUT = 60   

    def __init__(self, node_id, lora, rtc, timer, qos=-80, role="slave"):
        self.neighbors = set()
        self.neighbors.add("A")
        self.neighbors.add("B")
        self.rreq_id = 0
        self.query = {
            "RREQ": [],
            "RREP": [],
            "DATA": [],
            "RESP": []
        }
        self.waiting_response = False
        self.routes = {}
        self.node_id = node_id
        self.quality_neighbor = qos
        self.lora = lora
        self.timestamp_message = 0        
        self.start_time = None
        self.rtc = rtc
        self.timer = timer
        self.time_pending_rreqs = []
        self.current_time = None
        self.role = role 
        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.set_timestamp)
        if self.role == "master":
            print(f"Node {self.node_id} is operating as master.")

        elif self.role == "slave":
            print(f"Node {self.node_id} is operating as slave.")


    def set_timestamp(self, timer):
        rtc_time = self.rtc.datetime()
        # Crear una tupla para `mktime`: (Año, Mes, Día, Hora, Minuto, Segundo, Día de la semana, Día del año, Horario de verano)
        t = (rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[4], rtc_time[5], rtc_time[6], 0, 0, 0)
        self.timestamp_message = time.mktime(t)

    @property
    def get_neighbors(self):
        return print(f"Vecinos proximos: {self.neighbors}")
    
    @property
    def get_routes(self):
        return print(f"Rutas disponibles: {self.routes}")

    def remove_query(self,command, element):
        try:
            # Filtrar las sublistas que contienen el elemento y eliminarlas
            initial_len = len(self.query[command])
            self.query[command] = [sublist for sublist in self.query[command] if element not in sublist]
            
            # Verificar si se eliminó alguna sublista
            if len(self.query[command]) < initial_len:
                print(f"La orden con el '{element}' ha sido exitosamente eliminada del comando '{command}'.")
            else:
                print(f"No se encuentra el self.query con el elemento '{element}'.")
        except KeyError:
            print(f"No existe el comando '{command}' en el diccionario.")
    
    def cache_cleaning(self):
        for z, i in enumerate(self.query["RREQ"][:]):
            if self.timestamp_message - int(i[0]) >= self.CACHE_TIMEOUT:
                print(f"No se encuentra el nodo {i[2]} por lo tanto se ha eliminado de la query el ID {i[0]}")             
                self.query["RREQ"].remove(i)
        for z, i in enumerate(self.query["RREP"][:]):
            if self.timestamp_message - int(i[0]) >= self.CACHE_TIMEOUT:
                self.query["RREP"].remove(i)

    def calculate_checksum(self,message):
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
    def verify_checksum(self, message_with_checksum):
        # Separar el mensaje y el checksum
        *message_parts, received_checksum = message_with_checksum.rsplit(":", 1)
        message = ":".join(message_parts)
        
        # Calcular el checksum nuevamente
        calculated_checksum = self.calculate_checksum(message)
        
        # Comparar checksums
        return int(received_checksum) == calculated_checksum


    def send_hello(self):
        """Envía un mensaje de hello para descubrir vecinos"""
        self.neighbors = set()
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)
    
    def send_response(self,destination,id_response, routelist):
        """Responde a la solicitud de datos al nodo origen"""
        temp = random.uniform(50,100)
        humidity = random.uniform(0,100)
        data_message_raw = f"RESP:{self.node_id}:{destination}:{id_response}:{routelist}:{temp},{humidity}"
        checksum = self.calculate_checksum(data_message_raw)
        data_message = f"{data_message_raw}:{checksum}"
        self.lora.send(data_message)

        #AGREGAR WAITING FOR RESPONSE Y TERMINAR LOGICA DE UDP

    def broadcast_rreq(self, destination):
        """Envía un mensaje RREQ a la red para descubrir rutas, con reintentos y control de expiración."""
        self.rreq_id = self.timestamp_message
        rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}:"
        #self.time_pending_rreqs.append(time.time())
        self.query["RREQ"] = [str(self.rreq_id),self.node_id,destination]
        self.lora.send(rreq_message)

    def send_rrep(self, destination,id_message,routes):
        """Envía un RREP al nodo origen por la ruta inversa"""
        print(f"{self.node_id} envia RREP a {destination}: {id_message}: {'-'.join(routes)}")
        rrep_message = f"RREP:{self.node_id}:{destination}:{id_message}:{'-'.join(routes)}"
        self.query["RREP"].append([id_message, self.node_id, destination])
        self.lora.send(rrep_message)

    def request_data(self, destination):
        """Envía una peticion de datos al nodo destino"""
        if destination in self.routes.keys():
            print(f"{self.node_id} enviando solicitud de datos a {destination} a través de la ruta {self.routes[destination]}")
            data_message = f"DATA:{self.node_id}:{destination}:{self.timestamp_message}:{'-'.join(self.routes[destination])}"
            
            # Registrar el mensaje en la consulta
            self.query["DATA"].append([self.timestamp_message, self.node_id, destination])
            
            # Enviar mensaje de datos a través de LoRa
            self.lora.send(data_message)
            self.waiting_response = True
            self.waiting_for_response(destination, data_message)
        else:
            print(f"{self.node_id} no se puede enviar DATA a {destination} porque no hay ruta disponible.")
            
            # Enviar un mensaje de solicitud de ruta (RREQ)
            self.broadcast_rreq(destination)

    def waiting_for_response(self, objetive, message):
        """Espera la respuesta del nodo esclavo y reenvía la solicitud si no lo recibe en el tiempo esperado."""
        attempts = 1
        while self.waiting_response:
            if self.timestamp_message - int(self.query["DATA"][0][0]) <= 30 and attempts <= self.MAX_ATTEMPTS:  
                # Reenvío del mensaje después de 15 segundos
                if self.timestamp_message - int(self.query["DATA"][0][0]) > 15 and attempts < self.MAX_ATTEMPTS:
                    self.lora.send(message)
                    attempts += 1
                    print(f"{self.node_id} reenviando mensaje de solicitud de datos {self.query['DATA'][0][0]}")
                
                # Verificar si se ha recibido un paquete
                if self.lora.is_packet_received():
                    message = self.lora.get_packet(rssi=False)
                    # Procesar mensaje de RESP si se recibe
                    if message.get('payload').startswith("RESP"):
                        if self.verify_checksum(message.get('payload')):
                            sequence, source, destination, data_id, routelist, sensors_data, checksum = message.get('payload').split(":")
                            if destination == self.node_id and data_id == self.query["DATA"][0][0]:
                                print(f"{self.node_id} recibió respuesta de la petición {data_id} con los datos {sensors_data}")
                                self.waiting_response = False
                            else:
                                print(f"{self.node_id} recibío una peticion distinta a {self.query['DATA'][0][0]}. Recibiendo la solicitud {data_id}")
                        else:
                            print(f"{self.node_id} no recibió un checksum correcto")
                    else:
                        print(f"{self.node_id} recibió un mensaje de otro tipo que no es RESP")        
            else:
                # No se recibió respuesta, ruta caida
                print(f"{self.node_id} no recibió respuesta para la petición {self.query['DATA'][0][0]} por lo tanto la ruta está caída")
                self.routes.pop(objetive)
                self.waiting_response = False

    def receive_message(self):
        """Escucha la red y procesa los mensajes recibidos según el tipo de mensaje (HELLO, RREQ, RREP, DATA)."""
        if self.lora.is_packet_received():
            message = self.lora.get_packet(rssi=True)
            print(f"{self.node_id} recibió mensaje: {message}")
            # Procesar diferentes tipos de mensajes
            if message.get('payload').startswith("HELLO"):
                self.process_hello(message)
            elif message.get('payload').startswith("RREQ"):
                self.process_rreq(message)
            elif message.get('payload').startswith("RREP"):
                self.process_rrep(message.get('payload'))
            elif message.get('payload').startswith("DATA"):
                self.process_data(message)
            elif message.get('payload').startswith("RESP"):
                self.process_response(message)

    def process_hello(self, message):
        """Procesa un mensaje HELLO recibido y agrega al nodo a la lista de vecinos"""
        try:
            _, neighbor_id = message.get("payload").split(":")
            if neighbor_id != self.node_id and int(message.get("rssi")) > self.quality_neighbor:
                if neighbor_id not in self.neighbors:
                    self.neighbors.add(neighbor_id)
                    print(f"{self.node_id} descubrió al vecino {neighbor_id}")
        except Exception as e:
            print(f"Error procesando HELLO: {e}")
    
    def process_rreq(self, message):
        try:
            sequence, source, destination, rreq_id, routelist = self.extract_message_data(message)
            if not routelist:
                print("Estoy vacia")
                self.process_empty_routelist(sequence, source, destination, rreq_id)
            else:
                print("Tengo algo")
                self.process_non_empty_routelist(sequence, source, destination, rreq_id, routelist)
        
        except Exception as e:
            print(f"Error procesando RREQ: {e}")

    def extract_message_data(self, message):
        """Extrae y descompone los datos del mensaje RREQ."""
        sequence, source, destination, rreq_id, route = message.get('payload').split(":")
        routelist = route.split("-") if route else []
        return sequence, source, destination, rreq_id, routelist

    def process_empty_routelist(self, sequence, source, destination, rreq_id):
        """Procesa el RREQ cuando la lista de ruta está vacía."""

        if source in self.neighbors:
            if destination == self.node_id:
                print(f"Ahh...soy yo wey {self.node_id} es el destino, enviando RREP a {source}")
                self.send_rrep_with_routelist(source, rreq_id, [])
            else:
                self.relay_rreq_if_needed(sequence, source, destination, rreq_id, [])

    def process_non_empty_routelist(self, sequence, source, destination, rreq_id, routelist):
        """Procesa el RREQ cuando la lista de ruta no está vacía."""
        if routelist[-1] in self.neighbors:
            if destination == self.node_id:
                print(f"Ahh...soy yo wey {self.node_id} es el destino, enviando RREP a {source}")
                self.send_rrep_with_routelist(source, rreq_id, routelist)
            else:
                self.relay_rreq_if_needed(sequence, source, destination, rreq_id, routelist)
        else:
            print(f"El mensaje RREQ no fue recibido por un vecino")

    def send_rrep_with_routelist(self, source, rreq_id, routelist):
        """Envía un mensaje RREP invirtiendo la ruta."""
        routelist.reverse()
        self.query["RREQ"].append([rreq_id, source, self.node_id])
        self.send_rrep(source, rreq_id, routelist)

    def relay_rreq_if_needed(self, sequence, source, destination, rreq_id, routelist):
        """Reenvía el RREQ si aún no ha sido procesado."""
        if not [rreq_id, source, destination] in self.query["RREQ"]:
            routelist.append(self.node_id)
            finalmessage = f"{sequence}:{source}:{destination}:{rreq_id}:{'-'.join(routelist)}"
            print(f"Nodo intermedio: {self.node_id} reenvía RREQ: {finalmessage}")
            self.query["RREQ"].append([rreq_id, source, destination])
            self.lora.send(finalmessage)
    
    def process_rrep(self, message):
        """Procesa un mensaje RREP recibido """
        try:
            sequence, source, destination, rrep_id, route = message.split(":")
            routelist = split("-") if route else []

            if destination == self.node_id:
                routelist.reverse()
                print(f"Volvistee wey. La ruta hacia {source} es {routelist}")
                self.routes[source] = routelist
                self.remove_query("RREQ",rrep_id)

            else:
                # Nodo intermedio, reenviar RREP si no fue procesado ya
                if self.node_id in routelist:
                    if not [rrep_id, source, destination] in self.query["RREP"]:
                        print(f"Nodo de camino inverso: {self.node_id} reenvía RREP: {message}")
                        self.query["RREP"].append([rrep_id, source, destination])
                        self.lora.send(message)
                    else:
                        print("Mensaje ya reenviado")
                else:
                    pass
        except Exception as e:
            print(f"Error procesando RREP: {e}")
    
    def process_data(self, message):
        """Procesa un mensaje DATA recibido """
        try:
            sequence, source, destination, data_id, routelist = self.extract_message_data(message)

            if destination == self.node_id:
                routelist.reverse()
                self.routes[source] = routelist
                self.send_response(source, data_id, routelist)

            else:
                # Nodo intermedio, reenviar DATA si no fue procesado ya
                if self.node_id in routelist:
                    if not [data_id, source, destination] in self.query["DATA"]:
                        print(f"Nodo de transicion: {self.node_id} reenvía DATA: {message.get('payload')}")
                        self.query["DATA"].append([data_id, source, destination])
                        self.lora.send(message.get('payload'))
                    else:
                        print("Mensaje ya reenviado")
                else:
                    pass
        except Exception as e:
            print(f"Error procesando RREP: {e}")

    def process_response(self, message):
        """Procesa un mensaje RESP recibido """
        try:
            sequence, source, destination, data_id, routelist, sensors, checksum = message.get('payload').split(":")
            routelist = routelist.split("-")
            if not destination == self.node_id:
                if self.node_id in routelist:
                    if not [data_id, source, destination] in self.query["RESP"]:
                        self.query["RESP"].append([data_id, source, destination])
                        self.lora.send(message.get('payload'))
                        print(f"Nodo de transicion: {self.node_id} reenvía RESP: {message.get('payload')}")
                    else:
                        pass             
                else:
                    pass
        except Exception as e:
            print(f"Error procesando RESP: {e}")
