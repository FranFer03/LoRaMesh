# 🌐 Red Mesh LoRa para Monitoreo en Áreas Remotas

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![MicroPython](https://img.shields.io/badge/MicroPython-ESP32-green.svg)](https://micropython.org/)

---

## 🌟 Introducción

En muchas áreas rurales y remotas, las soluciones de comunicación tradicionales como Wi-Fi o redes de datos móviles enfrentan limitaciones significativas relacionadas con la infraestructura, el alcance y el costo. Este proyecto aborda estas problemáticas mediante el uso de **LoRa** (Long Range) combinado con una **red mesh** basada en el protocolo **DSR** (Dynamic Source Routing).

### 🎯 Aplicaciones

- 🌱 **Monitoreo ambiental**: Calidad del aire, temperatura, humedad
- 🌾 **Agricultura inteligente**: Seguimiento de cultivos en grandes extensiones
- 🌳 **Gestión de recursos naturales**: Vigilancia en áreas protegidas
- 🏭 **IoT Industrial**: Sensores distribuidos en plantas de producción

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

#### 1. **Nodos Esclavos** 📡

- **Hardware**: ESP32 + Módulo LoRa SX1276/SX1278
- **Sensores**: DS18B20 (temperatura), GPS, sensores ambientales
- **Función**: Recolectan datos y participan en el enrutamiento mesh

#### 2. **Nodos Maestros** 🖥️

- **Master API**: Centraliza datos y los envía via WiFi a servidores web
- **Función**: Gateway entre la red mesh y servicios externos

#### 3. **Protocolo DSR** 🔄

- **Descubrimiento de rutas**: RREQ (Route Request) / RREP (Route Reply)
- **Transmisión de datos**: DATA / RESP con verificación de integridad
- **Mantenimiento**: Detección automática de rutas caídas y re-enrutamiento

---

## 🗂️ Estructura del Proyecto

```
LoRaMesh/
├── firmware/
│   ├── master_api/         # Nodo maestro con API REST
│   │   └── SOFWARE/
│   │       ├── main.py     # Código principal
│   │       ├── config.py   # Configuración de pines y constantes
│   │       └── DSRNode.py  # Implementación del protocolo DSR
│   ├── master_mqtt/        # Nodo maestro con MQTT
│   │   ├── HARDWARE/       # Configuración para SPI hardware
│   │   └── SOFWARE/        # Configuración para SoftSPI
│   └── slave/              # Nodos esclavos con sensores
│       ├── HARDWARE/
│       └── SOFTWARE/
├── libraries/              # Librerías compartidas
│   ├── LoRa.py            # Driver para módulos LoRa
│   ├── DSRNode.py         # Implementación base del protocolo DSR
│   ├── MicropyGPS.py      # Parser para módulos GPS
│   └── mqttsimple.py      # Cliente MQTT ligero
├── bocetos/               # Diagramas y esquemas del sistema
├── requirements.txt       # Dependencias Python
└── README.md
```

---

## ⚙️ Configuración e Instalación

### 1. Preparación del Hardware

#### ESP32 + LoRa (SX1276/SX1278)

```
ESP32    | LoRa Module
---------|------------
GPIO5    | SCK
GPIO27   | MOSI
GPIO19   | MISO
GPIO18   | CS
GPIO14   | RST
GPIO26   | DIO0
3.3V     | VCC
GND      | GND
```

#### Sensores Adicionales

- **DS18B20**: GPIO12 (temperatura)
- **GPS**: UART2, RX=GPIO16 (coordenadas)

### 2. Software

#### Dependencias Python

```bash
pip install -r requirements.txt
```

#### Configuración de Nodos

Edita `firmware/master_api/SOFWARE/config.py`:

```python
# Identificación del nodo
NODE_ID = 1

# Configuración WiFi
WIFI_SSID = "TU_SSID"
WIFI_PASSWORD = "TU_PASSWORD"

# Configuración LoRa
LORA_QOS = -90  # Umbral RSSI para vecinos
SPI_SCK_PIN = 5
SPI_MOSI_PIN = 27
SPI_MISO_PIN = 19
LORA_CS_PIN = 18
LORA_RST_PIN = 14
LORA_DIO0_PIN = 26

# Configuración de tiempo
MAX_TIME_SYNC_ATTEMPTS = 5
API_TIME_URL = "http://worldtimeapi.org/api/timezone/America/Argentina/Buenos_Aires"
```

---

## 🚀 Uso del Sistema

### 1. Despliegue de la Red

#### Configurar Nodo Maestro

1. Cargar firmware desde `firmware/master_api/SOFWARE/main.py`
2. Configurar credenciales WiFi en `config.py`
3. El nodo sincronizará automáticamente el tiempo y comenzará a anunciar su presencia

#### Configurar Nodos Esclavos

1. Cargar firmware desde `firmware/slave/SOFTWARE/main.py`
2. Asignar ID único a cada nodo
3. Los nodos comenzarán a descubrir vecinos automáticamente

### 2. Protocolo de Comunicación

#### Descubrimiento de Rutas

```
Nodo A → RREQ:A:C:12345: → Broadcast
Nodo B → RREQ:A:C:12345:B → Reenvío
Nodo C → RREP:C:A:12345:B → Respuesta con ruta
```

#### Solicitud de Datos

```
Nodo A → DATA:A:C:67890:B → Solicitud via ruta conocida
Nodo C → RESP:C:A:67890:B:temp=25.3,hum=60.2:CRC → Respuesta con datos
```

### 3. Comandos MQTT (Nodo Master MQTT)

Envía comandos al tópico `{NODE_ID}/commands`:

- `VECINOS`: Lista vecinos detectados
- `CAMINOS`: Muestra tabla de enrutamiento
- `DESTINO/{ID}`: Descubre ruta hacia nodo ID
- `DATOS/{ID}`: Solicita datos del nodo ID
- `TIEMPO`: Muestra timestamp actual

---

## 📊 Monitoreo y Debugging

### Logs del Sistema

```python
# Ejemplo de salida del nodo maestro
Conexión Wi-Fi establecida! IP: 192.168.1.100
Hora sincronizada en el RTC.
Node 1 descubrió al vecino B
1 enviando solicitud de datos a C a través de la ruta ['B', 'C']
1 recibió respuesta de la petición 67890 con los datos 25.3,60.2
```

### Métricas de Red

- **RSSI**: Calidad de señal entre nodos (umbral configurable)
- **Latencia**: Tiempo de respuesta extremo a extremo
- **Confiabilidad**: Tasa de entrega exitosa de mensajes
- **Topología**: Visualización automática de conexiones

---

## 🔧 Características Técnicas

### Protocolo DSR Implementado

- ✅ **Route Discovery**: RREQ/RREP con prevención de loops
- ✅ **Data Transmission**: DATA/RESP con checksums
- ✅ **Route Maintenance**: Detección automática de enlaces caídos
- ✅ **Cache Management**: Limpieza automática de entradas antiguas
- ✅ **QoS Support**: Filtrado por calidad de señal (RSSI)

### Características LoRa

- **Frecuencia**: 915 MHz (configurable)
- **Potencia**: Hasta +20 dBm
- **Alcance**: 2-15 km (según condiciones)
- **Velocidad**: 1.2 - 50 kbps (configurable)
- **Consumo**: < 50 mA en transmisión

### Integración de Sensores

- **Temperatura**: DS18B20 (precisión ±0.5°C)
- **GPS**: Coordenadas con precisión < 5m
- **Extensible**: Soporte para I2C, SPI, UART

---

## 🧪 Pruebas y Validación

### Escenarios de Prueba

1. **Red lineal**: A ↔ B ↔ C ↔ D
2. **Red en malla**: Múltiples rutas entre nodos
3. **Pérdida de enlaces**: Recuperación automática
4. **Escalabilidad**: Hasta 10+ nodos simultáneos

### Resultados Esperados

- **Latencia promedio**: < 5 segundos
- **Tasa de entrega**: > 95% en condiciones normales
- **Tiempo de recuperación**: < 30 segundos ante fallos

---

## 📚 Documentación Técnica

### Clases Principales

#### `DSRNode`

```python
class DSRNode:
    """
    Implementa un nodo para una red mesh basada en el protocolo DSR
    usando LoRa como medio de comunicación.
    """
    def __init__(self, node_id, lora, rtc, timer, qos=-80, role="slave"):
        # Inicialización del nodo DSR

    def send_hello(self):
        # Envía mensaje HELLO para anunciar presencia

    def broadcast_rreq(self, destination):
        # Descubre rutas hacia un destino

    def request_data(self, destination):
        # Solicita datos de un nodo específico
```

#### `LoRa`

```python
class LoRa:
    """
    Driver para módulos LoRa SX1276/SX1278
    """
    def __init__(self, spi, cs_pin, reset_pin, dio0_pin):
        # Configuración del módulo LoRa

    def send(self, message):
        # Transmite un mensaje

    def get_packet(self, rssi=False):
        # Recibe un mensaje con información RSSI opcional
```

### Formato de Mensajes

#### HELLO

```
HELLO:{node_id}
```

#### RREQ (Route Request)

```
RREQ:{source}:{destination}:{rreq_id}:{route_list}
```

#### RREP (Route Reply)

```
RREP:{source}:{destination}:{rreq_id}:{route_list}
```

#### DATA

```
DATA:{source}:{destination}:{data_id}:{route_list}
```

#### RESP (Response)

```
RESP:{source}:{destination}:{data_id}:{route_list}:{sensor_data}:{checksum}
```

---

## 🛠️ Desarrollo y Contribución

### Configuración del Entorno de Desarrollo

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/LoRaMesh.git
cd LoRaMesh

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Guías de Contribución

1. Fork del repositorio
2. Crear branch para nueva funcionalidad
3. Implementar cambios con tests
4. Documentar nuevas características
5. Enviar Pull Request

---

## 🐛 Troubleshooting

### Problemas Comunes

#### No se detectan vecinos

- Verificar conexiones SPI y alimentación del módulo LoRa
- Comprobar que ambos nodos usen la misma frecuencia
- Ajustar umbral QoS si la señal es débil

#### Rutas no se mantienen

- Verificar sincronización de tiempo entre nodos
- Ajustar intervalos de timeout en DSRNode
- Comprobar interferencias en el canal LoRa

#### Errores de checksum

- Verificar integridad de conexiones SPI
- Comprobar que no hay interferencias electromagnéticas
- Verificar alimentación estable del ESP32

---

## 👨‍🎓 Sobre Nosotros

**Francisco Fernández**

- 🎓 Estudiante de Ingeniería Electrónica - UTN FRT
- 💼 [LinkedIn](https://linkedin.com/in/franfer0301)

**Nahuel Ontivero**

- 🎓 Estudiante de Ingeniería Electrónica - UTN FRT
- 💼 [LinkedIn](https://linkedin.com/in/nahuel-ontivero-5790871b7/)
