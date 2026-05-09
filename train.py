from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolov8s.pt")   # 正式第一轮用 s，不再用 n

    model.train(
        data="TT100K.yaml",

        # 训练轮数
        epochs=100,

        # 输入尺寸
        imgsz=640,

        # 2080Ti 11GB 先保守一点，避免第一次正式训练就爆显存
        batch=8,

        # 使用第一张显卡
        device=0,

        # Windows 下先不要开太大
        workers=4,

        # 输出目录
        project=r"D:\traffic_sign_project\runs",
        name="tt100k_yolov8s_baseline",
        pretrained=True,

        # 早停，防止后期长时间无提升
        patience=30,

        # ========= 交通标志任务的重要设置 =========
        # 交通标志有方向性，关掉左右翻转和上下翻转
        fliplr=0.0,
        flipud=0.0,

        # 轻量几何增强，别太猛
        degrees=3.0,
        translate=0.08,
        scale=0.30,
        shear=0.0,
        perspective=0.0,

        # 轻量颜色增强
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.3,

        # 保留 mosaic，但最后若干轮关闭，利于收敛
        close_mosaic=10,

        # 首轮正式训练先不用 cache，避免占盘和额外变量
        cache=False,

        # 保持确定性，方便复现实验
        deterministic=True,
        seed=0
    )