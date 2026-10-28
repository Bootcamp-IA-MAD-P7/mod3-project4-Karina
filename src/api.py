import os
import sys
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_PATH = os.path.join(BASE_DIR, "runs", "detect", "runs", "videogame-logos-3", "weights", "best.pt")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

sys.path.append(os.path.dirname(__file__))
from detect_video import analizar_video
from database import guardar_detecciones, obtener_detecciones

app = FastAPI(title="Videogame Logo Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

MODELO_PATH = os.path.join(BASE_DIR, "runs", "detect", "runs", "videogame-logos-3", "weights", "best.pt")

@app.get("/")
def root():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.post("/analizar")
async def analizar(video: UploadFile = File(...), confianza: float = 0.5):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(await video.read())
        tmp_path = tmp.name

    informe, duracion = analizar_video(tmp_path, MODELO_PATH, confianza)
    os.unlink(tmp_path)

    guardar_detecciones(video.filename, informe, duracion)

    return {
        "video": video.filename,
        "duracion": round(duracion, 2),
        "detecciones": [
            {
                "clase": clase,
                "tiempo": round(datos["tiempo"], 2),
                "porcentaje": round(datos["porcentaje"], 2)
            }
            for clase, datos in informe.items() if datos["frames"] > 0
        ]
    }

@app.get("/historial")
def historial():
    registros = obtener_detecciones()
    return [
        {
            "video": r.video,
            "clase": r.clase,
            "tiempo": r.tiempo_aparicion,
            "porcentaje": r.porcentaje,
            "duracion_video": r.duracion_video,
            "fecha": r.fecha.strftime("%d/%m/%Y %H:%M")
        }
        for r in registros
    ]
