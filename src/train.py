from ultralytics import YOLO

model = YOLO("yolov8s.pt")

model.train(
    data="data.yaml",
    epochs=50,
    imgsz=512,
    batch=16,
    name="videogame-logos",
    project="runs",
    patience=10,
)

print("\n✅ Entrenamiento completado!")
print("Modelo guardado en: runs/videogame-logos/weights/best.pt")
