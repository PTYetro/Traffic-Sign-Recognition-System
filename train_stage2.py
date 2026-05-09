from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO(r"D:\traffic_sign_project\runs\tt100k_yolov8s_baseline\weights\best.pt")

    model.train(
        data="TT100K.yaml",

        # 第二轮强化训练，轮数不用太长
        epochs=40,

        # 提高输入分辨率，专门强化小目标
        imgsz=1280,

        # 2080Ti 11GB 这里必须保守
        batch=2,

        device=0,
        workers=2,

        project=r"D:\traffic_sign_project\runs",
        name="tt100k_yolov8s_stage2_1280",
        pretrained=True,

        patience=15,

        # 交通标志方向敏感，继续关闭翻转
        fliplr=0.0,
        flipud=0.0,

        # 几何增强保持克制
        degrees=2.0,
        translate=0.05,
        scale=0.20,
        shear=0.0,
        perspective=0.0,

        # 颜色增强稍弱一点
        hsv_h=0.015,
        hsv_s=0.4,
        hsv_v=0.25,

        close_mosaic=5,
        cache=False,
        deterministic=True,
        seed=0
    )