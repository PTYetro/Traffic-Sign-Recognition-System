from pathlib import Path
from typing import List, Dict, Any
import os
import shutil
import sys
import time
import uuid

from backend.label_map_zh import get_display_name

import cv2
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO


# ========= 路径工具 =========
def get_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return get_source_root()


def get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        local_appdata = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        return local_appdata / "TrafficSignDetection"
    return get_source_root()


SOURCE_ROOT = get_source_root()
BUNDLE_ROOT = get_bundle_root()
APP_RUNTIME_ROOT = get_runtime_root()

MODEL_CANDIDATES = [
    BUNDLE_ROOT / "model" / "best.pt",
    SOURCE_ROOT / "runs" / "tt100k_yolov8s_stage2_1280" / "weights" / "best.pt",
]

MODEL_PATH = next((p for p in MODEL_CANDIDATES if p.exists()), None)
if MODEL_PATH is None:
    raise FileNotFoundError(
        "模型文件不存在，已检查路径：\n" + "\n".join(str(p) for p in MODEL_CANDIDATES)
    )

RUNTIME_DIR = APP_RUNTIME_ROOT / "backend_runtime"
UPLOAD_DIR = RUNTIME_DIR / "uploads"
RESULT_DIR = RUNTIME_DIR / "results"

for p in [RUNTIME_DIR, UPLOAD_DIR, RESULT_DIR]:
    p.mkdir(parents=True, exist_ok=True)


# ========= 加载模型 =========
model = YOLO(str(MODEL_PATH))

app = FastAPI(title="Traffic Sign Detection API", version="1.0.0")

# 发布版 Electron 加载 file:// 页面时，请求来源可能是 null
# 所以这里直接放开，桌面单机程序场景下更稳
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件访问，便于前端直接展示结果图
app.mount("/results", StaticFiles(directory=str(RESULT_DIR)), name="results")


def replace_result_names_with_display_names(result):
    """
    把 YOLO 结果里的类别名称替换成中文显示名，
    这样 result.plot() 画框时会尽量显示可读标签。
    """
    if not hasattr(result, "names") or result.names is None:
        return

    result.names = {
        class_id: get_display_name(raw_name)
        for class_id, raw_name in result.names.items()
    }


def result_to_dict(result) -> List[Dict[str, Any]]:
    detections = []
    names = result.names

    if result.boxes is None or len(result.boxes) == 0:
        return detections

    xyxy_list = result.boxes.xyxy.cpu().tolist()
    conf_list = result.boxes.conf.cpu().tolist()
    cls_list = result.boxes.cls.cpu().tolist()

    for xyxy, conf, cls_id in zip(xyxy_list, conf_list, cls_list):
        cls_id = int(cls_id)

        raw_name = names.get(cls_id, str(cls_id))
        display_name = get_display_name(raw_name)

        detections.append(
            {
                "class_id": cls_id,
                "class_name": raw_name,
                "display_name": display_name,
                "confidence": round(float(conf), 6),
                "xyxy": [round(float(v), 2) for v in xyxy],
            }
        )

    return detections


@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Traffic Sign Detection API is running",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "model_path": str(MODEL_PATH),
        "runtime_dir": str(RUNTIME_DIR),
        "message": "backend is running",
    }


@app.post("/predict/image")
async def predict_image(
    file: UploadFile = File(...),
    imgsz: int = Form(1280),
    conf: float = Form(0.15),
    iou: float = Form(0.50),
):
    suffix = Path(file.filename).suffix.lower() or ".jpg"
    file_id = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    upload_path = UPLOAD_DIR / f"{file_id}{suffix}"
    result_img_path = RESULT_DIR / f"{file_id}_result.jpg"

    with upload_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    results = model.predict(
        source=str(upload_path),
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        device="0",
        verbose=False,
    )

    result = results[0]
    detections = result_to_dict(result)

    replace_result_names_with_display_names(result)

    plotted = result.plot(conf=True, labels=True, line_width=2)
    cv2.imwrite(str(result_img_path), plotted)

    return JSONResponse(
        {
            "success": True,
            "file_name": file.filename,
            "num_detections": len(detections),
            "detections": detections,
            "result_image_url": f"/results/{result_img_path.name}",
            "result_image_path": str(result_img_path),
        }
    )


@app.post("/predict/frame")
async def predict_frame(
    file: UploadFile = File(...),
    imgsz: int = Form(640),
    conf: float = Form(0.20),
    iou: float = Form(0.50),
):
    suffix = Path(file.filename).suffix.lower() or ".jpg"
    file_id = f"frame_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    upload_path = UPLOAD_DIR / f"{file_id}{suffix}"
    result_img_path = RESULT_DIR / f"{file_id}_result.jpg"

    with upload_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    results = model.predict(
        source=str(upload_path),
        imgsz=imgsz,
        conf=conf,
        iou=iou,
        device="0",
        verbose=False,
    )

    result = results[0]
    detections = result_to_dict(result)

    replace_result_names_with_display_names(result)

    plotted = result.plot(conf=True, labels=True, line_width=2)
    cv2.imwrite(str(result_img_path), plotted)

    return JSONResponse(
        {
            "success": True,
            "num_detections": len(detections),
            "detections": detections,
            "result_image_url": f"/results/{result_img_path.name}",
        }
    )