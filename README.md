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
│   └── app.py
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
streamlit run src/app.py
```

## 🛠️ Tecnologías
- YOLOv8 (Ultralytics)
- OpenCV
- SQLAlchemy + SQLite
- Streamlit
