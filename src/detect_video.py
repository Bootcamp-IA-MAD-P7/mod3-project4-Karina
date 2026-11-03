import os
import cv2
import argparse
from ultralytics import YOLO
from collections import defaultdict

CLASES = ["fortnite", "genshin_impact", "league_of_legends", "minecraft", "valorant", "vrchat"]

def analizar_video(ruta_video, modelo_path="runs/detect/runs/videogame-logos-3/weights/best.pt", confianza=0.5, frame_skip=3):
    model = YOLO(modelo_path)
    cap = cv2.VideoCapture(ruta_video)

    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el vídeo: {ruta_video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duracion_total = total_frames / fps

    frames_detectados = defaultdict(int)
    frame_actual = 0

    print(f"\n🎬 Analizando: {ruta_video}")
    print(f"📊 Total frames: {total_frames} | FPS: {fps:.1f} | Duración: {duracion_total:.1f}s | Skip: {frame_skip}\n")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_actual % frame_skip == 0:
                resultados = model(frame, conf=confianza, verbose=False)
                clases_en_frame = set()

                for r in resultados:
                    for box in r.boxes:
                        clase_id = int(box.cls[0])
                        clase_nombre = CLASES[clase_id]
                        clases_en_frame.add(clase_nombre)

                frames_restantes = total_frames - frame_actual
                incremento = min(frame_skip, frames_restantes)
                for clase in clases_en_frame:
                    frames_detectados[clase] += incremento

            frame_actual += 1
            if frame_actual % 100 == 0:
                print(f"  Procesando... {frame_actual}/{total_frames} frames", end="\r")
    finally:
        cap.release()

    print("\n\n📋 INFORME DE DETECCIONES")
    print("=" * 45)
    print(f"{'Marca':<20} {'Tiempo':>8} {'Porcentaje':>10}")
    print("-" * 45)

    informe = {}
    for clase in CLASES:
        frames = frames_detectados.get(clase, 0)
        tiempo = frames / fps
        porcentaje = (frames / total_frames) * 100
        informe[clase] = {"frames": frames, "tiempo": tiempo, "porcentaje": porcentaje}
        if frames > 0:
            print(f"{clase:<20} {tiempo:>7.1f}s {porcentaje:>9.1f}%")

    print("=" * 45)
    print(f"{'Duración total':<20} {duracion_total:>7.1f}s")

    return informe, duracion_total

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Ruta al vídeo")
    parser.add_argument("--modelo", default="runs/detect/runs/videogame-logos-3/weights/best.pt")
    parser.add_argument("--confianza", type=float, default=0.5)
    parser.add_argument("--frame-skip", type=int, default=3)
    args = parser.parse_args()

    informe, duracion = analizar_video(args.video, args.modelo, args.confianza, args.frame_skip)
    from database import guardar_detecciones
    guardar_detecciones(os.path.basename(args.video), informe, duracion)
