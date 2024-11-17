import time
from machine import SoftSPI, Pin

class LoRa:
    def __init__(self, spi, cs_pin, reset_pin, dio0_pin):
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT)
        self.reset_pin = Pin(reset_pin, Pin.OUT)
        self.dio0 = Pin(dio0_pin, Pin.IN)
        
        # Configurar la interrupción en DIO0
        self.dio0.irq(trigger=Pin.IRQ_RISING, handler=self._irq_recv)
        
        # Bandera para indicar si se recibió un paquete
        self.packet_received = False
        # Variable para almacenar el contenido del paquete
        self.received_payload = None
        # Variable para almacenar el último paquete recibido (para detectar duplicados)
        self.last_payload = None
        # Variable para almacenar el RSSI del último paquete
        self.received_rssi = None
        
        # Timestamp para evitar recibir el mismo paquete dos veces
        self.last_receive_time = 0
        self.receive_delay = 2  # Retardo entre recepciones para evitar duplicados
        
        # Constantes de registros y modos
        self.REG_RSSI_VALUE = 0x1A
        self.RSSI_OFFSET = 157
        self.TX_BASE_ADDR = 0x00
        self.RX_BASE_ADDR = 0x00
        self.REG_FIFO = 0x00
        self.REG_OP_MODE = 0x01
        self.REG_FRF_MSB = 0x06
        self.REG_FRF_MID = 0x07
        self.REG_FRF_LSB = 0x08
        self.REG_PA_CONFIG = 0x09
        self.REG_LNA = 0x0c
        self.REG_FIFO_ADDR_PTR = 0x0d
        self.REG_FIFO_TX_BASE_ADDR = 0x0e
        self.REG_FIFO_RX_BASE_ADDR = 0x0f
        self.REG_FIFO_RX_CURRENT_ADDR = 0x10
        self.REG_IRQ_FLAGS = 0x12
        self.REG_RX_NB_BYTES = 0x13
        self.REG_PKT_RSSI_VALUE = 0x1a
        self.REG_PKT_SNR_VALUE = 0x1b
        self.REG_MODEM_CONFIG_1 = 0x1d
        self.REG_MODEM_CONFIG_2 = 0x1e
        self.REG_PREAMBLE_MSB = 0x20
        self.REG_PREAMBLE_LSB = 0x21
        self.REG_PAYLOAD_LENGTH = 0x22
        self.REG_MODEM_CONFIG_3 = 0x26
        self.REG_DETECTION_OPTIMIZE = 0x31
        self.REG_DETECTION_THRESHOLD = 0x37
        self.REG_SYNC_WORD = 0x39
        self.REG_DIO_MAPPING_1 = 0x40
        self.REG_VERSION = 0x42
        self.REG_PA_DAC = 0x4d
        self.IRQ_RX_DONE_MASK = 0x40
        self.MODE_RX_SINGLE = 0x06
        self.MODE_LORA = 0x80
        self.MODE_SLEEP = 0x00
        self.MODE_STDBY = 0x01
        self.MODE_TX = 0x03
        self.MODE_RX_CONTINUOUS = 0x05
        self.IRQ_TX_DONE_MASK = 0x08
        self.IRQ_PAYLOAD_CRC_ERROR_MASK = 0x20
        self.MAX_PKT_LENGTH = 255
        
        self.init_lora()

    def init_lora(self):    
        init_try = True
        re_try = 0
        self.cs.value(1)
        self.reset_lora()
        while init_try and re_try < 5:
            version = self.read_register(self.REG_VERSION)
            re_try = re_try + 1
            if version != 0:
                init_try = False
        if version != 0x12:
            raise Exception('Invalid version.') 
        self.set_mode_sleep()
        self.set_frequency(915E6)
        self.set_bandwidth(125000)
        self.set_spreading_factor(7)
        self.set_coding_rate(5)
        self.set_tx_power(17, use_pa_boost=True)
        self.write_register(self.REG_FIFO_TX_BASE_ADDR, self.TX_BASE_ADDR)
        self.write_register(self.REG_FIFO_RX_BASE_ADDR, self.RX_BASE_ADDR)
        self.write_register(self.REG_LNA, self.read_register(self.REG_LNA) | 0x03)
        self.write_register(self.REG_MODEM_CONFIG_3, 0x04)
        self.set_mode_standby()
        self.set_mode_rx_continuous()
        self.write_register(self.REG_DIO_MAPPING_1, 0x00)
        print("Lora Conectado")
    
    def send(self, data):
        self.set_mode_standby()
        self.write_register(self.REG_FIFO_ADDR_PTR, self.TX_BASE_ADDR)
        
        # Cargar el payload en el FIFO
        for byte in data:
            self.write_register(self.REG_FIFO, ord(byte))  # Convertir cada carácter a byte
        # Configurar la longitud del payload
        self.write_register(self.REG_PAYLOAD_LENGTH, len(data))
        # Cambiar al modo transmisión
        self.set_mode_tx()
        # Esperar hasta que la transmisión esté completa
        while not (self.read_register(self.REG_IRQ_FLAGS) & self.IRQ_TX_DONE_MASK):
            time.sleep(0.01)
        # Limpia la bandera de TxDone
        self.write_register(self.REG_IRQ_FLAGS, self.IRQ_TX_DONE_MASK)
        # print("Paquete transmitido.")
        # Volver al modo de recepción continua
        self.set_mode_rx_continuous()

    def _irq_recv(self, pin):
        self.check_for_packet()
        
    def check_for_packet(self):
        irq_flags = self.read_register(self.REG_IRQ_FLAGS)
        if irq_flags & self.IRQ_RX_DONE_MASK:
            current_addr = self.read_register(self.REG_FIFO_RX_CURRENT_ADDR)
            self.write_register(self.REG_FIFO_ADDR_PTR, current_addr)
            packet_length = self.read_register(self.REG_RX_NB_BYTES)
            payload = [self.read_register(self.REG_FIFO) for _ in range(packet_length)]
            payload_string = ''.join([chr(byte) for byte in payload])
            
            self.get_rssi()
            
            self.packet_received = True
            self.received_payload = payload_string
            self.last_payload = payload_string
            self.write_register(self.REG_IRQ_FLAGS, self.IRQ_RX_DONE_MASK)
            self.write_register(self.REG_IRQ_FLAGS, 0xFF)
        
    def set_mode_tx(self):
        self.write_register(self.REG_OP_MODE, self.MODE_LORA | self.MODE_TX)

    def set_mode_rx_continuous(self):
        self.write_register(self.REG_OP_MODE, self.MODE_LORA | self.MODE_RX_CONTINUOUS)

    def set_mode_sleep(self):
        self.write_register(self.REG_OP_MODE, self.MODE_LORA | self.MODE_SLEEP)

    def set_mode_standby(self):
        self.write_register(self.REG_OP_MODE, self.MODE_LORA | self.MODE_STDBY)

    def set_tx_power(self, power, use_pa_boost=False):
            if use_pa_boost:
                if power > 17:
                    power = 20
                    self.write_register(self.REG_PA_DAC, 0x87)
                else:
                    self.write_register(self.REG_PA_DAC, 0x84)
                power = max(2, min(power, 20))
                self.write_register(self.REG_PA_CONFIG, 0x80 | (power - 2))
            else:
                power = max(0, min(power, 14))
                self.write_register(self.REG_PA_CONFIG, 0x70 | power)
            
            # print(f"Potencia de transmisión configurada a {power} dBm {'con PA_BOOST' if use_pa_boost else 'sin PA_BOOST'}")

    def set_frequency(self, frequency):
        frf = int(frequency / 61.03515625)
        self.write_register(self.REG_FRF_MSB, (frf >> 16) & 0xFF)
        self.write_register(self.REG_FRF_MID, (frf >> 8) & 0xFF)
        self.write_register(self.REG_FRF_LSB, frf & 0xFF)

    def set_bandwidth(self, bw):
        bws = (7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000)
        i = 9
        for j in range(len(bws)):
            if bw <= bws[j]:
                i = j
                break
        x = self.read_register(self.REG_MODEM_CONFIG_1) & 0x0f
        self.write_register(self.REG_MODEM_CONFIG_1, x | (i << 4))

    def set_spreading_factor(self, sf):
        if sf < 6 or sf > 12:
            raise ValueError('Spreading factor must be between 6-12')
        self.write_register(self.REG_DETECTION_OPTIMIZE, 0xc5 if sf == 6 else 0xc3)
        self.write_register(self.REG_DETECTION_THRESHOLD, 0x0c if sf == 6 else 0x0a)
        reg2 = self.read_register(self.REG_MODEM_CONFIG_2)
        self.write_register(self.REG_MODEM_CONFIG_2, (reg2 & 0x0f) | ((sf << 4) & 0xf0))
        self.write_register(self.REG_MODEM_CONFIG_3, 0x08 if (sf > 10 and bw < 250000) else 0x00)

    def set_coding_rate(self, denom):
        denom = min(max(denom, 5), 8)
        cr = denom - 4
        reg1 = self.read_register(self.REG_MODEM_CONFIG_1)
        self.write_register(self.REG_MODEM_CONFIG_1, (reg1 & 0xf1) | (cr << 1))

    def write_register(self, reg, value):
        self.cs.value(0)
        self.spi.write(bytearray([reg | 0x80, value]))
        self.cs.value(1)

    def read_register(self, reg):
        self.cs.value(0)
        self.spi.write(bytearray([reg & 0x7F]))
        value = self.spi.read(1)
        self.cs.value(1)
        return value[0]

    def reset_lora(self):
        self.reset_pin.value(0)
        time.sleep(0.01)
        self.reset_pin.value(1)
        time.sleep(0.01)
    # Método para verificar si llegó un paquete
    def is_packet_received(self):
        return self.packet_received
    
    def get_rssi(self):
        rssi_value = self.read_register(self.REG_RSSI_VALUE)
        self.received_rssi  = rssi_value - self.RSSI_OFFSET  
        return self.received_rssi 

    # Método para obtener el contenido del paquete recibido
    def get_packet(self,rssi=False):
        if self.packet_received:
            if rssi:
                packet_info = {
                "rssi": self.received_rssi,
                "payload": self.received_payload
                }
            else:
                packet_info = {
                "payload": self.received_payload
                }
            self.packet_received = False  # Reiniciar la bandera
            self.received_payload = None  # Limpiar el payload
            self.received_rssi = None  # Limpiar el valor de RSSI
            return packet_info
        else:
            return None
