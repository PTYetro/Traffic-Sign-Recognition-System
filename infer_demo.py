import argparse
import json
import time
from pathlib import Path
from typing import List

import cv2
from ultralytics import YOLO


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".mpeg", ".mpg"}


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_SUFFIXES


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_SUFFIXES


def collect_images(source: Path) -> List[Path]:
    if source.is_file() and is_image_file(source):
        return [source]

    if source.is_dir():
        files = [p for p in source.iterdir() if p.is_file() and is_image_file(p)]
        return sorted(files)

    return []


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def make_output_dir(base_dir: Path) -> Path:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = base_dir / f"infer_demo_{timestamp}"
    ensure_dir(out_dir)
    return out_dir


def save_result_json(result, json_path: Path) -> None:
    detections = []
    names = result.names

    if result.boxes is not None and len(result.boxes) > 0:
        xyxy_list = result.boxes.xyxy.cpu().tolist()
        conf_list = result.boxes.conf.cpu().tolist()
        cls_list = result.boxes.cls.cpu().tolist()

        for xyxy, conf, cls_id in zip(xyxy_list, conf_list, cls_list):
            cls_id = int(cls_id)
            detections.append(
                {
                    "class_id": cls_id,
                    "class_name": names.get(cls_id, str(cls_id)),
                    "confidence": round(float(conf), 6),
                    "xyxy": [round(float(v), 2) for v in xyxy],
                }
            )

    payload = {
        "image_path": str(result.path) if result.path is not None else "",
        "num_detections": len(detections),
        "detections": detections,
    }

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_on_images(model: YOLO, args, output_dir: Path) -> None:
    source_path = Path(args.source)
    image_paths = collect_images(source_path)

    if not image_paths:
        raise FileNotFoundError(f"未找到可处理的图片: {source_path}")

    image_out_dir = output_dir / "images"
    json_out_dir = output_dir / "json"
    ensure_dir(image_out_dir)
    if args.save_json:
        ensure_dir(json_out_dir)

    print(f"共发现 {len(image_paths)} 张图片，开始推理...")
    print(f"输出目录: {output_dir}")

    for idx, image_path in enumerate(image_paths, start=1):
        results = model.predict(
            source=str(image_path),
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            device=args.device,
            verbose=False,
        )

        result = results[0]
        plotted = result.plot(
            conf=not args.hide_conf,
            labels=not args.hide_labels,
            line_width=args.line_width,
        )

        save_img_path = image_out_dir / image_path.name
        cv2.imwrite(str(save_img_path), plotted)

        if args.save_json:
            save_json_path = json_out_dir / f"{image_path.stem}.json"
            save_result_json(result, save_json_path)

        num_det = 0 if result.boxes is None else len(result.boxes)
        print(f"[{idx}/{len(image_paths)}] {image_path.name} -> 检测到 {num_det} 个目标")

        if args.show:
            cv2.imshow("infer_demo", plotted)
            key = cv2.waitKey(0) & 0xFF
            if key == ord("q"):
                break

    if args.show:
        cv2.destroyAllWindows()

    print("图片推理完成。")


def run_on_video_or_camera(model: YOLO, args, output_dir: Path) -> None:
    source = args.source
    is_camera = source.isdigit()

    cap = cv2.VideoCapture(int(source) if is_camera else source)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频/摄像头: {source}")

    video_out_dir = output_dir / "video"
    ensure_dir(video_out_dir)

    writer = None
    save_video_path = None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 1 or fps != fps:
        fps = 25.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)

    if args.save_video:
        video_name = "camera_result.mp4" if is_camera else f"{Path(source).stem}_result.mp4"
        save_video_path = video_out_dir / video_name
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(save_video_path), fourcc, fps, (width, height))

    print("开始视频/摄像头推理，按 q 退出。")
    print(f"输出目录: {output_dir}")

    frame_count = 0
    t0 = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(
            source=frame,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            device=args.device,
            verbose=False,
        )

        result = results[0]
        plotted = result.plot(
            conf=not args.hide_conf,
            labels=not args.hide_labels,
            line_width=args.line_width,
        )

        frame_count += 1
        elapsed = max(time.time() - t0, 1e-6)
        fps_text = frame_count / elapsed
        cv2.putText(
            plotted,
            f"FPS: {fps_text:.2f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
        )

        if args.show:
            cv2.imshow("infer_demo", plotted)

        if writer is not None:
            writer.write(plotted)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    if writer is not None:
        writer.release()
    if args.show:
        cv2.destroyAllWindows()

    if save_video_path is not None:
        print(f"视频已保存到: {save_video_path}")

    print("视频/摄像头推理完成。")


def build_parser():
    parser = argparse.ArgumentParser(description="YOLOv8 交通标志识别推理脚本")

    parser.add_argument(
        "--model",
        type=str,
        default=r"D:\traffic_sign_project\runs\tt100k_yolov8s_stage2_1280\weights\best.pt",
        help="模型权重路径",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=r"D:\traffic_sign_project\demo_images",
        help="输入源：图片、图片文件夹、视频文件，或摄像头编号如 0",
    )
    parser.add_argument("--imgsz", type=int, default=1280, help="推理分辨率")
    parser.add_argument("--conf", type=float, default=0.15, help="置信度阈值")
    parser.add_argument("--iou", type=float, default=0.50, help="NMS IOU 阈值")
    parser.add_argument("--device", type=str, default="0", help="设备，如 0 或 cpu")
    parser.add_argument(
        "--output",
        type=str,
        default=r"D:\traffic_sign_project\runs",
        help="输出根目录",
    )
    parser.add_argument("--line-width", type=int, default=2, help="框线宽")
    parser.add_argument("--hide-labels", action="store_true", help="隐藏类别标签")
    parser.add_argument("--hide-conf", action="store_true", help="隐藏置信度")
    parser.add_argument("--show", action="store_true", help="是否弹窗显示结果")
    parser.add_argument("--save-json", action="store_true", help="是否保存图片检测结果 JSON")
    parser.add_argument("--save-video", action="store_true", help="视频/摄像头模式下是否保存视频")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在: {model_path}")

    output_dir = make_output_dir(Path(args.output))
    model = YOLO(str(model_path))

    source_str = args.source.strip()
    source_path = Path(source_str)

    if source_str.isdigit():
        run_on_video_or_camera(model, args, output_dir)
        return

    if source_path.is_file() and is_video_file(source_path):
        run_on_video_or_camera(model, args, output_dir)
        return

    run_on_images(model, args, output_dir)


if __name__ == "__main__":
    main()