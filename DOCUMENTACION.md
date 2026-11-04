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
YOLO (You Only Look Once) es uno de los modelos de detección de objetos más populares y rápidos del mundo. Su nombre viene de que analiza la imagen entera de una sola vez, en lugar de ir parte por parte. Nosotros usamos la versión 8 en su variante **nano** (YOLOv8n), optimizada para ser rápida en CPU sin sacrificar precisión para logos.

### ¿Qué es el entrenamiento?
El entrenamiento es el proceso por el que el modelo aprende. Le mostramos cientos de imágenes de logos con su ubicación marcada (bounding boxes) y el modelo va ajustando sus parámetros internos hasta que es capaz de reconocerlos solo.

- **Época**: cada vez que el modelo ve todas las imágenes del dataset una vez. Con 50 épocas, ve el dataset 50 veces, mejorando en cada pasada.
- **Loss (pérdida)**: número que indica cuánto se equivoca el modelo. Cuanto más bajo, mejor.

### ¿Qué es el Transfer Learning?
En lugar de entrenar el modelo desde cero (lo que requeriría millones de imágenes), partimos de un modelo que ya sabe reconocer objetos genéricos (YOLOv8n preentrenado) y lo "afinamos" con nuestras imágenes de logos. Esto ahorra tiempo y mejora los resultados con pocos datos.

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
- **Rotación ±15°**: gira la imagen ligeramente
- **Brillo ±25%**: cambia el brillo de la imagen

Así pasamos de 480 imágenes reales a **556 imágenes** para entrenar, sin necesidad de buscar más fotos.

---

## ⚡ Optimización: Frame Skip

Para analizar vídeos de forma eficiente, el sistema no analiza todos los frames del vídeo. En su lugar, analiza **1 de cada 3 frames** (frame skip x3). Esto reduce el tiempo de análisis un **66%** sin perder precisión significativa, ya que los logos no cambian de posición de un frame al siguiente.

Por ejemplo, en un vídeo a 30 fps:
- Sin frame skip: analiza 30 imágenes por segundo
- Con frame skip x3: analiza 10 imágenes por segundo

El tiempo de aparición de cada logo se calcula correctamente teniendo en cuenta los frames saltados.

---

## 🛠️ Tecnologías utilizadas

### Python
Lenguaje de programación principal del proyecto. Es el más usado en inteligencia artificial por su simplicidad y la cantidad de librerías disponibles.

### YOLOv8n (Ultralytics)
El modelo de detección de objetos que usamos. Usamos la variante **nano** por ser la más rápida en CPU, suficiente para detectar logos con buena precisión.

### OpenCV
Librería de visión por computador. La usamos para leer y procesar los vídeos frame por frame (imagen por imagen).

### PyTorch
Framework de deep learning desarrollado por Meta. Es el motor que hay detrás de YOLOv8, el que hace los cálculos matemáticos del entrenamiento.

### FastAPI
Framework para crear APIs web en Python. Una API es un intermediario que permite que el frontend (la página web) se comunique con el modelo de IA. Cuando subes un vídeo en la web, FastAPI lo recibe, se lo pasa al modelo y devuelve los resultados.

### SQLAlchemy + SQLite
- **SQLite**: base de datos ligera que guarda los resultados de cada análisis en un archivo `.db`
- **SQLAlchemy**: librería que nos permite interactuar con la base de datos desde Python de forma sencilla

Cada vez que se analiza un vídeo, se guarda en la base de datos: el nombre del vídeo, qué logos se detectaron, cuánto tiempo aparecieron y el porcentaje.

### Docker
Herramienta que empaqueta toda la aplicación (código, dependencias, configuración) en un contenedor. Esto garantiza que la app funciona igual en cualquier ordenador o servidor, sin problemas de compatibilidad.

Los pesos del modelo y la base de datos se montan como **volúmenes externos** al contenedor, de forma que los datos persisten aunque el contenedor se reinicie.

### Roboflow
Plataforma web para gestionar datasets de visión por computador. La usamos para anotar las imágenes y aplicar data augmentation antes del entrenamiento.

---

## 📁 Estructura del proyecto

```
computer-vision/
├── dataset/
│   ├── images/
│   │   ├── train/        → imágenes de entrenamiento (no en repo)
│   │   └── val/          → imágenes de validación (no en repo)
│   └── labels/           → anotaciones en formato YOLO
├── src/
│   ├── download_images.py  → descarga imágenes automáticamente
│   ├── train.py            → entrena el modelo YOLOv8
│   ├── detect_video.py     → analiza un vídeo y genera el informe
│   ├── database.py         → guarda los resultados en SQLite
│   └── api.py              → servidor FastAPI (backend)
├── frontend/
│   ├── index.html          → estructura de la página web
│   ├── style.css           → diseño visual gamer oscuro
│   └── app.js              → lógica de la página web
├── runs/                   → modelo entrenado (no en repo)
├── database/               → base de datos SQLite (se genera al arrancar)
├── data.yaml               → configuración del dataset para YOLO
├── requirements.txt        → dependencias Python
├── Dockerfile              → instrucciones para crear el contenedor
├── .dockerignore           → qué excluir del build de Docker
└── docker-compose.yml      → configuración para lanzar con Docker
```

---

## 🚨 Mensajes de error

Cuando algo sale mal, la aplicación muestra una notificación animada en la parte inferior de la pantalla con un mensaje explicativo. Los errores tienen un toque de humor gamer para que no sea tan frustrante:

| Situación | Mensaje |
|---|---|
| No has seleccionado vídeo | "👀 Oye, que no has seleccionado ningún vídeo..." |
| Vídeo demasiado grande (+500MB) | "🐘 Ese vídeo pesa más que un Creeper cargado de TNT" |
| Formato de vídeo no soportado | "🤔 Ese formato no lo reconozco ni con wall hack activado" |
| Valor de confianza inválido | "🎯 La confianza tiene que estar entre 10% y 90%, no seas extremista" |
| Error inesperado | "💀 Algo salió mal... como cuando te matan en la zona segura" |

La notificación desaparece sola a los 4 segundos.

---

## 📄 Descargar informe en PDF

Después de analizar un vídeo, aparece el botón **📄 DESCARGAR INFORME PDF**. Al pulsarlo se genera y descarga automáticamente un PDF con los resultados del análisis.

El PDF incluye:
- Nombre del vídeo analizado
- Fecha y hora del análisis
- Tabla con cada marca detectada, su tiempo de aparición y porcentaje
- Barra visual proporcional al porcentaje para cada marca, coloreada con el color característico del juego
- Duración total del vídeo

El archivo se descarga con el nombre `informe_nombreVideo_fecha.pdf` directamente en la carpeta de descargas del navegador, sin necesidad de ninguna acción adicional en el servidor.

> El botón solo aparece cuando se han detectado logos. Si el vídeo no contiene ningún logo reconocido, no se ofrece la descarga.

---

## 🚀 Flujo completo del sistema

```
1. Usuario sube un vídeo en la web
        ↓
2. FastAPI recibe el vídeo y lo guarda en un archivo temporal
        ↓
3. detect_video.py analiza el vídeo frame a frame con YOLOv8
   (1 de cada 3 frames gracias al frame skip x3)
        ↓
4. Por cada frame analizado, el modelo detecta logos presentes
        ↓
5. Se calcula el tiempo y porcentaje de aparición de cada logo
        ↓
6. El archivo temporal se elimina
        ↓
7. Los resultados se guardan en la base de datos SQLite
        ↓
8. La web muestra el informe con tarjetas por cada marca detectada
        ↓
9. El usuario puede descargar el informe completo en PDF
```

---

## 📊 ¿Cómo se interpreta el informe?

Cuando se analiza un vídeo, el sistema devuelve:

| Campo | Descripción |
|---|---|
| Marca | Nombre del logo detectado |
| Tiempo (s) | Segundos que aparece el logo en el vídeo |
| Porcentaje | % del vídeo total en que aparece el logo |
| Duración total | Duración completa del vídeo analizado |

El historial de todos los análisis se puede consultar en la pestaña **Historial** de la aplicación web.

---

## ❓ Preguntas frecuentes

**¿El análisis es en tiempo real?**
No, el sistema analiza vídeos pregrabados. Procesa el vídeo completo y genera el informe al terminar.

**¿Cuánto tarda en analizar un vídeo?**
Depende de la duración del vídeo y el hardware. Gracias al frame skip x3, el análisis es aproximadamente 3 veces más rápido que sin optimización.

**¿Se pueden añadir más logos en el futuro?**
Sí, el sistema está diseñado para escalar. Solo hay que añadir más imágenes del nuevo logo, anotarlas en Roboflow y reentrenar el modelo.

**¿Dónde se guardan los resultados?**
En una base de datos SQLite local (`database/detecciones.db`), consultable desde la pestaña Historial de la aplicación web.

**¿Se puede descargar el informe?**
Sí, después de cada análisis aparece el botón **📄 DESCARGAR INFORME PDF**. El PDF se genera directamente en el navegador e incluye la tabla completa de detecciones con barras visuales por marca.

**¿Hay límite de tamaño para los vídeos?**
Sí, el límite es de 500MB por vídeo.
