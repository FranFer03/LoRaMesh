

class DSRNode:
    MAX_ATTEMPTS = 4
    RETRY_INTERVAL = 5
    TIMEOUT = 20   
    def __init__(self, node_id, lora,timer, qos=-80, timestamp=20):
        self.neighbors = set()
        self.rreq_id = 0
        self.pending_rreqs = {}
        self.routes = []
        self.node_id = node_id
        self.quality_neighbor = qos
        self.lora = lora 
        self.timestamp_message = timestamp        
        self.start_time = None
        self.timer = timer
        self.time_pending_rreqs = 0

        self.timer.init(mode=self.timer.ONE_SHOT, period=1, callback=self.set_times)
    
    @property
    def get_neighbors(self):
        return print(f"Vecinos proximos: {self.neighbors}")
    
    @property
    def get_routes(self):
        return print(f"Rutas disponibles: {self.routes}")

    def set_times(self):
        self.time_pending_rreqs += 1
        if self.time_pending_rreqs // 60:
            pass

    def set_timestamp(self, seconds):
        self.timestamp_message = seconds

    def send_hello(self):
        """Envía un mensaje de hello para descubrir vecinos"""
        hello_message = f"HELLO:{self.node_id}"
        print(f"{self.node_id} enviando mensaje HELLO")
        self.lora.send(hello_message)

    def broadcast_rreq(self, destination):
        """Envía un mensaje RREQ a la red para descubrir rutas, con reintentos y control de expiración."""
        self.rreq_id = self.timestamp_message
        rreq_message = f"RREQ:{self.node_id}:{destination}:{self.rreq_id}"
        self.pending_rreqs[self.rreq_id] = ["RREQ",self.node_id,destination]
        self.lora.send(rreq_message)

    def send_rrep(self, source,id_message):
        """Envía un RREP al nodo origen por la ruta inversa"""
        print(f"{self.node_id} enviando RREP a {source}: {id_message}")
        rrep_message = f"RREP:{self.node_id}:{source}:{id_message}"
        self.lora.send(rrep_message)

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
                if rreq_id in self.pending_rreqs.keys:
                    print(f"{self.node_id} es el destino, enviando RREP a {source}")
                    self.pending_rreqs[self.rreq_id] = ["RREQ",self.node_id,destination]
                    self.send_rrep(source,rreq_id)
            else:
                # Nodo intermedio, reenviar RREQ
                if not rreq_id in self.pending_rreqs.keys :
                    print(f"{self.node_id} reenvía RREQ: {message}")
                    self.pending_rreqs(rreq_id) = ["RREQ",source]
                    self.lora.send(message)
                else:
                    print("Mensaje ya reenviado")
        except Exception as e:
            print(f"Error procesando RREQ: {e}")
    
    def process_rrep(self, message):
        """Procesa un mensaje RREP recibido RREP:{self.node_id}:{source}:{id_message}"""
        try:
            _, source, destination, rrep_id = message.split(":")
            
            if destination == self.node_id:
                self.pending_rreqs.pop(int(rrep_id), None)
                self.echo = False
                self.rreq_attempts = 0
                pass
        except Exception as e:
            print(f"Error procesando RREP: {e}")