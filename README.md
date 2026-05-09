# 使用ctrl+shift+v进行预览
# 交通标志识别系统

基于 **YOLOv8 + FastAPI + Vue 3** 的交通标志识别系统，当前已实现：

* 图片推理
* 实时推理（摄像头）
* Python 后端推理服务
* Vue 前端交互页面
* 基于 TT100K 数据集训练的交通标志检测模型

---

## 1. 项目结构

```text
D:\traffic_sign_project
├─ .venv                         # Python 虚拟环境
├─ backend                       # Python 后端
│  └─ app.py
├─ backend_runtime               # 后端运行时目录（上传文件、推理结果）
├─ frontend                      # Vue 前端项目
├─ runs                          # 模型训练与推理输出目录
│  ├─ tt100k_yolov8s_baseline
│  └─ tt100k_yolov8s_stage2_1280
├─ infer_demo.py                 # 本地推理脚本
├─ train.py                      # 第一轮训练脚本
├─ train_stage2.py               # 第二轮强化训练脚本
└─ ...
```

当前正式使用的模型权重路径：

```text
D:\traffic_sign_project\runs\tt100k_yolov8s_stage2_1280\weights\best.pt
```

---

## 2. 运行环境

### Python 环境

项目使用 Python 虚拟环境：

```text
D:\traffic_sign_project\.venv
```

### 前端环境

需要安装：

* Node.js
* npm

当前开发环境示例：

* Node.js：`v22.17.0`
* npm：`10.9.2`

### GPU 环境

项目默认使用 CUDA 版 PyTorch 进行 GPU 推理与训练。

---

## 3. 项目启动方式

每次重新启动项目时，建议按照以下顺序进行。

### 3.1 启动后端

打开一个新的 **PowerShell** 窗口，执行：

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

启动成功后，终端应显示类似：

```text
Uvicorn running on http://127.0.0.1:8001
```

### 3.2 启动前端

再打开一个新的 **PowerShell** 窗口，执行：

```powershell
cd D:\traffic_sign_project\frontend
npm run dev
```

启动成功后，终端会显示前端地址，通常为：

```text
http://127.0.0.1:5173/
```

或：

```text
http://localhost:5173/
```

然后在浏览器中打开该地址即可。

---

## 4. 运行前的健康检查

### 检查后端根路由

浏览器打开：

```text
http://127.0.0.1:8001/
```

正常返回示例：

```json
{"ok":true,"message":"Traffic Sign Detection API is running","health":"/health","docs":"/docs"}
```

### 检查后端健康状态

浏览器打开：

```text
http://127.0.0.1:8001/health
```

正常返回示例：

```json
{"ok":true,"model_path":"D:\\traffic_sign_project\\runs\\tt100k_yolov8s_stage2_1280\\weights\\best.pt","message":"backend is running"}
```

### 检查接口文档

浏览器打开：

```text
http://127.0.0.1:8001/docs
```

如果能正常打开，说明后端服务可用。

---

## 5. 功能使用说明

### 5.1 图片推理

1. 打开前端页面。
2. 进入 **图片推理** 模式。
3. 点击“选择图片”。
4. 选择本地测试图片。
5. 设置推理参数：

   * `imgsz`：推荐 `1280`
   * `conf`：推荐 `0.15`
   * `iou`：推荐 `0.50`
6. 点击“开始推理”。
7. 页面会显示：

   * 原图
   * 推理结果图
   * 检测结果表格

### 5.2 实时推理（摄像头）

1. 切换到 **实时推理** 模式。
2. 点击“启动摄像头并开始推理”。
3. 浏览器弹出摄像头权限请求时点击允许。
4. 页面左侧显示原始画面。
5. 页面右侧显示实时推理结果图。
6. 下方表格显示当前帧检测结果。

当前实时推理默认建议帧间隔：

```text
80 ms
```

如需进一步测试，可尝试：

* `60 ms`
* `50 ms`

不建议无节制继续调低。

---

## 6. 本地脚本推理

如果不想启动前后端，也可以直接使用本地推理脚本。

### 6.1 图片文件夹推理

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\infer_demo.py --source D:\traffic_sign_project\demo_images --save-json
```

### 6.2 单张图片推理

```powershell
python .\infer_demo.py --source D:\traffic_sign_project\single_test\324.jpg --save-json --show
```

### 6.3 摄像头推理

```powershell
python .\infer_demo.py --source 0 --imgsz 640 --conf 0.2 --show
```

### 6.4 当前推荐参数

* 高精度模式：`--imgsz 1280 --conf 0.15`
* 快速模式：`--imgsz 640 --conf 0.25`

---

## 7. 模型训练

### 7.1 第一轮基线训练

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\train.py
```

### 7.2 第二轮小目标强化训练

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
python .\train_stage2.py
```

---

## 8. 常见问题

### 8.1 PowerShell 中 `cd /d` 报错

在 PowerShell 中不要写：

```powershell
cd /d D:\traffic_sign_project
```

应写为：

```powershell
cd D:\traffic_sign_project
```

### 8.2 8000 端口被占用

如果后端启动时报：

```text
[Errno 10048] ... 8000 ... 只允许使用一次
```

说明 8000 端口已被占用。当前项目统一使用 **8001** 端口：

```powershell
uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

### 8.3 前端提示后端没有启动

先检查浏览器能否打开：

```text
http://127.0.0.1:8001/health
```

再检查前端代码中的后端地址是否为：

```javascript
const API_BASE = 'http://127.0.0.1:8001'
```

### 8.4 模型显示的是 `pl30`、`w55` 等编号

这是 TT100K 数据集原始类别编码。后续可通过标签映射表，将其转换为中文名称，例如：

* `pl30` → `限速30`
* `pl40` → `限速40`
* `pn` → `禁止停车`

### 8.5 VSCode 终端太多、容易混乱

建议平时至少保留两个窗口：

#### 窗口 1：后端

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

#### 窗口 2：前端

```powershell
cd D:\traffic_sign_project\frontend
npm run dev
```

---

## 9. 日常推荐使用流程

### 场景 1：演示系统

1. 启动后端
2. 启动前端
3. 打开浏览器访问前端地址
4. 使用图片推理或实时推理

### 场景 2：只测试模型

1. 激活虚拟环境
2. 直接运行 `infer_demo.py`
3. 查看结果图和 JSON

### 场景 3：继续训练模型

1. 激活虚拟环境
2. 运行 `train.py` 或 `train_stage2.py`
3. 查看 `runs` 目录中的训练结果

---

## 10. 最常用命令速查

### 激活虚拟环境

```powershell
cd D:\traffic_sign_project
.venv\Scripts\activate
```

### 启动后端

```powershell
uvicorn backend.app:app --host 127.0.0.1 --port 8001
```

### 启动前端

```powershell
cd D:\traffic_sign_project\frontend
npm run dev
```

### 本地脚本图片推理

```powershell
python .\infer_demo.py --source D:\traffic_sign_project\demo_images --save-json
```

---

## 11. 说明

当前项目已经完成：

* 模型训练
* 图片推理
* 实时推理
* Python 后端服务
* Vue 前端界面

因此日常启动时，记住一句话即可：

**先启动后端，再启动前端。**
"# ��ͨ��־ʶ��ϵͳ"  
