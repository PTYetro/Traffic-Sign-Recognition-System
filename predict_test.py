from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO(r"D:\traffic_sign_project\runs\tt100k_yolov8s_baseline\weights\best.pt")

    model.predict(
        source=r"D:\traffic_sign_project\demo_images",
        imgsz=640,
        conf=0.25,
        save=True,
        project=r"D:\traffic_sign_project\runs",
        name="tt100k_predict_demo",
        device=0
    )