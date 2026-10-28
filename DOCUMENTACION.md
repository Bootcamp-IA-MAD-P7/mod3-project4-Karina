# 🎮 Detección de Logos de Videojuegos con Inteligencia Artificial

## ¿De qué trata este proyecto?

Una empresa de publicidad quiere saber cuánto tiempo aparecen los logos de sus marcas en pantalla dentro de vídeos (streams, gameplays, etc.). Para eso hemos creado un sistema de inteligencia artificial que analiza vídeos automáticamente, detecta los logos y genera un informe con el tiempo y porcentaje de aparición de cada marca.

Las marcas que detecta son:
- League of Legends
- Valorant
- Fortnite
- Genshin Impact
- Minecraft
- VRChat

---

## 🧠 ¿Cómo funciona la Inteligencia Artificial?

### ¿Qué es un modelo de detección de objetos?
Un modelo de detección de objetos es un programa que ha "aprendido" a reconocer cosas dentro de imágenes. Igual que un humano aprende a reconocer un logo después de verlo muchas veces, el modelo aprende viendo miles de imágenes etiquetadas.

### ¿Qué es YOLO?
YOLO (You Only Look Once) es uno de los modelos de detección de objetos más populares y rápidos del mundo. Su nombre viene de que analiza la imagen entera de una sola vez, en lugar de ir parte por parte. Nosotros usamos la versión 8 (YOLOv8), la más moderna.

### ¿Qué es el entrenamiento?
El entrenamiento es el proceso por el que el modelo aprende. Le mostramos cientos de imágenes de logos con su ubicación marcada (bounding boxes) y el modelo va ajustando sus parámetros internos hasta que es capaz de reconocerlos solo.

- **Época**: cada vez que el modelo ve todas las imágenes del dataset una vez. Con 50 épocas, ve el dataset 50 veces, mejorando en cada pasada.
- **Loss (pérdida)**: número que indica cuánto se equivoca el modelo. Cuanto más bajo, mejor.
  - **box_loss**: error al localizar el bounding box
  - **cls_loss**: error al identificar la clase (qué logo es)
  - **dfl_loss**: error en la precisión de los bordes del bounding box

### ¿Qué es el Transfer Learning?
En lugar de entrenar el modelo desde cero (lo que requeriría millones de imágenes), partimos de un modelo que ya sabe reconocer objetos genéricos (YOLOv8 preentrenado) y lo "afinamos" con nuestras imágenes de logos. Esto ahorra tiempo y mejora los resultados.

### ¿Qué es un Bounding Box?
Es el rectángulo que dibuja el modelo alrededor del objeto detectado. Junto al rectángulo aparece el nombre de la clase y el porcentaje de confianza (qué seguro está el modelo de su detección).

---

## 📦 ¿Cómo se creó el Dataset?

Un dataset es el conjunto de imágenes que usamos para entrenar el modelo.

### 1. Recolección de imágenes
Creamos un script en Python que descarga automáticamente imágenes de logos desde internet usando DuckDuckGo. Descargamos 80 imágenes por cada juego (480 en total).

### 2. Anotación con Roboflow
Roboflow es una plataforma web que nos permite:
- Subir las imágenes
- Dibujar los bounding boxes alrededor de cada logo
- Etiquetar cada bounding box con el nombre del juego
- Aplicar **data augmentation** automático

### 3. ¿Qué es el Data Augmentation?
Es una técnica que multiplica las imágenes del dataset aplicando transformaciones:
- **Flip horizontal**: voltea la imagen en espejo
- **Rotación**: gira la imagen ligeramente
- **Brillo**: cambia el brillo de la imagen

Así pasamos de 215 imágenes reales a 556 imágenes para entrenar, sin necesidad de buscar más fotos.

---

## 🛠️ Tecnologías utilizadas

### Python
Lenguaje de programación principal del proyecto. Es el más usado en inteligencia artificial por su simplicidad y la cantidad de librerías disponibles.

### YOLOv8 (Ultralytics)
El modelo de detección de objetos que usamos. Ultralytics es la empresa que desarrolla y mantiene YOLO. Nosotros usamos su librería para entrenar y usar el modelo.

### OpenCV
Librería de visión por computador. La usamos para leer y procesar los vídeos frame por frame (imagen por imagen). También dibuja los bounding boxes sobre los frames del vídeo.

### PyTorch
Framework de deep learning desarrollado por Meta. Es el motor que hay detrás de YOLOv8, el que hace los cálculos matemáticos del entrenamiento.

### FastAPI
Framework para crear APIs web en Python. Una API es un intermediario que permite que el frontend (la página web) se comunique con el modelo de IA. Por ejemplo, cuando subes un vídeo en la web, FastAPI lo recibe, se lo pasa al modelo y devuelve los resultados.

### SQLAlchemy + SQLite
- **SQLite**: base de datos ligera que guarda los resultados de cada análisis en un archivo `.db`
- **SQLAlchemy**: librería que nos permite interactuar con la base de datos desde Python de forma sencilla

Cada vez que se analiza un vídeo, se guarda en la base de datos: el nombre del vídeo, qué logos se detectaron, cuánto tiempo aparecieron y el porcentaje.

### Docker
Herramienta que empaqueta toda la aplicación (código, dependencias, configuración) en un contenedor. Esto garantiza que la app funciona igual en cualquier ordenador o servidor, sin problemas de compatibilidad.

### Roboflow
Plataforma web para gestionar datasets de visión por computador. La usamos para anotar las imágenes y aplicar data augmentation antes del entrenamiento.

---

## 📁 Estructura del proyecto

```
computer-vision/
├── dataset/              → imágenes para entrenar el modelo
├── src/
│   ├── download_images.py  → descarga imágenes automáticamente
│   ├── train.py            → entrena el modelo YOLOv8
│   ├── detect_video.py     → analiza un vídeo y genera el informe
│   ├── database.py         → guarda los resultados en SQLite
│   └── api.py              → servidor FastAPI (backend)
├── frontend/
│   ├── index.html          → estructura de la página web
│   ├── style.css           → diseño visual de la página
│   └── app.js              → lógica de la página web
├── runs/                 → aquí YOLO guarda el modelo entrenado
├── database/             → aquí se guarda la base de datos
├── data.yaml             → configuración del dataset para YOLO
├── requirements.txt      → lista de dependencias Python
├── Dockerfile            → instrucciones para crear el contenedor Docker
└── docker-compose.yml    → configuración para lanzar la app con Docker
```

---

## 🚀 Flujo completo del sistema

```
1. Usuario sube un vídeo en la web
        ↓
2. FastAPI recibe el vídeo
        ↓
3. detect_video.py analiza el vídeo frame por frame con YOLOv8
        ↓
4. Por cada frame, el modelo detecta logos y dibuja bounding boxes
        ↓
5. Se calcula el tiempo y porcentaje de aparición de cada logo
        ↓
6. Los resultados se guardan en la base de datos SQLite
        ↓
7. La web muestra el informe con los resultados
```

---

## 📊 ¿Cómo se interpreta el informe?

Cuando se analiza un vídeo, el sistema devuelve:

| Campo | Descripción |
|---|---|
| Marca | Nombre del logo detectado |
| Tiempo (s) | Segundos que aparece el logo en el vídeo |
| Porcentaje | % del vídeo total en que aparece el logo |
| Confianza | % de seguridad del modelo en la detección |

---

## ❓ Preguntas frecuentes

**¿El análisis es en tiempo real?**
No, el sistema analiza vídeos pregrabados. Procesa el vídeo completo y genera el informe al terminar.

**¿Cuánto tarda en analizar un vídeo?**
Depende de la duración del vídeo y el hardware. En CPU tarda aproximadamente 1-2 segundos por segundo de vídeo.

**¿Se pueden añadir más logos en el futuro?**
Sí, el sistema está diseñado para escalar. Solo hay que añadir más imágenes del nuevo logo, anotarlas en Roboflow y reentrenar el modelo.

**¿Dónde se guardan los resultados?**
En una base de datos SQLite local (`database/detecciones.db`) y se pueden consultar desde la pestaña Historial de la aplicación web.
