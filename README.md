# **Red Mesh LoRa para Monitoreo en Áreas Remotas** 🚀

---

## **🌟 Introducción**

En muchas áreas rurales y remotas, las soluciones de comunicación tradicionales como Wi-Fi o redes de datos móviles enfrentan limitaciones significativas relacionadas con la infraestructura, el alcance y el costo. Este proyecto aborda estas problemáticas mediante el uso de **LoRa** 🌐 (tecnología de largo alcance y bajo consumo) combinado con una **red mesh** 🔗 para garantizar una solución escalable y eficiente.

Este sistema tiene aplicaciones en diversos sectores, como:  
🌱 **Medición ambiental**: Monitoreo de calidad del aire, temperatura y humedad.  
🌾 **Agricultura inteligente**: Seguimiento de cultivos en grandes extensiones.  
🌳 **Gestión de recursos naturales**: Vigilancia en áreas protegidas o de difícil acceso.

---

## **🎯 Objetivos del Proyecto**

### **Objetivo General**
Desarrollar una red mesh basada en **tecnología LoRa** y el algoritmo de enrutamiento **DSR** (Dynamic Source Routing) que permita la transmisión eficiente de datos en áreas remotas, proporcionando una solución económica, confiable y escalable.

### **Objetivos Específicos**
✅ Diseñar una **arquitectura de red mesh** que permita la incorporación dinámica de nodos.  
✅ Implementar el algoritmo **DSR** para optimizar el enrutamiento de datos entre nodos.  
✅ Integrar **sensores ambientales** en los nodos para recolectar datos específicos.  
✅ Centralizar la información en un **nodo maestro** y enviarla a un servidor web mediante una **REST API**.  
✅ Probar la funcionalidad y confiabilidad del sistema en entornos simulados y reales.

---

## **📂 Estructura del Proyecto**

### **1. Componentes del Sistema**
- **Nodos** 📡:  
  - Equipados con tecnología **LoRa** para comunicación.  
  - Incluyen sensores ambientales para recolectar datos como temperatura, humedad, y más.  

- **Nodo Maestro** 🖥️:  
  - Centraliza los datos recolectados por los nodos y los transmite a un servidor web.  

- **Servidor Web** 🌐:  
  - Implementado con **Django** y **Django REST Framework**.  
  - Proporciona una **API REST** para la recolección y consulta de datos.  

---

## **🔧 Instalación y Configuración**

### **1. Nodo Maestro**

1. Clona este repositorio:

   ```
   git clone https://github.com/usuario/lora-mesh-project.git
   cd lora-mesh-project
   ```

2. Configura el entorno virtual y las dependencias:
    ```
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    ```

3. Configura la base de datos en el archivo settings.py. Recomendamos usar AWS RDS para entornos de producción.

4. Ejecuta las migraciones y levanta el servidor:
    ```
    python manage.py migrate
    python manage.py runserver
    ```

### **2. Nodos LoRa**
Carga el firmware MicroPython en los microcontroladores.
Personaliza el script de cada nodo para incluir la dirección única y la lógica de enrutamiento DSR.
Conecta los sensores al nodo y verifica la transmisión de datos.

---

## **🚀 Uso del Proyecto**

1. **Configuración Inicial**:
   - Define la topología inicial de la red.  
   - Asegúrate de que el nodo maestro esté configurado correctamente para recibir datos.  

2. **Recolección de Datos**:  
   - Los nodos recolectarán información de los sensores y la transmitirán a través de la red mesh.  

3. **Consulta de Datos**:
   - Usa la **API REST** para acceder a los datos centralizados:
     - **GET** `/api/sensors/`: Consulta los datos recolectados.  
     - **POST** `/api/sensors/`: Registra nuevos datos.  

---

## **🔬 Pruebas y Resultados**

El sistema será probado en:  
- **Entornos simulados** para verificar la funcionalidad de la red y el enrutamiento.  
- **Entornos reales** para evaluar la cobertura, eficiencia y confiabilidad en áreas remotas.

---

## **👨‍🎓 Sobre Nosotros**

Somos **dos estudiantes de Ingeniería Electrónica** en la **Universidad Tecnológica Nacional, Facultad Regional Tucumán (UTN FRT)** 🏫. Este proyecto nació como una iniciativa para aplicar nuestras habilidades en áreas como redes de comunicación, sistemas embebidos y desarrollo web, buscando resolver problemas reales en comunidades remotas.  

📌 **LinkedIn**:  
- [Fernandez Francisco](https://linkedin.com/in/franfer0301)  
- [Ontivero Nahuel](https://linkedin.com/in/nahuel-ontivero-5790871b7/)  

---

## **📜 Licencia**
Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.
