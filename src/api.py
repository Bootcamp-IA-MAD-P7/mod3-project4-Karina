import os
import sys
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_PATH = os.path.join(BASE_DIR, "runs", "detect", "runs", "videogame-logos-3", "weights", "best.pt")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
MAX_UPLOAD_MB = 500

sys.path.append(os.path.dirname(__file__))
from detect_video import analizar_video, cargar_modelo
from database import guardar_detecciones, obtener_detecciones

app = FastAPI(title="Videogame Logo Detector")

@app.on_event("startup")
def startup():
    cargar_modelo(MODELO_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def root():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.post("/analizar")
async def analizar(video: UploadFile = File(...), confianza: float = 0.5):
    if not 0 < confianza <= 1:
        raise HTTPException(status_code=422, detail="La confianza debe estar entre 0 y 1")

    if video.size and video.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"El vídeo supera el límite de {MAX_UPLOAD_MB}MB")

    ext = os.path.splitext(video.filename)[-1].lower() or ".mp4"
    EXTENSIONES_VALIDAS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    if ext not in EXTENSIONES_VALIDAS:
        raise HTTPException(status_code=415, detail=f"Formato no soportado: {ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        informe, duracion = analizar_video(tmp_path, MODELO_PATH, confianza)
    finally:
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
