import os
import sys
import shutil
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timezone

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_PATH = os.path.join(BASE_DIR, "runs", "detect", "runs", "videogame-logos-3", "weights", "best.pt")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
MAX_UPLOAD_MB = 500

sys.path.append(os.path.dirname(__file__))
from detect_video import analizar_video, cargar_modelo
from database import guardar_detecciones, obtener_detecciones
from auth.routes import router as auth_router
from auth.jwt import get_current_user
from db.models import Base, User, Video, Detection, Brand, VideoStatusEnum
from db.session import engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Videogame Logo Detector")
app.include_router(auth_router)

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

PLAN_LIMITS = {"free": 3, "pro": None, "agency": None}


@app.post("/analizar")
async def analizar(
    video: UploadFile = File(...),
    confianza: float = 0.5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not 0 < confianza <= 1:
        raise HTTPException(status_code=422, detail="La confianza debe estar entre 0 y 1")

    if video.size and video.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"El vídeo supera el límite de {MAX_UPLOAD_MB}MB")

    ext = os.path.splitext(video.filename)[-1].lower() or ".mp4"
    if ext not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        raise HTTPException(status_code=415, detail=f"Formato no soportado: {ext}")

    # Validar cuota del plan
    plan = current_user.subscription.plan.value if current_user.subscription else "free"
    limit = PLAN_LIMITS.get(plan)
    if limit is not None:
        now = datetime.now(timezone.utc)
        videos_este_mes = db.query(Video).filter(
            Video.user_id == current_user.id,
            Video.uploaded_at >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ).count()
        if videos_este_mes >= limit:
            raise HTTPException(status_code=429, detail=f"Límite del plan {plan}: {limit} vídeos/mes alcanzado")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        informe, duracion = analizar_video(tmp_path, MODELO_PATH, confianza)
    finally:
        os.unlink(tmp_path)

    # Guardar en PostgreSQL asociado al usuario
    video_record = Video(
        user_id=current_user.id,
        filename=video.filename,
        duration=round(duracion, 2),
        status=VideoStatusEnum.done
    )
    db.add(video_record)
    db.flush()

    detecciones_resultado = []
    for clase, datos in informe.items():
        if datos["frames"] > 0:
            # Buscar o crear Brand para este usuario
            brand = db.query(Brand).filter(Brand.user_id == current_user.id, Brand.name == clase).first()
            if not brand:
                brand = Brand(user_id=current_user.id, name=clase, display_name=clase.replace("_", " ").title())
                db.add(brand)
                db.flush()
            db.add(Detection(
                video_id=video_record.id,
                brand_id=brand.id,
                time_seconds=round(datos["tiempo"], 2),
                percentage=round(datos["porcentaje"], 2)
            ))
            detecciones_resultado.append({
                "clase": clase,
                "tiempo": round(datos["tiempo"], 2),
                "porcentaje": round(datos["porcentaje"], 2)
            })

    db.commit()
    guardar_detecciones(video.filename, informe, duracion)  # mantiene SQLite legacy

    return {
        "video": video.filename,
        "duracion": round(duracion, 2),
        "detecciones": detecciones_resultado
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


@app.get("/auth/mis-videos")
def mis_videos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.user_id == current_user.id).order_by(Video.uploaded_at.desc()).all()
    return [
        {
            "id": v.id,
            "filename": v.filename,
            "duration": v.duration,
            "status": v.status.value,
            "uploaded_at": v.uploaded_at.strftime("%d/%m/%Y %H:%M"),
            "detecciones": [
                {
                    "clase": d.brand.name,
                    "tiempo": d.time_seconds,
                    "porcentaje": d.percentage
                }
                for d in v.detections
            ]
        }
        for v in videos
    ]
