import cv2
import argparse
from ultralytics import YOLO
from collections import defaultdict
from database import guardar_detecciones

CLASES = ["fortnite", "genshin_impact", "league_of_legends", "minecraft", "valorant", "vrchat"]

def analizar_video(ruta_video, modelo_path="runs/detect/runs/videogame-logos/weights/best.pt", confianza=0.5):
    model = YOLO(modelo_path)
    cap = cv2.VideoCapture(ruta_video)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duracion_total = total_frames / fps

    frames_detectados = defaultdict(int)
    frame_actual = 0

    print(f"\n🎬 Analizando: {ruta_video}")
    print(f"📊 Total frames: {total_frames} | FPS: {fps:.1f} | Duración: {duracion_total:.1f}s\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        resultados = model(frame, conf=confianza, verbose=False)
        clases_en_frame = set()

        for r in resultados:
            for box in r.boxes:
                clase_id = int(box.cls[0])
                clase_nombre = CLASES[clase_id]
                confianza_det = float(box.conf[0])
                clases_en_frame.add(clase_nombre)

                label = f"{clase_nombre} {confianza_det:.0%}"
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for clase in clases_en_frame:
            frames_detectados[clase] += 1

        frame_actual += 1
        if frame_actual % 100 == 0:
            print(f"  Procesando... {frame_actual}/{total_frames} frames", end="\r")

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

    guardar_detecciones(ruta_video.split("/")[-1], informe, duracion_total)

    return informe, duracion_total

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Ruta al vídeo")
    parser.add_argument("--modelo", default="runs/detect/runs/videogame-logos/weights/best.pt")
    parser.add_argument("--confianza", type=float, default=0.5)
    args = parser.parse_args()

    analizar_video(args.video, args.modelo, args.confianza)
