# 🧠 Guía Técnica del Código - Para Entender el Proyecto Por Dentro

---

## 📥 download_images.py — Descarga automática de imágenes

Este script descarga imágenes de logos desde internet para crear el dataset.

```python
from ddgs import DDGS
```
Importamos DDGS, que es la librería para hacer búsquedas en DuckDuckGo. La usamos porque Google y Bing bloqueaban nuestras peticiones automáticas.

```python
juegos = {
    "league_of_legends": "league of legends logo",
    ...
}
```
Un diccionario donde la clave es el nombre de la carpeta donde guardaremos las imágenes, y el valor es el texto que buscaremos en DuckDuckGo.

```python
def descargar_imagen(url, ruta):
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        with open(ruta, "wb") as f:
            f.write(response.content)
```
Esta función recibe una URL de imagen y una ruta donde guardarla. Hace una petición HTTP a esa URL, y si responde con 200 (que significa "OK"), escribe el contenido binario de la imagen en el archivo. El `"wb"` significa "write binary" (escribir en binario).

```python
existentes = len(os.listdir(ruta))
```
Cuenta cuántas imágenes hay ya en la carpeta. Así si el script se interrumpe y lo volvemos a ejecutar, no empieza desde cero sino que continúa desde donde se quedó.

```python
ext = r["image"].split(".")[-1].split("?")[0]
```
Extrae la extensión del archivo de la URL. Por ejemplo de `https://web.com/logo.png?size=200` extrae `png`. El `.split("?")[0]` elimina los parámetros de la URL que van después del `?`.

```python
nombre = f"{ruta}/{descargadas + 1:04d}.{ext}"
```
Genera el nombre del archivo con 4 dígitos. Por ejemplo `0001.jpg`, `0002.png`, etc. El `:04d` es el formato que le dice a Python que use 4 dígitos con ceros a la izquierda.

---

## 🧠 train.py — Entrenamiento del modelo

Este script entrena el modelo YOLOv8 con nuestras imágenes.

```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
```
Cargamos el modelo YOLOv8 nano (la versión más pequeña y rápida). La primera vez que lo ejecutas, lo descarga automáticamente de internet. La `n` de `yolov8n` significa "nano". Existen versiones más grandes: s (small), m (medium), l (large), x (extra large). Más grande = más preciso pero más lento.

```python
model.train(
    data="data.yaml",     # dónde están las imágenes y las clases
    epochs=50,            # cuántas veces ve el dataset completo
    imgsz=512,            # tamaño al que redimensiona las imágenes
    batch=16,             # cuántas imágenes procesa a la vez
    name="videogame-logos", # nombre de la carpeta donde guarda el modelo
    project="runs",       # carpeta principal donde guarda todo
    patience=10,          # para si no mejora en 10 épocas seguidas
)
```
- **data**: apunta al `data.yaml` que le dice dónde están las imágenes y cuántas clases hay
- **epochs**: número de veces que el modelo ve todas las imágenes. Más épocas = más aprendizaje (hasta cierto punto)
- **imgsz**: todas las imágenes se redimensionan a 512x512 píxeles para que sean uniformes
- **batch**: procesa 16 imágenes a la vez. Más batch = más rápido pero necesita más RAM
- **patience**: si después de 10 épocas el modelo no mejora, para automáticamente para no desperdiciar tiempo

---

## 🎬 detect_video.py — Análisis de vídeos

Este script analiza un vídeo frame por frame buscando logos.

```python
CLASES = ["fortnite", "genshin_impact", "league_of_legends", "minecraft", "valorant", "vrchat"]
```
Lista de clases en el mismo orden que las tiene el modelo. Es importante que el orden coincida con el `data.yaml` de Roboflow, porque el modelo devuelve un número (0, 1, 2...) y nosotros lo convertimos al nombre usando esta lista.

```python
cap = cv2.VideoCapture(ruta_video)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duracion_total = total_frames / fps
```
- `VideoCapture` abre el vídeo
- `FPS` (Frames Per Second) = cuántas imágenes por segundo tiene el vídeo. Un vídeo normal tiene 30fps
- `total_frames` = número total de imágenes del vídeo
- `duracion_total` = total_frames / fps → si hay 300 frames a 30fps = 10 segundos

```python
frames_detectados = defaultdict(int)
```
Un diccionario especial que empieza en 0 automáticamente para cualquier clave nueva. Lo usamos para contar en cuántos frames aparece cada logo. `defaultdict(int)` significa que si accedes a una clave que no existe, la crea con valor 0 en lugar de dar error.

```python
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
```
Bucle que lee el vídeo frame por frame. `cap.read()` devuelve dos cosas: `ret` (True si leyó bien, False si llegó al final) y `frame` (la imagen en sí). Cuando `ret` es False significa que el vídeo terminó y salimos del bucle.

```python
resultados = model(frame, conf=confianza, verbose=False)
```
Pasamos el frame al modelo. `conf=confianza` le dice que solo devuelva detecciones con más de X% de confianza. `verbose=False` evita que imprima información por cada frame (sería demasiado texto).

```python
for r in resultados:
    for box in r.boxes:
        clase_id = int(box.cls[0])      # número de la clase (0=fortnite, 1=genshin...)
        clase_nombre = CLASES[clase_id]  # convertimos el número al nombre
        confianza_det = float(box.conf[0]) # porcentaje de confianza
        x1, y1, x2, y2 = map(int, box.xyxy[0]) # coordenadas del bounding box
```
Por cada detección extraemos: qué clase es, con qué confianza, y las coordenadas del rectángulo (x1,y1 = esquina superior izquierda, x2,y2 = esquina inferior derecha).

```python
cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
```
Dibujamos el rectángulo verde y el texto encima. El color `(0, 255, 0)` es verde en formato BGR (Blue, Green, Red) que usa OpenCV. El `2` al final es el grosor en píxeles.

```python
clases_en_frame.add(clase_nombre)
```
Usamos un `set` (conjunto) en lugar de una lista para evitar contar el mismo logo dos veces en el mismo frame si aparece duplicado.

```python
tiempo = frames / fps
porcentaje = (frames / total_frames) * 100
```
Convertimos frames a segundos dividiendo entre los FPS. El porcentaje es cuántos frames tiene el logo respecto al total.

```python
parser = argparse.ArgumentParser()
parser.add_argument("--video", required=True)
```
`argparse` permite pasar argumentos desde la terminal. Así podemos ejecutar `python detect_video.py --video mivideo.mp4` sin tener que modificar el código.

---

## 🗄️ database.py — Base de datos

Este script gestiona el guardado de resultados en SQLite.

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "detecciones.db")
```
Calculamos la ruta absoluta de la base de datos. `__file__` es la ruta del archivo actual (`database.py`). Con dos `dirname` subimos dos niveles (de `src/` a la raíz del proyecto). Así funciona desde cualquier directorio sin importar desde dónde se ejecute.

```python
engine = create_engine(f"sqlite:///{DB_PATH}")
```
Creamos la conexión a la base de datos SQLite. El formato `sqlite:///ruta` es la forma que SQLAlchemy entiende para conectarse a SQLite.

```python
class Deteccion(Base):
    __tablename__ = "detecciones"
    id = Column(Integer, primary_key=True)
    video = Column(String)
    clase = Column(String)
    tiempo_aparicion = Column(Float)
    porcentaje = Column(Float)
    duracion_video = Column(Float)
    fecha = Column(DateTime, default=datetime.now)
```
Definimos la tabla de la base de datos como una clase Python. Cada `Column` es una columna de la tabla. Esto es lo que se llama ORM (Object Relational Mapping): en lugar de escribir SQL directamente, usamos clases Python.

```python
Base.metadata.create_all(engine)
```
Crea la tabla en la base de datos si no existe. Si ya existe, no hace nada. Se ejecuta automáticamente al importar el archivo.

```python
def guardar_detecciones(nombre_video, informe, duracion_video):
    with Session(engine) as session:
        for clase, datos in informe.items():
            if datos["frames"] > 0:
                session.add(Deteccion(...))
        session.commit()
```
Abre una sesión con la base de datos, crea un registro por cada clase detectada (solo las que tienen frames > 0, es decir que se detectaron), y hace `commit` para guardar los cambios permanentemente.

```python
def obtener_detecciones(video=None):
    with Session(engine) as session:
        query = session.query(Deteccion)
        if video:
            query = query.filter(Deteccion.video == video)
        return query.all()
```
Consulta todos los registros de la base de datos. Si se pasa un nombre de vídeo, filtra solo los de ese vídeo. `.all()` devuelve todos los resultados como una lista.

---

## 🚀 api.py — Servidor FastAPI

Este script es el backend que conecta el frontend con el modelo.

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```
Igual que en database.py, calculamos la ruta raíz del proyecto para poder encontrar el modelo y el frontend independientemente de desde dónde se ejecute.

```python
app = FastAPI(title="Videogame Logo Detector")
```
Creamos la aplicación FastAPI. A partir de aquí definimos los endpoints (rutas) que responderán a las peticiones HTTP.

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
CORS (Cross-Origin Resource Sharing) es una política de seguridad del navegador que bloquea peticiones entre dominios diferentes. Con `allow_origins=["*"]` permitimos peticiones desde cualquier origen. Necesario para que el frontend pueda hablar con el backend.

```python
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
```
Sirve los archivos estáticos (CSS, JS) del frontend. Cuando el navegador pide `/static/style.css`, FastAPI devuelve el archivo `frontend/style.css`.

```python
@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
```
El decorador `@app.get("/")` le dice a FastAPI que cuando alguien entre a `http://localhost:8000/` ejecute esta función. Devuelve el `index.html` del frontend.

```python
@app.post("/analizar")
async def analizar(video: UploadFile = File(...), confianza: float = 0.5):
```
Endpoint POST para recibir el vídeo. `UploadFile` es el tipo de FastAPI para archivos subidos. `async` significa que es una función asíncrona (no bloquea el servidor mientras espera).

```python
with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
    tmp.write(await video.read())
    tmp_path = tmp.name
```
Como el vídeo llega como datos en memoria, lo guardamos en un archivo temporal en disco para que OpenCV pueda leerlo. `delete=False` evita que se borre automáticamente al cerrar el `with`. `await video.read()` lee el contenido del vídeo de forma asíncrona.

```python
informe, duracion = analizar_video(tmp_path, MODELO_PATH, confianza)
os.unlink(tmp_path)
```
Analizamos el vídeo y luego borramos el archivo temporal con `os.unlink` para no llenar el disco.

```python
@app.get("/historial")
def historial():
    registros = obtener_detecciones()
    return [{"video": r.video, "clase": r.clase, ...} for r in registros]
```
Endpoint GET que devuelve todos los análisis guardados. Convierte los objetos de SQLAlchemy a diccionarios Python que FastAPI serializa automáticamente a JSON.

---

## 🌐 frontend/index.html — Estructura de la página

```html
<link href="https://fonts.googleapis.com/css2?family=Orbitron...">
```
Carga la fuente Orbitron de Google Fonts, que es la tipografía estilo gamer que usamos en los títulos.

```html
<div class="scanlines"></div>
<div class="particles" id="particles"></div>
```
Dos capas decorativas: `scanlines` crea el efecto de líneas de TV antigua, y `particles` es donde JavaScript añade las partículas flotantes.

```html
<span class="glitch" data-text="GAMELOGO">GAMELOGO</span>
```
El efecto glitch del título. El `data-text` es un atributo personalizado que CSS usa para crear el efecto de duplicado con colores diferentes.

```html
<input type="file" id="videoInput" accept="video/*" hidden>
<button onclick="document.getElementById('videoInput').click()">SELECCIONAR VÍDEO</button>
```
El input de archivo está oculto (`hidden`) porque es feo por defecto. El botón bonito al hacer click activa el input oculto programáticamente.

---

## 🎨 frontend/app.js — Lógica de la página

```javascript
const COLORES = {
    fortnite: { color: "#bf00ff", icon: "🟣" },
    ...
}
```
Diccionario con el color y emoji de cada juego. Lo usamos para que cada card de resultados tenga el color característico de su juego.

```javascript
function crearParticulas() {
    for (let i = 0; i < 40; i++) {
        const p = document.createElement("div")
        p.style.left = Math.random() * 100 + "vw"
        p.style.animationDuration = (Math.random() * 10 + 8) + "s"
    }
}
```
Crea 40 partículas con posición y velocidad aleatoria. `Math.random()` devuelve un número entre 0 y 1. Multiplicado por 100 da una posición aleatoria en la pantalla.

```javascript
uploadZone.addEventListener("dragover", e => { e.preventDefault(); ... })
uploadZone.addEventListener("drop", e => { const file = e.dataTransfer.files[0] })
```
Implementa el drag & drop. `e.preventDefault()` evita que el navegador abra el archivo. `e.dataTransfer.files[0]` obtiene el primer archivo arrastrado.

```javascript
async function analizar() {
    const formData = new FormData()
    formData.append("video", input.files[0])
    const res = await fetch("/analizar", { method: "POST", body: formData })
    const data = await res.json()
}
```
Envía el vídeo al backend. `FormData` es la forma de enviar archivos por HTTP. `fetch` hace la petición HTTP. `await` espera a que el servidor responda antes de continuar. `res.json()` convierte la respuesta JSON a un objeto JavaScript.

```javascript
data.detecciones.forEach((d, i) => {
    html += `<div class="card" style="animation-delay: ${i * 0.1}s">...</div>`
})
```
Por cada detección crea una card HTML. El `animation-delay` hace que las cards aparezcan una tras otra con un pequeño retraso, creando un efecto de entrada escalonado.

---

## 🐳 Dockerfile — Contenedor Docker

```dockerfile
FROM python:3.13-slim
```
Usamos la imagen base de Python 3.13 en versión slim (más ligera, sin cosas innecesarias).

```dockerfile
RUN apt-get install -y libgl1 libglib2.0-0
```
Instalamos dependencias del sistema que necesita OpenCV para funcionar dentro del contenedor. Sin esto OpenCV daría error al intentar procesar imágenes.

```dockerfile
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY runs/ ./runs/
```
Copiamos el código y el modelo entrenado dentro del contenedor.

```dockerfile
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```
El comando que se ejecuta cuando arranca el contenedor. `--host 0.0.0.0` hace que sea accesible desde fuera del contenedor (no solo desde dentro).

---

## 📋 data.yaml — Configuración del dataset

```yaml
path: C:/Users/Coder/Downloads/videogame-logos.v1i.yolov8
train: train/images
val: valid/images
nc: 6
names:
  - fortnite
  - genshin_impact
  - league_of_legends
  - minecraft
  - valorant
  - vrchat
```
- **path**: ruta raíz del dataset
- **train/val**: subcarpetas con las imágenes de entrenamiento y validación
- **nc**: número de clases (6 juegos)
- **names**: nombres de las clases en orden. El orden importa porque el modelo usa el índice (0, 1, 2...) y lo mapeamos a estos nombres
