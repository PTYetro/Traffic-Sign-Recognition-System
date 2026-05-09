# 交通标志识别系统

基于 **YOLOv8 + FastAPI + Vue 3 + Electron** 的交通标志检测与识别系统。当前版本同时支持浏览器 Web 端、Electron 桌面端、本地脚本推理、模型训练与桌面程序打包。

当前主要能力：

- 图片交通标志检测：上传本地图片，返回检测框、类别、置信度和结果图。
- 实时摄像头检测：浏览器或桌面端调用摄像头，按帧发送到后端推理。
- 中文标签显示：后端将 TT100K 原始类别编码转换为更易读的中文显示名。
- FastAPI 后端接口：提供健康检查、图片推理、实时帧推理和结果图静态访问。
- Vue 3 前端界面：提供图片推理、实时推理、参数设置和结果表格。
- Electron 桌面端：支持无边框窗口、托盘、最小化、窗口控制，并可自动拉起后端服务。
- 一键启动脚本：`启动.bat` 会检查残留进程，并按顺序启动后端、前端和桌面端。

## 项目结构

```text
D:\traffic_sign_project
├─ backend\                         # FastAPI 后端
│  ├─ app.py                         # API 服务、模型加载、推理接口
│  └─ label_map_zh.py                # TT100K 类别中文显示映射
├─ frontend\                         # Vue 3 + Vite 前端
│  ├─ src\App.vue                    # 主界面：图片推理 / 实时推理
│  ├─ src\components\desktop\        # Electron 窗口与启动遮罩组件
│  └─ src\composables\               # 后端启动轮询、桌面窗口控制
├─ desktop\                          # Electron 桌面端
│  ├─ main.js                        # 主进程、托盘、后端进程管理
│  ├─ preload.js                     # 桌面 API 暴露
│  ├─ assets\                        # 图标与 Logo
│  ├─ backend_dist\backend\          # 桌面端发布用后端可执行文件
│  └─ renderer-dist\                 # 前端构建产物，打包时生成
├─ backend_runtime\                  # 后端运行时上传文件与结果图
├─ datasets\cts_yolo\                # YOLO 格式数据集
├─ demo_images\                      # 演示图片
├─ dist\backend_service\             # PyInstaller 后端打包产物
├─ runs\                             # 训练、验证和推理输出
├─ 官网\                             # 项目展示网页
├─ backend_service.py                # 后端服务启动入口
├─ backend_service.spec              # PyInstaller 打包配置
├─ infer_demo.py                     # 本地图片 / 视频 / 摄像头推理脚本
├─ train.py                          # 第一阶段 YOLOv8s 训练脚本
├─ train_stage2.py                   # 第二阶段 1280 分辨率强化训练脚本
├─ 启动.bat                          # 一键启动脚本
└─ 启动方法.txt                      # 手动启动简要说明
```

当前默认正式模型权重：

```text
D:\traffic_sign_project\runs\tt100k_yolov8s_stage2_1280\weights\best.pt
```

后端加载模型时会依次检查：

```text
打包模式：<bundle_root>\model\best.pt
源码模式：D:\traffic_sign_project\runs\tt100k_yolov8s_stage2_1280\weights\best.pt
```

## 环境要求

### Python 后端

项目使用本地虚拟环境：

```powershell
D:\traffic_sign_project\.venv
```

主要依赖包括：

- Python 3.11
- ultralytics / YOLOv8
- torch / torchvision
- fastapi
- uvicorn
- opencv-python
- python-multipart

如果需要手动进入虚拟环境：

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
```

### 前端与桌面端

需要安装 Node.js 和 npm。当前项目使用：

- 前端：Vue 3 + Vite
- 桌面端：Electron + electron-builder

从 `frontend\package.json` 看，Node 版本要求为：

```text
^20.19.0 || >=22.12.0
```

### GPU

当前后端和脚本默认使用 CUDA 设备 `0`：

```python
device="0"
```

如果没有 NVIDIA GPU 或 CUDA 环境，需要把相关命令或代码中的设备改为 `cpu`。

## 推荐启动方式

最简单的方式是双击或运行：

```powershell
cd D:\traffic_sign_project
.\启动.bat
```

脚本会自动：

1. 检查后端 `8001` 端口、前端 `5173` 端口和 Electron 进程是否已有残留。
2. 如检测到残留，会提示是否关闭残留进程并重新启动。
3. 无残留时依次启动后端、前端和 Electron 桌面端。

默认端口：

```text
后端 API：http://127.0.0.1:8001
前端页面：http://127.0.0.1:5173
```

## 手动启动方式

如果不使用一键脚本，可以分别打开三个 PowerShell 窗口。

### 1. 启动后端

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

也可以使用后端入口脚本：

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\backend_service.py
```

### 2. 启动前端

```powershell
cd D:\traffic_sign_project\frontend
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173/
```

### 3. 启动 Electron 桌面端

```powershell
cd D:\traffic_sign_project\desktop
npm start
```

开发模式下，Electron 会尝试自动启动：

```text
D:\traffic_sign_project\.venv\Scripts\python.exe backend_service.py
```

如果 `desktop\renderer-dist\index.html` 存在，桌面端会优先加载该构建产物；否则加载 Vite 开发服务 `http://localhost:5173`。

## 后端接口

### 健康检查

```text
GET http://127.0.0.1:8001/
GET http://127.0.0.1:8001/health
```

`/health` 正常返回示例：

```json
{
  "ok": true,
  "model_path": "D:\\traffic_sign_project\\runs\\tt100k_yolov8s_stage2_1280\\weights\\best.pt",
  "runtime_dir": "D:\\traffic_sign_project\\backend_runtime",
  "message": "backend is running"
}
```

### 接口文档

```text
http://127.0.0.1:8001/docs
```

### 图片推理

```text
POST http://127.0.0.1:8001/predict/image
```

表单参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 必填 | 待检测图片 |
| `imgsz` | int | `1280` | 推理输入分辨率 |
| `conf` | float | `0.15` | 置信度阈值 |
| `iou` | float | `0.50` | NMS IOU 阈值 |

返回内容包含：

- `num_detections`：检测目标数量
- `detections`：检测结果列表
- `display_name`：中文显示名
- `xyxy`：检测框坐标
- `result_image_url`：结果图地址

### 实时帧推理

```text
POST http://127.0.0.1:8001/predict/frame
```

默认参数：

```text
imgsz=640
conf=0.20
iou=0.50
```

前端实时模式会定时从摄像头画面截帧，并调用该接口。

### 结果图访问

```text
http://127.0.0.1:8001/results/<result_file_name>
```

结果图和上传文件默认保存在：

```text
D:\traffic_sign_project\backend_runtime\uploads
D:\traffic_sign_project\backend_runtime\results
```

打包后的后端运行时目录会改为：

```text
%LOCALAPPDATA%\TrafficSignDetection\backend_runtime
```

## 前端功能

### 图片推理

1. 打开前端或桌面端。
2. 选择“图片推理”。
3. 点击“选择图片”。
4. 设置推理参数。
5. 点击“开始推理”。
6. 查看原图、结果图、检测数量和结果表格。

推荐参数：

```text
imgsz=1280
conf=0.15
iou=0.50
```

### 实时推理

1. 切换到“实时推理”。
2. 点击启动摄像头并开始推理。
3. 浏览器弹出权限请求时允许摄像头访问。
4. 左侧显示摄像头原始画面，右侧显示推理结果图。
5. 下方结果表格显示当前帧的检测结果。

默认帧间隔：

```text
80 ms
```

可根据显卡性能尝试 `60 ms` 或 `50 ms`。数值越小，推理频率越高，对显卡压力越大。

## 本地脚本推理

不启动前后端时，可以直接使用 `infer_demo.py`。

### 图片文件夹推理

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source D:\traffic_sign_project\demo_images --save-json
```

### 单张图片推理

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source D:\traffic_sign_project\single_test\324.jpg --save-json --show
```

### 摄像头推理

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source 0 --imgsz 640 --conf 0.2 --show
```

### 视频文件推理

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source D:\path\to\video.mp4 --imgsz 640 --conf 0.2 --show --save-video
```

脚本输出目录默认位于：

```text
D:\traffic_sign_project\runs\infer_demo_时间戳
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `--model` | 指定模型权重路径 |
| `--source` | 图片、图片文件夹、视频文件或摄像头编号 |
| `--imgsz` | 推理分辨率 |
| `--conf` | 置信度阈值 |
| `--iou` | NMS IOU 阈值 |
| `--device` | 推理设备，如 `0` 或 `cpu` |
| `--save-json` | 保存图片检测结果 JSON |
| `--save-video` | 保存视频 / 摄像头推理结果 |
| `--show` | 弹窗显示结果 |

推荐参数：

```text
高精度图片模式：--imgsz 1280 --conf 0.15
实时/快速模式：--imgsz 640 --conf 0.20
CPU 兼容模式：--device cpu --imgsz 640 --conf 0.25
```

## 模型训练

### 第一阶段：YOLOv8s 基线训练

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\train.py
```

训练输出：

```text
D:\traffic_sign_project\runs\tt100k_yolov8s_baseline
```

主要设置：

- 初始权重：`yolov8s.pt`
- 轮数：`100`
- 分辨率：`640`
- batch：`8`
- 关闭左右 / 上下翻转，避免方向敏感标志被错误增强

### 第二阶段：1280 分辨率强化训练

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\train_stage2.py
```

训练输出：

```text
D:\traffic_sign_project\runs\tt100k_yolov8s_stage2_1280
```

主要设置：

- 初始权重：第一阶段 `best.pt`
- 轮数：`40`
- 分辨率：`1280`
- batch：`2`
- 目标：强化小目标交通标志检测能力

## 打包与发布

### 打包后端服务

项目包含 PyInstaller 配置：

```text
D:\traffic_sign_project\backend_service.spec
```

后端已生成的打包产物位于：

```text
D:\traffic_sign_project\dist\backend_service\backend_service.exe
```

桌面端发布目录中也包含后端可执行文件：

```text
D:\traffic_sign_project\desktop\backend_dist\backend\backend_service.exe
```

### 构建前端

```powershell
cd D:\traffic_sign_project\frontend
npm run build
```

### 构建 Electron 渲染资源

```powershell
cd D:\traffic_sign_project\desktop
npm run build:renderer
```

该命令会构建 `frontend\dist`，并复制到：

```text
D:\traffic_sign_project\desktop\renderer-dist
```

### 打包 Electron

仅生成解包目录：

```powershell
cd D:\traffic_sign_project\desktop
npm run pack
```

生成 Windows 安装包：

```powershell
cd D:\traffic_sign_project\desktop
npm run dist
```

输出目录：

```text
D:\traffic_sign_project\desktop\dist
```

## 常见问题

### PowerShell 中 `cd /d` 报错

`cd /d` 是 cmd 写法。PowerShell 中使用：

```powershell
cd D:\traffic_sign_project
```

### 后端端口被占用

当前项目统一使用后端端口 `8001`。如果启动失败，先检查是否已有残留进程，或直接使用：

```powershell
.\启动.bat
```

脚本会提示是否关闭残留后重新启动。

### 前端提示后端未启动

先打开：

```text
http://127.0.0.1:8001/health
```

如果打不开，说明后端没有成功启动。检查：

- `.venv` 是否存在
- 模型权重 `runs\tt100k_yolov8s_stage2_1280\weights\best.pt` 是否存在
- CUDA / PyTorch 环境是否可用
- `8001` 端口是否被占用

### 摄像头无法打开

检查：

- 浏览器或 Electron 是否获得摄像头权限
- 摄像头是否被其他软件占用
- Windows 隐私设置是否允许桌面应用访问摄像头

### 没有 GPU 怎么运行

后端代码目前默认 `device="0"`。无 GPU 时需要改为 CPU：

```python
device="cpu"
```

需要修改的位置主要在：

```text
D:\traffic_sign_project\backend\app.py
D:\traffic_sign_project\infer_demo.py 的命令参数 --device cpu
```

### 结果显示 `pl30`、`w55` 等编码

这是 TT100K 数据集的原始类别编码。当前后端会通过 `backend\label_map_zh.py` 尽量转换为中文显示名，例如限速类、限高类、警告类、禁令类、指示类等。

## 日常使用建议

演示系统时，优先使用：

```powershell
cd D:\traffic_sign_project
.\启动.bat
```

只测试模型时，使用：

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source D:\traffic_sign_project\demo_images --save-json
```

继续训练模型时，使用：

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\train.py
python .\train_stage2.py
```

## 速查命令

```powershell
# 激活 Python 环境
cd D:\traffic_sign_project
.venv\Scripts\activate

# 启动后端
uvicorn backend.app:app --host 127.0.0.1 --port 8001

# 启动前端
cd D:\traffic_sign_project\frontend
npm run dev

# 启动桌面端
cd D:\traffic_sign_project\desktop
npm start

# 一键启动全部模块
cd D:\traffic_sign_project
.\启动.bat

# 本地图片推理
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source D:\traffic_sign_project\demo_images --save-json
```

## 当前版本总结

当前版本已经从早期的“模型训练 + 简单推理脚本”升级为完整应用：

- 后端：FastAPI 推理服务
- 前端：Vue 3 交互界面
- 桌面端：Electron 应用壳与托盘能力
- 模型：两阶段 YOLOv8s 训练后的 1280 分辨率强化权重
- 工具：一键启动、脚本推理、后端打包、桌面端打包

日常运行记住一句话：**优先运行 `启动.bat`，需要调试时再分别启动后端、前端和 Electron。**
