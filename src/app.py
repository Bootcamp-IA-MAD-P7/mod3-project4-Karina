import streamlit as st
import tempfile
import os
import pandas as pd
import sys

sys.path.append(os.path.dirname(__file__))
from detect_video import analizar_video
from database import obtener_detecciones

st.set_page_config(page_title="🎮 Detector de Logos", layout="wide")
st.title("🎮 Detector de Logos de Videojuegos")

tab1, tab2 = st.tabs(["📤 Analizar Vídeo", "📊 Historial"])

with tab1:
    st.subheader("Sube un vídeo para analizar")
    video_file = st.file_uploader("Selecciona un vídeo", type=["mp4", "avi", "mov", "mkv"])
    confianza = st.slider("Confianza mínima", 0.1, 1.0, 0.5, 0.05)

    if video_file and st.button("🔍 Analizar", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(video_file.read())
            tmp_path = tmp.name

        with st.spinner("Analizando vídeo..."):
            modelo_path = "runs/detect/runs/videogame-logos-3/weights/best.pt"
            informe, duracion = analizar_video(tmp_path, modelo_path, confianza)

        os.unlink(tmp_path)

        st.success("✅ Análisis completado!")

        detecciones = {k: v for k, v in informe.items() if v["frames"] > 0}

        if detecciones:
            st.subheader("📋 Resultados")
            col1, col2 = st.columns(2)

            with col1:
                df = pd.DataFrame([
                    {"Marca": k, "Tiempo (s)": round(v["tiempo"], 1), "Porcentaje": f"{v['porcentaje']:.1f}%"}
                    for k, v in detecciones.items()
                ])
                st.dataframe(df, use_container_width=True)

            with col2:
                chart_data = {k: v["porcentaje"] for k, v in detecciones.items()}
                st.bar_chart(chart_data)
        else:
            st.warning("No se detectaron logos en el vídeo.")

with tab2:
    st.subheader("📊 Historial de análisis")
    registros = obtener_detecciones()

    if registros:
        df = pd.DataFrame([{
            "Vídeo": r.video,
            "Marca": r.clase,
            "Tiempo (s)": r.tiempo_aparicion,
            "Porcentaje": f"{r.porcentaje:.1f}%",
            "Duración vídeo": f"{r.duracion_video:.1f}s",
            "Fecha": r.fecha.strftime("%d/%m/%Y %H:%M")
        } for r in registros])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay análisis guardados.")
