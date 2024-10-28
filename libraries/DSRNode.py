import time

class DSRNode:
    MAX_ATTEMPTS = 4          # Máximo de intentos de reenvío (20 segundos / 5 segundos)
    RETRY_INTERVAL = 5         # Intervalo de reintento en segundos
    TIMEOUT = 20               # Tiempo máximo de espera en segundos

    def __init__(self, node_id, lora, qos=-80, timestamp=20):
        self.node_id = node_id
        self.neighbors = set()  # Vecinos directos
        self.quality_neighbor = qos
        self.routing_table = {}  # Tabla de rutas: destino -> lista de saltos
        self.rreq_id = 0  # ID único para cada RREQ
        self.pending_rreqs = {}  # Solicitudes RREQ pendientes (ID -> destino)
        self.lora = lora  # Instancia de la clase LoRa
        self.timestamp_message = timestamp
        self.start_time = None
        self.rreq_attempts = 0  # Conteo de reintentos de RREQ
        self.echo = False

    def set_timestamp(self, seconds):
        self.timestamp_message = seconds

    def send_hello(self):
        """Envía un mensaje de hello para descubrir vecinos"""
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)
    
    def broadcast_rreq(self, destination):
        """Envía un mensaje RREQ a la red para descubrir rutas, con reintentos y control de expiración."""
        self.rreq_id = self.timestamp_message  # Genera un nuevo ID de RREQ
        self.pending_rreqs[self.rreq_id] = destination
        self.start_time = time.time()  # Marca el tiempo de inicio
        self._attempt_rreq(destination)

    def _attempt_rreq(self, destination):
        """Envía el RREQ y controla el reintento si no hay respuesta en 5 segundos."""
        elapsed_time = time.time() - self.start_time
        self.receive_message()
        if elapsed_time >= self.TIMEOUT:
            print(f"{self.node_id}: Tiempo de espera agotado para el nodo {destination}. No se encontró ruta.")
            self.pending_rreqs.pop(self.rreq_id, None)  # Elimina la solicitud pendiente
            return

        if self.rreq_attempts < self.MAX_ATTEMPTS:
            # Incrementa el contador de intentos y envía el RREQ
            self.rreq_attempts = self.timestamp_message
            rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}"
            self.lora.send(rreq_message)
            print(f"{self.node_id} reenvía RREQ intento {self.rreq_attempts} hacia {destination}")
            
            # Espera RETRY_INTERVAL y vuelve a intentar si no hay respuesta
            time.sleep(self.RETRY_INTERVAL)
            self._attempt_rreq(destination)
        else:
            print(f"{self.node_id}: Se agotaron los intentos para el nodo {destination}.")

    def send_rrep(self, source, message):
        """Envía un RREP al nodo origen por la ruta inversa"""
        print(f"{self.node_id} enviando RREP a {source}: {message}")
        self.lora.send(message)

    def receive_message(self):
        """Escucha la red y procesa los mensajes recibidos"""
        if self.lora.is_packet_received():
            message = self.lora.get_packet(rssi=True)
            print(f"{self.node_id} recibió mensaje: {message}")
            if message.get('payload').startswith("HELLO"):
                self.process_hello(message)
            elif message.get('payload').startswith("RREQ"):
                self.process_rreq(message.get('payload'))
            elif message.get('payload').startswith("RREP"):
                self.process_rrep(message.get('payload'))

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
        """Procesa un mensaje RREQ recibido"""
        try:
            _, source, destination, rreq_id = message.split(":")
            if destination == self.node_id:
                # Este nodo es el destino, enviar RREP
                print(f"{self.node_id} es el destino, enviando RREP a {source}")
                rrep_message = f"RREP:{self.node_id}:{source}:{rreq_id}"
                self.send_rrep(source, rrep_message)
            else:
                # Nodo intermedio, reenviar RREQ
                print(f"{self.node_id} reenvía RREQ: {message}")
                self.lora.send(message)
        except Exception as e:
            print(f"Error procesando RREQ: {e}")
    
    def process_rrep(self, message):
        """Procesa un mensaje RREP recibido"""
        try:
            _, destination, source, rrep_id, *route = message.split(":")
            
            # Agregar este nodo a la ruta
            route.append(self.node_id)
            
            if destination == self.node_id:
                # Este nodo es el origen, almacena la ruta completa en la tabla de rutas
                complete_route = route[::-1]  # La revertimos para que sea origen -> destino
                print(f"{self.node_id} almacena la ruta hacia {source}: {complete_route}")
                self.routing_table[source] = complete_route
                self.pending_rreqs.pop(int(rrep_id), None)  # Limpiar solicitud de RREQ
                self.echo = False
                self.rreq_attempts = 0  # Reinicia intentos
            else:
                # Nodo intermedio, reenviar RREP agregando este nodo a la ruta
                #route.append(self.node_id)
                #new_message = f"RREP:{destination}:{source}:{rrep_id}:{':'.join(route)}"
                #print(f"{self.node_id} reenvía RREP: {new_message}")
                #self.lora.send(new_message)
                pass
        except Exception as e:
            print(f"Error procesando RREP: {e}")
