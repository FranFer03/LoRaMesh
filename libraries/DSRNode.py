import time
from machine import Timer

class DSRNode:
    MAX_ATTEMPTS = 2
    RETRY_INTERVAL = 5
    TIMEOUT = 20
    CACHE_TIMEOUT = 60   

    def __init__(self, node_id, lora, rtc, timer, qos=-80):
        self.neighbors = set()
        self.rreq_id = 0
        self.query = {
            "RREQ": [],
            "RREP": [],
            "DATA": []
        }
        self.waiting_ack = False
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
        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.set_timestamp)

    def set_timestamp(self, timer):
        # Obtener la fecha y hora actual del RTC
        rtc_time = self.rtc.datetime()
        
        # Crear una tupla para `mktime`: (Año, Mes, Día, Hora, Minuto, Segundo)
        t = (rtc_time[0], rtc_time[1], rtc_time[2], rtc_time[3], rtc_time[4], rtc_time[5])
        
        # Convertir a tiempo Unix y asignarlo a `timestamp_message`
        self.timestamp_message = time.mktime(t)

    @property
    def get_neighbors(self):
        return print(f"Vecinos proximos: {self.neighbors}")
    
    @property
    def get_routes(self):
        return print(f"Rutas disponibles: {self.routes}")

    def remove_query(self, command, element):
        try:
            # Filtramos sublistas que contengan el elemento y las eliminamos
            initial_len = len(self.query[command])
            self.query[command] = [sublist for sublist in self.query[command] if element not in sublist]
            
            # Verificar si se eliminó alguna sublista
            if len(self.query[command]) < initial_len:
                print(f"Elemento '{element}' eliminado exitosamente del comando '{command}'.")
            else:
                print(f"No se encuentra el query con el elemento '{element}'.")
                
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

    def send_hello(self):
        """Envía un mensaje de hello para descubrir vecinos"""
        self.neighbors = set()
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)
    
    def send_ack(self,source,id_req):
        #Agregar logica para reenviar mensaje
        ack_message = f"ACK:{self.node_id}:{source}:{id_req}"
        print(f"{self.node_id} envio ACK para {source} por request {id_req}")
        self.lora.send(ack_message)

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

    def send_data(self, destination):
        """
        Envía un mensaje de datos a un nodo destino a través de la ruta especificada.
        Si no hay ruta disponible, envía un mensaje de solicitud de ruta (RREQ).
        """
        if destination in self.routes.keys():
            print(f"{self.node_id} enviando DATA a {destination} a través de la ruta {self.routes[destination]}")
            data_message = f"DATA:{self.node_id}:{destination}:{self.timestamp_message}:{'-'.join(self.routes[destination])}"
            
            # Registrar el mensaje en la consulta
            self.query["DATA"].append([self.timestamp_message, self.node_id, destination])
            
            # Enviar mensaje de datos a través de LoRa
            self.lora.send(data_message)
            self.waiting_ack = True
            self.waiting_for_ack(destination, data_message)
        else:
            print(f"{self.node_id} no se puede enviar DATA a {destination} porque no hay ruta disponible.")
            
            # Enviar un mensaje de solicitud de ruta (RREQ)
            self.broadcast_rreq(destination)

    def waiting_for_ack(self, objetive, message):
        """
        Espera el ACK (reconocimiento) de un mensaje enviado y reenvía si no lo recibe en el tiempo esperado.
        """
        attempts = 1
        while self.waiting_ack:
            if self.timestamp_message - int(self.query["DATA"][0][0]) <= 30 and attempts <= self.MAX_ATTEMPTS:
                
                # Reenvío del mensaje después de 15 segundos
                if self.timestamp_message - int(self.query["DATA"][0][0]) == 15 and attempts < self.MAX_ATTEMPTS:
                    self.lora.send(message)
                    attempts += 1
                
                # Verificar si se ha recibido un paquete
                if self.lora.is_packet_received():
                    message = self.lora.get_packet(rssi=True)
                    
                    # Procesar mensaje de ACK si se recibe
                    if message.get('payload').startswith("ACK"):
                        sequence, source, destination, data_id, routelist = self.extract_message_data(message)
                        if destination == self.node_id and data_id == self.query["DATA"][0][0]:
                            print(f"{self.node_id} recibió ACK para la petición {data_id}")
                            self.waiting_ack = False
            else:
                # Si no se recibe ACK, la ruta se considera caída
                print(f"{self.node_id} no recibió ACK para la petición {self.query['DATA'][0][0]} por lo tanto la ruta está caída")
                self.routes.pop(objetive)
                self.waiting_ack = False

    def receive_message(self):
        """
        Escucha la red y procesa los mensajes recibidos según el tipo de mensaje (HELLO, RREQ, RREP, DATA).
        """
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
                self.forward_data(message)

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
                self.process_empty_routelist(sequence, source, destination, rreq_id)
            else:
                self.process_non_empty_routelist(sequence, source, destination, rreq_id, routelist)
        
        except Exception as e:
            print(f"Error procesando RREQ: {e}")

    def extract_message_data(self, message):
        """Extrae y descompone los datos del mensaje RREQ."""
        sequence, source, destination, rreq_id, *route = message.get('payload').split(":")
        routelist = route[0].split("-") if route else []
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
            sequence, source, destination, rrep_id, *route = message.split(":")
            routelist = route[0].split("-")

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
    
    def forward_data(self, message):
        """Procesa un mensaje DATA recibido """
        try:
            sequence, source, destination, data_id, routelist = self.extract_message_data(message)

            if destination == self.node_id:
                #Completar envio de ACK
                routelist.reverse()
                print(f"Volvistee wey. La ruta hacia {source} es {routelist}")
                self.routes[source] = routelist
                self.send_ack()

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