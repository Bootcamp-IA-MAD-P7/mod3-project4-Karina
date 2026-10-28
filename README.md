<div align="center">

# 🎮 GameLogo Detector

**Detección de logos de videojuegos en vídeos usando Inteligencia Artificial**

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?style=for-the-badge&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-00ff88?style=for-the-badge)

<br>

> *"Un sistema de IA que analiza vídeos, detecta logos de videojuegos y genera informes de aparición en pantalla."*

</div>

---

## 🕹️ ¿Qué hace este proyecto?

Una empresa de publicidad quiere saber **cuánto tiempo aparecen sus marcas** en streams y gameplays. Este sistema analiza vídeos automáticamente y genera un informe con el tiempo y porcentaje de aparición de cada logo.

```
📹 Vídeo  ──►  🧠 YOLOv8  ──►  📊 Informe  ──►  🗄️ SQLite  ──►  🌐 Web
```

---

## 🎯 Marcas detectadas

| | Juego | Color característico |
|---|---|---|
| ⚔️ | **League of Legends** | ![#c89b3c](https://placehold.co/15x15/c89b3c/c89b3c.png) Dorado |
| 🔴 | **Valorant** | ![#ff003c](https://placehold.co/15x15/ff003c/ff003c.png) Rojo |
| 🟣 | **Fortnite** | ![#bf00ff](https://placehold.co/15x15/bf00ff/bf00ff.png) Morado |
| 🔵 | **Genshin Impact** | ![#00f5ff](https://placehold.co/15x15/00f5ff/00f5ff.png) Cyan |
| 🟢 | **Minecraft** | ![#00ff88](https://placehold.co/15x15/00ff88/00ff88.png) Verde |
| 🟠 | **VRChat** | ![#ff6600](https://placehold.co/15x15/ff6600/ff6600.png) Naranja |

---

## 🧠 ¿Cómo funciona la IA?

```
┌─────────────────────────────────────────────────────────┐
│                    PIPELINE DE IA                        │
│                                                         │
│  480 imgs  ──►  Roboflow  ──►  556 imgs  ──►  YOLOv8   │
│  (scraping)    (anotación +    (augmented)   (training) │
│                augmentation)                            │
└─────────────────────────────────────────────────────────┘
```

- 🔍 **Transfer Learning** sobre YOLOv8n preentrenado
- 🏷️ **Dataset propio** de 480 imágenes recolectadas con script Python
- 📈 **Data augmentation** → flip, rotación ±15°, brillo ±25%
- 🎯 **556 imágenes** finales para entrenamiento
- ⏱️ **50 épocas** de entrenamiento

---

## 🛠️ Stack tecnológico

<div align="center">

| Tecnología | Versión | Uso |
|---|---|---|
| 🧠 **YOLOv8** | 8.4 | Detección de objetos |
| 👁️ **OpenCV** | 5.0 | Procesado de vídeo frame a frame |
| ⚡ **FastAPI** | 0.162 | Backend y API REST |
| 🗄️ **SQLAlchemy** | 2.1 | ORM para base de datos |
| 🌐 **HTML/CSS/JS** | - | Frontend gamer personalizado |
| 🐳 **Docker** | - | Contenedorización |
| 🏷️ **Roboflow** | - | Anotación y data augmentation |
| 🔎 **DuckDuckGo API** | - | Scraping de imágenes |

</div>

---

## 📊 Ejemplo de informe

```
📋 INFORME DE DETECCIONES
=============================================
Marca                Tiempo    Porcentaje
---------------------------------------------
valorant              8.07s       15.07%
minecraft             5.21s        9.71%
league_of_legends     1.57s        2.93%
fortnite              0.93s        1.74%
genshin_impact        0.47s        0.87%
=============================================
Duración total       53.57s
```

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Bootcamp-IA-MAD-P7/mod3-project4-Karina.git
cd mod3-project4-Karina

# 2. Crear entorno virtual
python -m venv .venv
source .venv/Scripts/activate  # Windows
source .venv/bin/activate       # Mac/Linux

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## 🚀 Uso

### 🔽 Descargar imágenes para el dataset
```bash
python src/download_images.py
```

### 🧠 Entrenar el modelo
```bash
python src/train.py
```

### 🎬 Analizar un vídeo por terminal
```bash
python src/detect_video.py --video ruta/al/video.mp4
```

### 🌐 Lanzar la app web
```bash
cd src
uvicorn api:app --reload
```
Abre `http://localhost:8000` en el navegador 🎮

### 🐳 Docker
```bash
docker-compose up --build
```

---

## 📁 Estructura del proyecto

```
computer-vision/
├── 📂 src/
│   ├── 🔽 download_images.py  → descarga imágenes automáticamente
│   ├── 🧠 train.py            → entrena YOLOv8
│   ├── 🎬 detect_video.py     → analiza vídeos frame a frame
│   ├── 🗄️  database.py        → gestión SQLite con SQLAlchemy
│   └── ⚡ api.py              → servidor FastAPI
├── 📂 frontend/
│   ├── 🌐 index.html          → estructura de la web
│   ├── 🎨 style.css           → diseño gamer oscuro con neones
│   └── ⚙️  app.js             → lógica del frontend
├── 📂 dataset/                → imágenes de entrenamiento
├── 📂 runs/                   → modelos entrenados
├── 📂 database/               → base de datos SQLite
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── ⚙️  data.yaml              → configuración del dataset
└── 📋 requirements.txt
```

---

## 🏆 Niveles completados

- ✅ **Nivel Esencial** → modelo entrenado con bounding boxes visibles
- ✅ **Nivel Medio** → detección en vídeos con nombre de clase
- ✅ **Nivel Avanzado** → porcentaje de confianza + base de datos + multimarca
- ✅ **Nivel Experto** → frontend propio + API REST con FastAPI

---

<div align="center">

**Hecho con ❤️ y mucho ☕ por Karina**

![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?style=flat-square&logo=python)
![YOLOv8](https://img.shields.io/badge/Powered%20by-YOLOv8-purple?style=flat-square)
![Gamer](https://img.shields.io/badge/100%25-Gamer-ff003c?style=flat-square)

</div>
