from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolov8n.pt")

    model.train(
        data="TT100K.yaml",
        epochs=1,
        imgsz=640,
        batch=2,
        device=0,
        workers=0,
        project=r"D:\traffic_sign_project\runs",
        name="tt100k_probe",
        pretrained=True
    )