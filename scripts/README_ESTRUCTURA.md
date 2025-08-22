# Generador de Datos Sintéticos - Estructura Segmentada

## Descripción

Este sistema genera datos sintéticos realistas para sensores IoT en el proyecto LoRaMesh. El código ha sido segmentado en múltiples módulos para facilitar el mantenimiento y la extensibilidad.

## Estructura de Archivos

### Archivos Principales

#### `upload_data.py`

**Punto de entrada principal del sistema**

- Configuración de la base de datos
- Inicialización y coordinación de todos los componentes
- Función main() simplificada

#### `config.py`

**Configuración y estructuras de datos**

- `DatabaseConfig`: Configuración de conexión a la base de datos
- `SensorPattern`: Definición de patrones de comportamiento de sensores
- `SensorPatterns`: Patrones específicos para cada tipo de sensor
- Constantes del sistema (modelos de dispositivos, tipos de sensores)

#### `database_manager.py`

**Gestor de conexión y operaciones de base de datos**

- Conexión/desconexión a MySQL
- Configuración inicial de datos (nodos y sensores)
- Operaciones CRUD básicas
- Inserción por lotes de mediciones
- Consultas de estadísticas

#### `data_generator.py`

**Generador de valores sintéticos realistas**

- Algoritmos de generación de datos basados en patrones
- Simulación de variaciones estacionales y temporales
- Aplicación de límites por tipo de sensor
- Generación de ruido realista

#### `historical_data_generator.py`

**Generador de datos históricos**

- Generación de datos para períodos pasados
- Gestión de intervalos de tiempo basados en refresh_rate
- Procesamiento por lotes para eficiencia
- Logging detallado del progreso

#### `realtime_data_generator.py`

**Generador de datos en tiempo real**

- Simulación de datos en tiempo real
- Control de intervalos de generación
- Gestión de interrupciones por usuario
- Mediciones probabilísticas por nodo

#### `statistics_reporter.py`

**Generador de reportes y estadísticas**

- Estadísticas de registros por tabla
- Análisis de mediciones por tipo de sensor
- Formato de salida organizado
- Rangos temporales de datos

#### `user_interface.py`

**Interfaz de línea de comandos**

- Menú interactivo principal
- Validación de entrada del usuario
- Coordinación entre todos los módulos
- Manejo de errores y interrupciones

## Ventajas de la Segmentación

### 1. **Separación de Responsabilidades**

- Cada módulo tiene una función específica y bien definida
- Facilita la localización y corrección de errores
- Permite modificar funcionalidades sin afectar otros componentes

### 2. **Mantenibilidad**

- Código más legible y organizado
- Archivos más pequeños y manejables
- Documentación específica por módulo

### 3. **Extensibilidad**

- Fácil agregar nuevos tipos de sensores en `config.py`
- Nuevos generadores de datos pueden heredar de `DataGenerator`
- Interfaces adicionales pueden usar los mismos managers

### 4. **Reutilización**

- Componentes pueden ser utilizados independientemente
- `DatabaseManager` puede usarse en otros scripts
- `DataGenerator` es reutilizable en diferentes contextos

### 5. **Testing**

- Cada módulo puede ser probado por separado
- Mocking más sencillo para pruebas unitarias
- Aislamiento de dependencias

## Flujo de Ejecución

1. **Inicialización** (`upload_data.py`)

   - Carga configuración de base de datos
   - Instancia UserInterface

2. **Interfaz de Usuario** (`user_interface.py`)

   - Conecta a base de datos via DatabaseManager
   - Presenta menú de opciones
   - Coordina operaciones según selección

3. **Operaciones de Datos**
   - **Históricos**: `HistoricalDataGenerator` + `DataGenerator`
   - **Tiempo Real**: `RealtimeDataGenerator` + `DataGenerator`
   - **Estadísticas**: `StatisticsReporter` + `DatabaseManager`

## Uso

```bash
python upload_data.py
```

El sistema mantiene la misma funcionalidad que el archivo original, pero ahora está organizado en una estructura modular más mantenible.

## Dependencias

- `mysql-connector-python`
- `numpy`
- Módulos estándar de Python: `datetime`, `random`, `logging`, `time`

## Configuración

Edita las credenciales de base de datos en `upload_data.py`:

```python
db_config = DatabaseConfig(
    host='localhost',
    database='remote_area_network',
    user='tu_usuario',
    password='tu_contraseña',
    port=3306
)
```
