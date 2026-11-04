# 🛠️ GUÍA TÉCNICA — GameLogo Detector
### Cómo se construyó este proyecto desde cero

---

## 0. Punto de partida

El objetivo era construir un sistema que analizara vídeos de streams y detectara cuánto tiempo aparecen logos de videojuegos en pantalla. Para eso necesitábamos:

1. Un modelo de IA capaz de detectar logos en imágenes
2. Un sistema que aplique ese modelo a vídeos frame a frame
3. Una base de datos que guarde los resultados
4. Una API que conecte todo
5. Un frontend para que sea usable desde el navegador

---

## 1. Estructura del proyecto

Lo primero fue decidir cómo organizar el código. La estructura final quedó así:

```
computer-vision/
├── src/               → todo el código Python
├── frontend/          → HTML, CSS y JS de la web
├── dataset/           → imágenes para entrenar (no en repo)
├── runs/              → pesos del modelo entrenado (no en repo)
├── database/          → archivo .db de SQLite (no en repo)
├── data.yaml          → configuración del dataset para YOLO
├── requirements.txt   → dependencias Python
├── Dockerfile         → para contenedorizar la app
├── .dockerignore      → qué excluir del build de Docker
└── docker-compose.yml → para lanzar la app con Docker
```

La carpeta `src/` tiene exactamente un archivo por responsabilidad:
- `download_images.py` → scraping
- `train.py` → entrenamiento
- `detect_video.py` → inferencia en vídeo
- `database.py` → capa de datos
- `api.py` → servidor web

---

## 2. Dataset — recolección de imágenes

### ¿Por qué un dataset propio?
Los modelos preentrenados de YOLO no saben reconocer logos de videojuegos específicos. Necesitábamos imágenes de esos logos para enseñarle.

### Script de descarga (`src/download_images.py`)

Usamos la librería `duckduckgo-search` (DDGS) para buscar imágenes por nombre de juego y descargarlas automáticamente.

```python
from ddgs import DDGS
import requests

juegos = {
    "league_of_legends": "league of legends logo",
    "valorant": "valorant logo",
    ...
}
```

Para cada juego:
1. Se crea la carpeta `dataset/images/train/{juego}/`
2. Se buscan hasta 150 resultados en DuckDuckGo
3. Se descargan hasta 80 imágenes por juego
4. Se guarda con nombre secuencial `0001.jpg`, `0002.png`, etc.

El `except requests.RequestException` captura solo errores de red, no errores inesperados del programa.

**Resultado:** 80 imágenes × 6 juegos = **480 imágenes**

---

## 3. Anotación con Roboflow

Las imágenes descargadas no sirven directamente para entrenar. YOLO necesita saber **dónde está el logo** en cada imagen (bounding box) y **qué logo es** (clase).

### Proceso en Roboflow:
1. Crear proyecto → tipo "Object Detection"
2. Subir las 480 imágenes
3. Dibujar manualmente el rectángulo alrededor de cada logo
4. Etiquetar con el nombre del juego
5. Aplicar **data augmentation**:
   - Flip horizontal
   - Rotación ±15°
   - Brillo ±25%
6. Exportar en formato YOLOv8

**Resultado:** 480 imágenes → **556 imágenes** con augmentation

Roboflow exporta dos carpetas:
- `images/train/` y `images/val/` → las imágenes
- `labels/train/` y `labels/val/` → archivos `.txt` con las coordenadas de los bounding boxes

### Formato de las anotaciones YOLO
Cada imagen tiene un `.txt` con una línea por objeto detectado:
```
clase_id  x_centro  y_centro  ancho  alto
```
Todo en valores relativos (0 a 1) respecto al tamaño de la imagen.

---

## 4. Configuración del dataset (`data.yaml`)

YOLO necesita un archivo de configuración que le diga dónde están las imágenes y cuántas clases hay:

```yaml
path: dataset
train: images/train
val: images/val

nc: 6
names:
  - fortnite
  - genshin_impact
  - league_of_legends
  - minecraft
  - valorant
  - vrchat
```

El orden de `names` es importante — el índice de cada nombre es el `clase_id` que usa YOLO internamente. Si en las anotaciones aparece `0`, significa `fortnite`.

> ⚠️ Inicialmente las rutas apuntaban a la carpeta de Roboflow descargada localmente. Se corrigió para apuntar a `dataset/` dentro del proyecto.

---

## 5. Entrenamiento (`src/train.py`)

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # carga el modelo base preentrenado

model.train(
    data="data.yaml",
    epochs=50,
    imgsz=512,
    batch=16,
    name="videogame-logos",
    project="runs",
    patience=10,
)
```

### Parámetros explicados:
- `yolov8n.pt` → modelo "nano", el más ligero. Suficiente para logos y más rápido que `yolov8s.pt` (small). Se cambió de `s` a `n` para optimizar velocidad en CPU.
- `epochs=50` → el modelo ve el dataset completo 50 veces
- `imgsz=512` → redimensiona todas las imágenes a 512×512 para el entrenamiento
- `batch=16` → procesa 16 imágenes a la vez antes de actualizar los pesos
- `patience=10` → si en 10 épocas seguidas no mejora, para antes de llegar a 50
- `project="runs"` → carpeta donde guarda los resultados

### ¿Qué genera el entrenamiento?
En `runs/videogame-logos/weights/` aparecen dos archivos:
- `best.pt` → los pesos del momento en que el modelo tuvo mejor rendimiento en validación
- `last.pt` → los pesos de la última época

Siempre usamos `best.pt`.

### Transfer Learning
No entrenamos desde cero. `yolov8n.pt` ya sabe detectar objetos genéricos (personas, coches, etc.) gracias a haber sido entrenado con el dataset COCO (80 clases, millones de imágenes). Nosotros "afinamos" esos pesos con nuestras imágenes de logos. Esto se llama **transfer learning** y permite obtener buenos resultados con pocos datos.

---

## 6. Detección en vídeo (`src/detect_video.py`)

Esta es la pieza central del sistema. Recibe un vídeo y devuelve cuánto tiempo aparece cada logo.

### Flujo:
```python
cap = cv2.VideoCapture(ruta_video)

if not cap.isOpened():
    raise ValueError(f"No se pudo abrir el vídeo: {ruta_video}")
```

`cv2.VideoCapture` no lanza excepción si el archivo no existe — devuelve un objeto inválido. Por eso hay que comprobar `isOpened()` explícitamente.

### Frame skip
```python
if frame_actual % frame_skip == 0:
    resultados = model(frame, conf=confianza, verbose=False)
```

Con `frame_skip=3` solo analizamos 1 de cada 3 frames. Esto reduce el tiempo de análisis un 66% con un impacto mínimo en la precisión, porque los logos no cambian de un frame al siguiente.

### Conteo de tiempo
```python
frames_restantes = total_frames - frame_actual
incremento = min(frame_skip, frames_restantes)
for clase in clases_en_frame:
    frames_detectados[clase] += incremento
```

Cuando detectamos un logo en el frame `N`, asumimos que también estaba en los `frame_skip` frames anteriores (que no analizamos). El `min(frame_skip, frames_restantes)` evita sobrecontar al final del vídeo cuando quedan menos frames que `frame_skip`.

### Cálculo del informe
```python
tiempo = frames / fps
porcentaje = (frames / total_frames) * 100
```

`fps` (frames por segundo) lo da OpenCV directamente del vídeo. Dividir los frames detectados entre fps da los segundos reales de aparición.

### try/finally para liberar recursos
```python
try:
    while cap.isOpened():
        ...
finally:
    cap.release()
```

`cap.release()` cierra el handle del vídeo. Si no se llama (por ejemplo si el modelo lanza una excepción), el archivo queda bloqueado. El `finally` garantiza que siempre se ejecuta.

---

## 7. Base de datos (`src/database.py`)

Usamos SQLite con SQLAlchemy como ORM.

### Modelo de datos
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

Una fila por cada logo detectado en cada vídeo. Si en un vídeo se detectan 3 logos, se insertan 3 filas.

### `Base.metadata.create_all(engine)`
Esta línea crea la tabla en la base de datos si no existe. Se ejecuta al importar el módulo, así que la primera vez que se arranca la app, la tabla se crea automáticamente.

### Por qué `session.expunge_all()`
```python
def obtener_detecciones(video=None):
    with Session(engine) as session:
        ...
        registros = query.all()
        session.expunge_all()  # ← importante
        return registros
```

SQLAlchemy mantiene los objetos ORM "conectados" a la sesión. Cuando el bloque `with` termina, la sesión se cierra. Si intentamos acceder a los atributos de los objetos fuera de la sesión, SQLAlchemy intenta hacer una consulta nueva y falla con `DetachedInstanceError`. `expunge_all()` desconecta los objetos de la sesión antes de cerrarla, permitiendo acceder a sus atributos libremente.

---

## 8. API REST (`src/api.py`)

FastAPI sirve tanto la API como el frontend estático.

### Subida de vídeo con streaming
```python
with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
    shutil.copyfileobj(video.file, tmp)
    tmp_path = tmp.name
```

`shutil.copyfileobj` copia el archivo en chunks en lugar de cargarlo entero en RAM con `await video.read()`. Para vídeos grandes esto evita quedarse sin memoria.

### Limpieza garantizada del archivo temporal
```python
try:
    informe, duracion = analizar_video(tmp_path, MODELO_PATH, confianza)
finally:
    os.unlink(tmp_path)
```

El `finally` garantiza que el archivo temporal se borra aunque `analizar_video` falle.

### Límite de tamaño
```python
MAX_UPLOAD_MB = 500

if video.size and video.size > MAX_UPLOAD_MB * 1024 * 1024:
    raise HTTPException(status_code=413, detail=f"El vídeo supera el límite de {MAX_UPLOAD_MB}MB")
```

Sin esto, cualquiera podría subir un archivo de varios GB y saturar el servidor.

### Endpoints
- `GET /` → sirve el `index.html`
- `POST /analizar` → recibe el vídeo, lo analiza y devuelve el informe
- `GET /historial` → devuelve todos los análisis guardados en la BD

### Montar el frontend como archivos estáticos
```python
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
```

Esto hace que `style.css` y `app.js` sean accesibles en `/static/style.css` y `/static/app.js`.

---

## 9. Frontend (`frontend/`)

Sin frameworks. HTML, CSS y JS puros.

### `index.html`
Estructura de dos pestañas: "Analizar" e "Historial". El vídeo se sube con un `<input type="file">` oculto que se activa con un botón personalizado. También soporta drag & drop.

### `style.css`
Estética gamer oscura con variables CSS para los colores neón:
```css
:root {
    --neon-cyan: #00f5ff;
    --neon-purple: #bf00ff;
    --neon-green: #00ff88;
    --neon-red: #ff003c;
    --bg-dark: #050510;
}
```

Efectos visuales: animación `glitch` en el título, partículas flotantes, líneas de escaneo con `repeating-linear-gradient`.

### `app.js`
- `analizar()` → construye un `FormData`, hace `fetch POST /analizar` y llama a `mostrarResultados()`
- `mostrarResultados()` → genera las cards dinámicamente con los colores de cada marca
- `cargarHistorial()` → hace `fetch GET /historial` y construye la tabla
- `showTab(tab, e)` → cambia entre pestañas. Recibe `event` como parámetro explícito (no como global implícito del navegador)

---

## 10. Exportar informe a PDF (`frontend/app.js`)

### ¿Por qué en el frontend y no en el backend?
Generar el PDF en el navegador con jsPDF evita añadir dependencias pesadas al backend (como `reportlab` o `weasyprint`) y no requiere ningún endpoint nuevo. El navegador ya tiene todos los datos del análisis, así que tiene sentido generarlo ahí directamente.

### Librería: jsPDF
Se carga via CDN en `index.html`, sin instalar nada:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
```

La versión UMD expone `window.jspdf`, de donde se extrae la clase `jsPDF`:
```javascript
const { jsPDF } = window.jspdf
const doc = new jsPDF()
```

### Guardar el último análisis
Para que el botón PDF funcione en cualquier momento después del análisis, los datos se guardan en una variable global al recibir la respuesta de la API:
```javascript
let ultimoAnalisis = null

function mostrarResultados(data) {
    ultimoAnalisis = data
    ...
}
```

Al pulsar "Analizar otro vídeo", `ultimoAnalisis` se resetea a `null` y el botón PDF se oculta.

### Visibilidad del botón PDF
El botón solo aparece cuando hay detecciones reales. Si el análisis no detecta ningún logo, no tiene sentido ofrecer un PDF vacío:
```javascript
if (!data.detecciones || data.detecciones.length === 0) {
    // muestra mensaje de no detecciones, NO muestra btnPDF
    return
}
document.getElementById("btnPDF").style.display = "block"
```

### Estructura del PDF generado
El PDF tiene fondo negro y estética gamer coherente con el frontend:

1. **Cabecera** — título "GAMELOGO DETECTOR" en cian neón, subtítulo en morado tenue
2. **Metadatos** — nombre del vídeo, duración y fecha del análisis
3. **Tabla de detecciones** — una fila por marca con barra de porcentaje coloreada
4. **Total** — duración total del vídeo en verde neón
5. **Footer** — créditos en la parte inferior

### Barras de porcentaje en el PDF
Cada fila tiene una barra de fondo que representa visualmente el porcentaje de aparición:
```javascript
// Fondo de fila oscuro
doc.setFillColor(20, 20, 40)
doc.rect(15, y - 5, 180, 8, "F")

// Barra coloreada proporcional al porcentaje
const barWidth = Math.min((d.porcentaje / 100) * 180, 180)
doc.setFillColor(...rgb)  // color de la marca
doc.setGState(new doc.GState({ opacity: 0.25 }))
doc.rect(15, y - 5, barWidth, 8, "F")
doc.setGState(new doc.GState({ opacity: 1 }))  // restaurar opacidad
```

El `Math.min(..., 180)` evita que la barra se salga del área si el porcentaje fuera mayor del esperado. La opacidad al 25% permite que el texto encima sea legible.

### Colores por marca en el PDF
jsPDF trabaja con RGB, no con hex, así que se define un mapa separado:
```javascript
const COLORES_RGB = {
    fortnite:          [191, 0, 255],
    genshin_impact:    [0, 245, 255],
    league_of_legends: [200, 155, 60],
    minecraft:         [0, 255, 136],
    valorant:          [255, 0, 60],
    vrchat:            [255, 102, 0],
}
```

### Nombre del archivo descargado
```javascript
const nombreArchivo = `informe_${data.video.replace(/\.[^.]+$/, "")}_${Date.now()}.pdf`
doc.save(nombreArchivo)
```

Se elimina la extensión del vídeo con la regex `/\.[^.]+$/` y se añade un timestamp para que cada descarga tenga nombre único. Ejemplo: `informe_test_video_1718123456789.pdf`.

---

## 11. Docker

### `Dockerfile`
```dockerfile
FROM python:3.13-slim

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data.yaml .

RUN mkdir -p /app/database /app/runs

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

- `libgl1` y `libglib2.0-0` son dependencias del sistema que necesita OpenCV en Linux
- Los pesos del modelo (`runs/`) **no se copian** en la imagen — se montan como volumen
- Se crean las carpetas `database/` y `runs/` vacías para que existan en el contenedor

### `docker-compose.yml`
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./database:/app/database   # la BD persiste fuera del contenedor
      - ./runs:/app/runs           # los pesos se montan desde el host
    restart: unless-stopped
```

Los volúmenes son clave:
- `database/` → si el contenedor se reinicia, los análisis guardados no se pierden
- `runs/` → los pesos del modelo se leen desde el host, no hay que reconstruir la imagen para cambiarlos

### `.dockerignore`
Excluye del build: el dataset, los vídeos de prueba, la BD local, `__pycache__`, `.git` y los `.md`. Esto hace el build más rápido y la imagen más ligera.

---

## 12. Control de versiones — decisiones de .gitignore

| Excluido | Motivo |
|---|---|
| `*.pt`, `*.onnx` | Archivos binarios de cientos de MB |
| `runs/` | Contiene los pesos, ya ignorados por `*.pt` |
| `dataset/images/train/*/` | Cientos de imágenes, no van en el repo |
| `database/*.db` | Datos de runtime, se genera automáticamente |
| `*.mp4`, `*.webm`, etc. | Vídeos de prueba, demasiado pesados |
| `GUIA_TECNICA.md` | Documento interno, no relevante para el repo |
| `src/app.py` | Interfaz Streamlit alternativa, no se usa en producción |

Las carpetas vacías necesarias (`database/`, `dataset/images/val/`) se trackean con archivos `.gitkeep` para que existan al clonar el repo.

---

## 14. Nuevas funcionalidades post code review

### 14.1 Validación de confianza en la API (`src/api.py`)

El slider del frontend envía la confianza como valor entre 0 y 1 (divide el valor del slider entre 100). Sin validación en el backend, un valor fuera de rango llegaría directamente a YOLOv8 y podría causar comportamientos inesperados.

```python
if not 0 < confianza <= 1:
    raise HTTPException(status_code=422, detail="La confianza debe estar entre 0 y 1")
```

Se usa `0 < confianza <= 1` en lugar de `0 <= confianza <= 1` porque una confianza de 0 significaría aceptar cualquier detección sin importar la certeza del modelo, lo que generaría resultados sin sentido.

**Código de error:** 422 Unprocessable Entity, el estándar HTTP para datos de entrada inválidos.

---

### 14.2 Soporte real de extensiones de vídeo (`src/api.py`)

Antes, el archivo temporal siempre se creaba con extensión `.mp4` independientemente del formato subido. OpenCV usa la extensión del archivo para elegir el decodificador, por lo que un `.webm` guardado como `.mp4` podía fallar al abrirse.

```python
ext = os.path.splitext(video.filename)[-1].lower() or ".mp4"
EXTENSIONES_VALIDAS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
if ext not in EXTENSIONES_VALIDAS:
    raise HTTPException(status_code=415, detail=f"Formato no soportado: {ext}")

with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
```

- `os.path.splitext(video.filename)[-1]` extrae la extensión del nombre original del archivo
- `.lower()` normaliza a minúsculas para que `.MP4` y `.mp4` sean equivalentes
- `or ".mp4"` es el fallback si el archivo no tiene extensión
- El set `EXTENSIONES_VALIDAS` permite la búsqueda en O(1)
- **Código de error:** 415 Unsupported Media Type, el estándar HTTP para formato no soportado

---

### 14.3 Manejo de errores de la API en el frontend (`frontend/app.js`)

Antes, si la API devolvía un error (422, 413, 415), el frontend intentaba llamar a `mostrarResultados(data)` con un objeto `{ detail: "..." }` en lugar de `{ detecciones: [...] }`, lo que causaba un fallo silencioso. Además, los errores se mostraban con `alert()`, que es un cuadro de diálogo nativo del navegador, bloqueante y sin ningún estilo.

**Solución: toast animado con frases gamer**

Se sustituyeron todos los `alert()` por un sistema de notificaciones propio con estilo coherente al frontend. El toast es un `div` fijo en la parte inferior de la pantalla que aparece con animación y desaparece solo a los 4 segundos.

**Mapa de errores (`ERRORES`):**
```javascript
const ERRORES = {
    nofile: {
        emoji: "👀",
        msg: "Oye, que no has seleccionado ningún vídeo...",
        sub: "Arrastra un vídeo o usa el botón de selección"
    },
    413: {
        emoji: "🐘",
        msg: "Ese vídeo pesa más que un Creeper cargado de TNT",
        sub: "Máximo permitido: 500MB"
    },
    415: {
        emoji: "🤔",
        msg: "Ese formato no lo reconozco ni con wall hack activado",
        sub: "Formatos válidos: mp4, avi, mov, mkv, webm"
    },
    422: {
        emoji: "🎯",
        msg: "La confianza tiene que estar entre 10% y 90%, no seas extremista",
        sub: "Ajusta el slider e inténtalo de nuevo"
    },
    default: {
        emoji: "💀",
        msg: "Algo salió mal... como cuando te matan en la zona segura",
        sub: "Recarga la página e inténtalo de nuevo"
    }
}
```

Cada clave del objeto corresponde a un código HTTP o a un caso especial (`nofile`, `default`). Usar un objeto en lugar de un `switch` o varios `if` es más limpio y fácil de ampliar.

**Función `mostrarError(status)`:**
```javascript
function mostrarError(status) {
    const info = ERRORES[status] || ERRORES.default
    document.getElementById("errorEmoji").textContent = info.emoji
    document.getElementById("errorMsg").textContent = info.msg
    document.getElementById("errorSub").textContent = info.sub
    const toast = document.getElementById("errorToast")
    toast.classList.add("visible")
    clearTimeout(errorTimer)
    errorTimer = setTimeout(() => toast.classList.remove("visible"), 4000)
}
```

- `ERRORES[status] || ERRORES.default` → si el código no está en el mapa, usa el mensaje genérico
- `clearTimeout(errorTimer)` → si el usuario provoca dos errores seguidos rápido, reinicia el temporizador en lugar de acumular timeouts
- La animación es solo CSS: la clase `visible` cambia `translateY(100px)` a `translateY(0)` con `cubic-bezier` para efecto de rebote

**Dónde se llama:**
```javascript
if (!input.files[0]) { mostrarError("nofile"); return }
// ...
if (!res.ok) { mostrarError(res.status); return }
// ...
catch (e) { mostrarError("default") }
```

`res.ok` es `true` solo cuando el código HTTP está entre 200 y 299. `res.status` devuelve el número exacto (413, 415, 422...) que se usa como clave en `ERRORES`.

**CSS del toast (`frontend/style.css`):**
```css
.error-toast {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%) translateY(100px); /* oculto abajo */
    transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    ...
}
.error-toast.visible {
    transform: translateX(-50%) translateY(0); /* visible */
}
```

El truco de la animación es solo cambiar el `transform` con una transición CSS. No hay JavaScript de animación, solo añadir/quitar la clase `visible`.

---

### 14.4 Exportar historial a CSV (`frontend/app.js`)

El CSV se genera íntegramente en el navegador sin ningún endpoint nuevo en el backend. Los datos ya están en `ultimoHistorial` desde la última llamada a `cargarHistorial()`.

```javascript
let ultimoHistorial = null  // se rellena al cargar el historial

function descargarCSV() {
    const cabecera = ["video", "clase", "tiempo_s", "porcentaje", "duracion_video_s", "fecha"]
    const filas = ultimoHistorial.map(r => [
        `"${r.video}"`,   // entre comillas por si el nombre tiene comas
        r.clase,
        r.tiempo,
        r.porcentaje,
        r.duracion_video,
        `"${r.fecha}"`
    ].join(","))

    const csv = [cabecera.join(","), ...filas].join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `historial_gamelogo_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
}
```

**Por qué `Blob` y no un link directo:**
No hay una URL real que apunte a un archivo en el servidor. `Blob` crea un objeto en memoria del navegador, `URL.createObjectURL` genera una URL temporal que apunta a ese objeto, y `a.click()` simula el click en un enlace de descarga. `URL.revokeObjectURL` libera la memoria una vez descargado.

**Por qué las comillas en `video` y `fecha`:**
El nombre del vídeo puede contener comas (ej: `stream, parte 1.mp4`) que romperían el formato CSV. Envolverlos en comillas dobles es el estándar RFC 4180 para campos con comas.

**Visibilidad del botón:**
El botón CSV solo aparece después de cargar el historial y solo si hay registros. Si el historial está vacío, el botón se oculta:
```javascript
if (data.length === 0) {
    document.getElementById("btnCSV").style.display = "none"
    return
}
document.getElementById("btnCSV").style.display = "block"
```

---

## 13. Fixes aplicados durante el code review

Durante la revisión del código se corrigieron estos problemas:

| Archivo | Problema | Solución |
|---|---|---|
| `api.py` | `await video.read()` cargaba el vídeo entero en RAM | `shutil.copyfileobj` en chunks |
| `api.py` | Archivo temporal no se borraba si había error | `try/finally` con `os.unlink` |
| `api.py` | Sin límite de tamaño en subidas | Validación de `video.size` con límite de 500MB |
| `api.py` | CORS `allow_origins=["*"]` | Restringido a `localhost:8000` |
| `detect_video.py` | `cap.release()` no se llamaba si había excepción | `try/finally` |
| `detect_video.py` | No se validaba que el vídeo se abriera | `if not cap.isOpened(): raise ValueError` |
| `detect_video.py` | Frame skip sobrecontaba al final del vídeo | `min(frame_skip, frames_restantes)` |
| `database.py` | `DetachedInstanceError` al acceder a objetos ORM fuera de sesión | `session.expunge_all()` |
| `download_images.py` | `except: pass` silenciaba todos los errores | `except requests.RequestException` |
| `app.js` | `event` global implícito en `showTab` | Pasar `event` como parámetro |
| `index.html` | `display:none` duplicado en `btnNuevo` | Eliminado el duplicado |
| `Dockerfile` | `COPY database/` incluía la BD en la imagen | Eliminado, se crea con `mkdir` |
| `requirements.txt` | `streamlit` y `pandas` en producción | Eliminados |

---

## 15. Guía de presentación (10 minutos)

Esta sección es para defender el proyecto en público. Cada slide tiene su tiempo asignado y las posibles preguntas que pueden surgir con sus respuestas.

---

### Slide 1 — Portada (30 seg)

**Lo que dices:**
> "GameLogo Detector. Un sistema de IA que analiza vídeos de streams y detecta cuánto tiempo aparece cada logo de videojuego en pantalla."

**Si preguntan:** ¿Para qué sirve esto en la vida real?
> "Las marcas pagan por aparecer en streams. Este sistema mide exactamente cuánto tiempo aparecieron, de forma automática, sin que nadie tenga que contarlo a mano."

---

### Slide 2 — El problema (1 min)

**Lo que dices:**
> "El mercado de publicidad en esports mueve más de 1.800 millones de dólares al año. Las marcas invierten en aparecer en streams y gameplays, pero no tienen forma automatizada de saber cuánto tiempo apareció realmente su logo. Hasta ahora se medía a ojo o con herramientas genéricas que no entienden el contexto gaming."

**Si preguntan:** ¿Ese dato de 1.800M es real?
> "Sí, es el tamaño del mercado global de publicidad en esports según Newzoo 2023. No es algo que calcule el proyecto, es el contexto de negocio que justifica por qué esto tiene valor."

---

### Slide 3 — La solución (1 min)

**Lo que dices:**
> "El pipeline es: subimos un vídeo, OpenCV lo lee frame a frame, YOLOv8 detecta los logos en cada frame, calculamos el tiempo de aparición, lo guardamos en base de datos y lo mostramos en la web."

**Si preguntan:** ¿Por qué YOLOv8 y no otro modelo?
> "YOLO es el estándar para detección de objetos en tiempo real. Usamos la variante nano, YOLOv8n, porque es la más rápida en CPU y para detectar logos no necesitamos un modelo más grande."

**Si preguntan:** ¿Analiza en tiempo real?
> "No, analiza vídeos pregrabados. Procesa el vídeo completo y genera el informe al terminar. El análisis en tiempo real de streams en vivo sería una mejora futura."

---

### Slide 4 — El dataset (1 min)

**Lo que dices:**
> "No usamos un dataset genérico. Lo construimos desde cero. Descargamos 80 imágenes por juego con un script de Python usando DuckDuckGo, las anotamos manualmente en Roboflow dibujando bounding boxes, aplicamos data augmentation y pasamos de 480 a 556 imágenes."

**Si preguntan:** ¿Qué es data augmentation?
> "Es multiplicar las imágenes aplicando transformaciones: voltear la imagen en espejo, rotarla ligeramente, cambiar el brillo. Así el modelo aprende a reconocer el logo en distintas condiciones sin necesitar más fotos reales."

**Si preguntan:** ¿Por qué solo 80 imágenes por juego?
> "Con transfer learning no necesitamos miles de imágenes. Partimos de un modelo que ya sabe detectar objetos genéricos y solo lo afinamos con nuestros logos. 80 imágenes por clase es suficiente para obtener buenos resultados."

---

### Slide 5 — Las 6 marcas (30 seg)

**Lo que dices:**
> "Detectamos 6 marcas: League of Legends, Valorant, Fortnite, Genshin Impact, Minecraft y VRChat. Cada una tiene su color característico en la interfaz."

**Si preguntan:** ¿Por qué estos juegos?
> "Son los más populares en Twitch y YouTube Gaming. Representan distintos géneros y estilos visuales, lo que hace el dataset más variado y el modelo más robusto."

**Si preguntan:** ¿Se pueden añadir más juegos?
> "Sí, el sistema está diseñado para escalar. Solo hay que añadir imágenes del nuevo logo, anotarlas en Roboflow y reentrenar. El código no necesita cambios."

---

### Slide 6 — Cómo funciona (1 min)

**Lo que dices:**
> "OpenCV abre el vídeo y lo lee frame a frame. Con frame skip x3 analizamos 1 de cada 3 frames, lo que reduce el tiempo de análisis un 66% sin perder precisión porque los logos no cambian de un frame al siguiente. YOLOv8 infiere en cada frame seleccionado, detecta qué logos hay y con qué confianza. Acumulamos los frames detectados, calculamos segundos y porcentaje, y guardamos en SQLite."

**Si preguntan:** ¿Qué es frame skip?
> "En lugar de analizar los 30 frames por segundo de un vídeo, analizamos 1 de cada 3. Los logos son estáticos, no se mueven rápido, así que no perdemos información relevante y el análisis es 3 veces más rápido."

**Si preguntan:** ¿Qué es confianza?
> "Es el porcentaje de certeza del modelo. Si ponemos confianza mínima al 50%, solo contamos las detecciones donde el modelo está al menos un 50% seguro de que es ese logo. Se puede ajustar desde el slider de la web."

---

### Slide 7 — Stack tecnológico (30 seg)

**Lo que dices:**
> "Python como lenguaje principal. YOLOv8n para la detección. OpenCV para procesar el vídeo. FastAPI para la API REST. SQLAlchemy con SQLite para la base de datos. HTML, CSS y JS puros para el frontend, sin frameworks. Docker para el despliegue."

**Si preguntan:** ¿Por qué FastAPI y no Flask o Django?
> "FastAPI es asíncrono, tiene tipado automático y genera documentación en /docs sin configuración. Para una API de este tipo es la opción más moderna y eficiente en Python."

**Si preguntan:** ¿Por qué SQLite y no PostgreSQL?
> "SQLite es suficiente para este caso de uso. No hay concurrencia alta, no hay múltiples usuarios simultáneos. Es portable, no necesita servidor separado y funciona igual en local que en Docker."

---

### Slide 8 — Decisiones técnicas (1 min)

**Lo que dices:**
> "Cuatro decisiones clave: YOLOv8n en lugar de s o m porque es más rápido en CPU con suficiente precisión para logos. Frame skip x3 para reducir el tiempo de análisis. SQLite sin infraestructura extra. Y FastAPI con documentación automática."

**Si preguntan:** ¿Qué diferencia hay entre YOLOv8n, s, m?
> "Son variantes del mismo modelo con distinto tamaño. Nano es el más pequeño y rápido, Small es intermedio, Medium es más preciso pero más lento. Para logos estáticos, nano es suficiente."

---

### Slide 9 — Demo y resultados (3 min)

**Pasos de la demo:**
1. Arrancar el servidor: `cd src && uvicorn api:app --reload`
2. Abrir `http://localhost:8000`
3. Subir `test_video.mp4`
4. Mostrar el análisis en curso (barra de progreso)
5. Mostrar las cards con resultados
6. Descargar el PDF
7. Ir a Historial y exportar CSV

**Si la demo falla:** Mostrar el ejemplo del README:
```
valorant        8.07s   15.07%
minecraft       5.21s    9.71%
league_of_legends 1.57s  2.93%
```

**Si preguntan:** ¿Por qué tarda tanto en analizar?
> "Estamos en CPU. Con GPU el análisis sería 10-20 veces más rápido. En producción se desplegaría con GPU o se usaría un servicio cloud con aceleración hardware."

---

### Slide 10 — Cierre (30 seg)

**Lo que dices:**
> "Dataset propio, modelo entrenado con transfer learning, API REST, base de datos, frontend gamer, exportación a PDF y CSV, Docker listo para despliegue. Todo construido desde cero. El núcleo del sistema está completo y funcionando. Las mejoras naturales serían integración con la API de Twitch para descargar VODs automáticamente y análisis en tiempo real."

---

## 16. Prompt de Canva (actualizado)

Copia este prompt en el chat de Canva AI para generar la presentación:

```
Crea una presentación de 10 diapositivas con estética gamer oscura y cyberpunk.
Paleta de colores: fondo negro profundo (#050510), cian neón (#00f5ff),
morado neón (#bf00ff), verde neón (#00ff88), rojo neón (#ff003c).
Tipografía Orbitron o similar futurista para títulos, Rajdhani o sans-serif
para cuerpo. Efectos de brillo neón, partículas flotantes y textura de
líneas de escaneo en todas las diapositivas.
IMPORTANTE: todos los personajes, logos e imágenes de juegos deben ser
exclusivamente de estos 6 juegos: League of Legends, Valorant, Fortnite,
Genshin Impact, Minecraft y VRChat. No usar imágenes de otros juegos.

Diapositiva 1 - Portada
Título "GAMELOGO DETECTOR" en grande con efecto glitch en cian neón.
Subtítulo: "Detección automática de logos en vídeos con IA".
Fondo con collage semitransparente de: Jinx o Vi de League of Legends,
un agente de Valorant con su traje táctico, un Creeper de Minecraft,
el cubo de Fortnite o Jonesy, Paimon de Genshin Impact, avatar de VRChat.
Efecto de desenfoque oscuro sobre los personajes para que no tapen el texto.
Autor: "por Karina" en esquina inferior derecha en morado neón.

Diapositiva 2 - El Problema
Fondo oscuro con silueta semitransparente de un streamer.
Texto: "El mercado de publicidad en esports mueve 1.800M$ al año...
y se mide a ojo." Número "1.800M$" enorme en rojo neón.
Icono de lupa o persona contando con tachado encima.
Pequeños logos de los 6 juegos del dataset flotando en el fondo muy tenues.

Diapositiva 3 - La Solución
Diagrama de pipeline horizontal con iconos conectados por flechas neón:
🎬 Vídeo → 🧠 YOLOv8 → 📊 Informe → 🗄️ Base de datos → 🌐 Web
Fondo con partículas y borde de tarjeta en cian neón brillante.
Logos pequeños de League of Legends, Valorant, Fortnite, Genshin Impact,
Minecraft y VRChat flotando alrededor del pipeline.

Diapositiva 4 - El Dataset
Fondo con cuadrícula estilo matrix en verde muy oscuro.
Tres columnas con iconos grandes:
📸 "480 imágenes scrapeadas" → icono DuckDuckGo
🏷️ "Anotadas en Roboflow" → bounding boxes dibujados sobre un logo
🔀 "556 imágenes finales" → iconos de flip, rotación, brillo
Logos de los 6 juegos del dataset en la parte inferior como decoración:
League of Legends, Valorant, Fortnite, Genshin Impact, Minecraft, VRChat.

Diapositiva 5 - Las 6 Marcas Detectadas
Título: "MARCAS DETECTADAS" en cian neón.
Cuadrícula 2x3 de tarjetas con fondo oscuro y borde del color de cada marca.
Cada tarjeta tiene logo oficial + nombre + color característico:
⚔️ League of Legends → borde dorado (#c89b3c), logo LoL con el escudo
🔴 Valorant → borde rojo (#ff003c), logo Valorant con la V
🟣 Fortnite → borde morado (#bf00ff), logo Fortnite
🔵 Genshin Impact → borde cian (#00f5ff), logo Genshin con el símbolo
🟢 Minecraft → borde verde (#00ff88), logo Minecraft con el Creeper
🟠 VRChat → borde naranja (#ff6600), logo VRChat

Diapositiva 6 - Cómo Funciona
Diagrama de arquitectura vertical con capas estilo HUD de videojuego:
Capa 1: 🎬 OpenCV — lee el vídeo frame a frame (frame skip x3)
Capa 2: 🧠 YOLOv8n — detecta logos con bounding boxes
Capa 3: ⚡ FastAPI — sirve la API REST
Capa 4: 🗄️ SQLite — guarda el historial
Capa 5: 🌐 Frontend — muestra resultados, PDF y CSV
Flechas neón entre capas. Fondo con personaje de Valorant o LoL
muy oscuro y desenfocado a la derecha.

Diapositiva 7 - Stack Tecnológico
Título: "ARSENAL TECNOLÓGICO" en morado neón.
Cuadrícula de 6 tarjetas con icono real de cada tecnología:
YOLOv8n 🧠 — Detección de objetos
OpenCV 👁️ — Procesado de vídeo
FastAPI ⚡ — API REST
SQLAlchemy 🗄️ — Base de datos
Docker 🐳 — Despliegue
Roboflow 🏷️ — Anotación y augmentation
Fondo con efecto de código cayendo estilo matrix muy sutil.

Diapositiva 8 - Decisiones Técnicas
Título: "POR QUÉ ESTAS DECISIONES" en cian neón.
4 tarjetas horizontales con borde izquierdo neón de color distinto:
⚡ YOLOv8n → más rápido en CPU, suficiente precisión para logos
🎬 Frame skip x3 → 66% menos tiempo de análisis
🗄️ SQLite → sin infraestructura extra, portable
🌐 FastAPI → async, tipado, documentación automática en /docs
Fondo oscuro con Creeper de Minecraft o logo de Fortnite muy desenfocado.

Diapositiva 9 - Resultados Reales
Título: "INFORME REAL DE DETECCIONES" en verde neón.
Gráfico de barras horizontales con los colores de cada marca:
valorant          ████████████████  8.07s  15.07%  (barra roja)
minecraft         ██████████        5.21s   9.71%  (barra verde)
league_of_legends ████              1.57s   2.93%  (barra dorada)
fortnite          ██                0.93s   1.74%  (barra morada)
genshin_impact    █                 0.47s   0.87%  (barra cian)
Duración total del vídeo: 53.57s en esquina inferior.
Logo pequeño de cada juego junto a su barra correspondiente.
Iconos de PDF y CSV en esquina indicando que se pueden exportar.

Diapositiva 10 - Cierre
Fondo oscuro con collage muy desenfocado y semitransparente de personajes
de los 6 juegos del dataset: Jinx de LoL, agente de Valorant, Creeper de
Minecraft, Jonesy de Fortnite, Paimon de Genshin Impact, avatar de VRChat.
Texto central grande en neón:
"DATASET PROPIO. MODELO REAL. VALOR DE NEGOCIO."
Debajo más pequeño: "Detección · Análisis · Historial · PDF · CSV · Docker"
Abajo del todo: "GameLogo Detector — por Karina" en morado neón.
```
