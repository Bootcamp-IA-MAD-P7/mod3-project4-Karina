import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Session
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "detecciones.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

class Base(DeclarativeBase):
    pass

class Deteccion(Base):
    __tablename__ = "detecciones"

    id = Column(Integer, primary_key=True)
    video = Column(String)
    clase = Column(String)
    tiempo_aparicion = Column(Float)
    porcentaje = Column(Float)
    duracion_video = Column(Float)
    fecha = Column(DateTime, default=datetime.now)

Base.metadata.create_all(engine)

def guardar_detecciones(nombre_video, informe, duracion_video):
    with Session(engine) as session:
        for clase, datos in informe.items():
            if datos["frames"] > 0:
                session.add(Deteccion(
                    video=nombre_video,
                    clase=clase,
                    tiempo_aparicion=round(datos["tiempo"], 2),
                    porcentaje=round(datos["porcentaje"], 2),
                    duracion_video=round(duracion_video, 2)
                ))
        session.commit()
    print(f"\n✅ Detecciones guardadas en la base de datos")

def obtener_detecciones(video=None):
    with Session(engine) as session:
        query = session.query(Deteccion)
        if video:
            query = query.filter(Deteccion.video == video)
        return query.all()
