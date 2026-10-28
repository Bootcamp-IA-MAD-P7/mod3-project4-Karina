# 🎮 Computer Vision - Detección de Logos de Videojuegos

Modelo de detección de logos de videojuegos en vídeos usando YOLOv8.

## 🎯 Marcas detectadas
- League of Legends
- Valorant
- Fortnite
- Genshin Impact
- Minecraft
- VRChat

## 📁 Estructura
```
computer-vision/
├── dataset/
│   ├── images/
│   │   ├── train/
│   │   └── val/
│   └── labels/
│       ├── train/
│       └── val/
├── src/
│   ├── train.py
│   ├── detect_video.py
│   ├── database.py
│   └── api.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── database/
├── runs/
├── data.yaml
├── requirements.txt
└── README.md
```

## ⚙️ Instalación
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Entrenar el modelo
```bash
python src/train.py
```

### Analizar un vídeo
```bash
python src/detect_video.py --video ruta/al/video.mp4
```

### Lanzar la app web
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Abre el navegador en `http://localhost:8000`

## 🛠️ Tecnologías
- YOLOv8 (Ultralytics)
- OpenCV
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- HTML/CSS/JavaScript
- Docker
