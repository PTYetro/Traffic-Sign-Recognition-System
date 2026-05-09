from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO(r"D:\traffic_sign_project\runs\tt100k_yolov8s_baseline\weights\best.pt")

    model.predict(
        source=r"D:\traffic_sign_project\single_test",
        imgsz=1280,      # 只改这一项
        conf=0.05,
        save=True,
        save_conf=True,
        project=r"D:\traffic_sign_project\runs",
        name="single_predict_1280",
        device=0
    )