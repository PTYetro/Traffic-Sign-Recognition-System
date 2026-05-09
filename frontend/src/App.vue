<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import axios from 'axios'

import WindowChrome from './components/desktop/WindowChrome.vue'
import BootOverlay from './components/desktop/BootOverlay.vue'
import { useDesktopWindow } from './composables/useDesktopWindow'
import { useBackendBoot } from './composables/useBackendBoot'

const API_BASE = 'http://127.0.0.1:8001'

const mode = ref('image') // image | realtime

const {
  isDesktopShell,
  shellMenuOpen,
  isMaximized,
  openShellMenu,
  closeShellMenu,
  handleCloseApp,
  handleMinimizeToTray,
  handleMinimizeWindow,
  handleToggleMaximize,
} = useDesktopWindow()

const {
  booting,
  bootError,
  retryBoot,
} = useBackendBoot(API_BASE)

// ===== 图片推理相关 =====
const selectedFile = ref(null)
const originalPreview = ref('')
const resultImageUrl = ref('')
const detections = ref([])
const numDetections = ref(0)
const loading = ref(false)
const errorMessage = ref('')

const imgsz = ref(1280)
const conf = ref(0.15)
const iou = ref(0.5)

const selectedFileName = computed(() => {
  return selectedFile.value ? selectedFile.value.name : '未选择图片'
})

// ===== 实时推理相关 =====
const videoRef = ref(null)
const canvasRef = ref(null)
const cameraRunning = ref(false)
const realtimeLoading = ref(false)
const realtimeError = ref('')
const realtimeResultImageUrl = ref('')
const realtimeDetections = ref([])
const realtimeNumDetections = ref(0)
const realtimeIntervalMs = ref(80)

let mediaStream = null
let realtimeTimer = null
let frameRequestPending = false

function resetImageResult() {
  resultImageUrl.value = ''
  detections.value = []
  numDetections.value = 0
  errorMessage.value = ''
}

function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (!file) return

  selectedFile.value = file
  originalPreview.value = URL.createObjectURL(file)
  resetImageResult()
}

async function runInference() {
  if (booting.value || bootError.value) {
    errorMessage.value = '服务尚未就绪，请稍候'
    return
  }

  if (!selectedFile.value) {
    errorMessage.value = '请先选择一张图片'
    return
  }

  loading.value = true
  errorMessage.value = ''
  resultImageUrl.value = ''
  detections.value = []
  numDetections.value = 0

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('imgsz', String(imgsz.value))
    formData.append('conf', String(conf.value))
    formData.append('iou', String(iou.value))

    const response = await axios.post(`${API_BASE}/predict/image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    const data = response.data
    numDetections.value = data.num_detections || 0
    detections.value = data.detections || []
    resultImageUrl.value = `${API_BASE}${data.result_image_url}`
  } catch (error) {
    console.error(error)
    errorMessage.value = '图片推理失败，请确认 Python 后端正在 8001 端口运行'
  } finally {
    loading.value = false
  }
}

function switchMode(newMode) {
  mode.value = newMode
  if (newMode !== 'realtime') {
    stopRealtime()
  }
}

async function startCamera() {
  realtimeError.value = ''

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: false,
    })

    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      await videoRef.value.play()
    }

    cameraRunning.value = true
    startRealtimeLoop()
  } catch (error) {
    console.error(error)
    realtimeError.value = '无法打开摄像头，请检查浏览器权限或设备占用情况'
  }
}

function stopCameraOnly() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }

  if (videoRef.value) {
    videoRef.value.srcObject = null
  }

  cameraRunning.value = false
}

function startRealtimeLoop() {
  stopRealtimeLoop()

  realtimeTimer = setInterval(async () => {
    if (!cameraRunning.value) return
    if (frameRequestPending) return
    await sendCurrentFrame()
  }, realtimeIntervalMs.value)
}

function stopRealtimeLoop() {
  if (realtimeTimer) {
    clearInterval(realtimeTimer)
    realtimeTimer = null
  }
}

function stopRealtime() {
  stopRealtimeLoop()
  stopCameraOnly()
  realtimeLoading.value = false
  frameRequestPending = false
}

async function startRealtime() {
  if (booting.value || bootError.value) {
    realtimeError.value = '服务尚未就绪，请稍候'
    return
  }

  realtimeResultImageUrl.value = ''
  realtimeDetections.value = []
  realtimeNumDetections.value = 0
  realtimeError.value = ''

  if (!cameraRunning.value) {
    await startCamera()
  } else {
    startRealtimeLoop()
  }
}

function captureFrameBlob() {
  return new Promise((resolve) => {
    const video = videoRef.value
    const canvas = canvasRef.value

    if (!video || !canvas) {
      resolve(null)
      return
    }

    const width = video.videoWidth
    const height = video.videoHeight

    if (!width || !height) {
      resolve(null)
      return
    }

    canvas.width = width
    canvas.height = height

    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, width, height)

    canvas.toBlob(
      (blob) => {
        resolve(blob)
      },
      'image/jpeg',
      0.92,
    )
  })
}

async function sendCurrentFrame() {
  const blob = await captureFrameBlob()
  if (!blob) return

  frameRequestPending = true
  realtimeLoading.value = true
  realtimeError.value = ''

  try {
    const formData = new FormData()
    formData.append('file', blob, 'frame.jpg')
    formData.append('imgsz', '640')
    formData.append('conf', '0.20')
    formData.append('iou', '0.50')

    const response = await axios.post(`${API_BASE}/predict/frame`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    const data = response.data
    realtimeNumDetections.value = data.num_detections || 0
    realtimeDetections.value = data.detections || []
    realtimeResultImageUrl.value = `${API_BASE}${data.result_image_url}?t=${Date.now()}`
  } catch (error) {
    console.error(error)
    realtimeError.value = '实时推理失败，请检查后端或摄像头状态'
  } finally {
    frameRequestPending = false
    realtimeLoading.value = false
  }
}

onBeforeUnmount(() => {
  stopRealtime()
})
</script>

<template>
  <div class="app-shell">
    <WindowChrome
      v-if="isDesktopShell"
      :visible="shellMenuOpen"
      :is-maximized="isMaximized"
      @mouseenter="openShellMenu"
      @mouseleave="closeShellMenu"
      @close-app="handleCloseApp"
      @minimize-to-tray="handleMinimizeToTray"
      @minimize-window="handleMinimizeWindow"
      @toggle-maximize="handleToggleMaximize"
    />

    <BootOverlay
      :booting="booting"
      :boot-error="bootError"
      :is-desktop-shell="isDesktopShell"
      @retry="retryBoot"
      @close-app="handleCloseApp"
    />

    <div 
      class="page" 
      :class="{
         'page-with-chrome': isDesktopShell,
         'page-image': mode === 'image',
         'page-realtime': mode === 'realtime',
         }"
    >
      <div class="hero-card">
        <div class="hero-left">
          <h1>交通标志识别系统</h1>
          <p class="subtitle">
            基于 YOLOv8 的真实道路场景交通标志检测与识别
          </p>

          <div class="mode-switch">
            <button
              class="mode-tab"
              :class="{ active: mode === 'image' }"
              @click="switchMode('image')"
            >
              图片推理
            </button>
            <button
              class="mode-tab"
              :class="{ active: mode === 'realtime' }"
              @click="switchMode('realtime')"
            >
              实时推理
            </button>
          </div>
        </div>

        <!-- <div class="hero-right">
          <div class="mode-card">
            <div class="mode-title">当前模式</div>
            <div class="mode-value">
              {{ mode === 'image' ? '图片推理' : '实时推理' }}
            </div>
          </div>
        </div> -->
      </div>

      <!-- 图片推理模式 -->
      <template v-if="mode === 'image'">
        <div class="main-grid">
          <section class="panel left-panel">
            <h2>上传与参数设置</h2>

            <div class="upload-box">
              <label for="fileInput" class="upload-button">选择图片</label>
              <input id="fileInput" type="file" accept="image/*" @change="handleFileChange" />
              <div class="file-name">{{ selectedFileName }}</div>
            </div>

            <div class="form-grid">
              <div class="form-item">
                <label>推理分辨率</label>
                <input v-model.number="imgsz" type="number" min="320" step="32" />
              </div>

              <div class="form-item">
                <label>置信度阈值</label>
                <input v-model.number="conf" type="number" min="0.01" max="1" step="0.01" />
              </div>

              <div class="form-item">
                <label>IOU 阈值</label>
                <input v-model.number="iou" type="number" min="0.1" max="1" step="0.01" />
              </div>
            </div>

            <button
              class="infer-button"
              :disabled="loading || booting || !!bootError"
              @click="runInference"
            >
              {{ loading ? '正在推理中...' : '开始推理' }}
            </button>

            <p v-if="errorMessage" class="error-text">
              {{ errorMessage }}
            </p>

            <div class="stats-box">
              <div class="stats-title">推理结果摘要</div>
              <div class="stats-item">检测目标数量：{{ numDetections }}</div>
              <div class="stats-item">后端地址：{{ API_BASE }}</div>
            </div>
          </section>

          <section class="panel preview-panel">
            <h2>图像预览</h2>

            <div class="preview-grid">
              <div class="preview-card">
                <div class="preview-title">原图</div>
                <div class="image-frame">
                  <img v-if="originalPreview" :src="originalPreview" alt="原图预览" />
                  <div v-else class="placeholder">请选择图片</div>
                </div>
              </div>

              <div class="preview-card">
                <div class="preview-title">推理结果</div>
                <div class="image-frame">
                  <img v-if="resultImageUrl" :src="resultImageUrl" alt="推理结果图" />
                  <div v-else class="placeholder">
                    {{ loading ? '模型正在推理...' : '结果图将在这里显示' }}
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>

        <section class="panel result-panel">
          <div class="result-header">
            <h2>检测结果列表</h2>
            <span class="result-count">共 {{ detections.length }} 条</span>
          </div>

          <div v-if="detections.length > 0" class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>类别名</th>
                  <th>类别 ID</th>
                  <th>置信度</th>
                  <th>框坐标（xyxy）</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in detections" :key="`${item.class_id}-${index}`">
                  <td>{{ index + 1 }}</td>
                  <td>{{ item.display_name || item.class_name }}</td>
                  <td>{{ item.class_id }}</td>
                  <td>{{ item.confidence }}</td>
                  <td>{{ item.xyxy.join(', ') }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="empty-state">
            还没有检测结果，请先选择图片并点击“开始推理”
          </div>
        </section>
      </template>

      <!-- 实时推理模式 -->
      <template v-else>
        <div class="main-grid realtime-grid">
          <section class="panel left-panel">
            <h2>实时推理控制台</h2>

            <div class="form-grid">
              <div class="form-item">
                <label>帧间隔（毫秒）默认80，可根据显卡性能自行调整，数值越小推理越快、显卡压力越大</label>
                <input v-model.number="realtimeIntervalMs" type="number" min="20" step="10" />
              </div>
            </div>

            <div class="button-group">
              <button
                class="infer-button"
                :disabled="booting || !!bootError"
                @click="startRealtime"
              >
                {{ cameraRunning ? '继续实时推理' : '启动摄像头并开始推理' }}
              </button>

              <button class="stop-button" @click="stopRealtime">
                停止实时推理
              </button>
            </div>

            <p v-if="realtimeError" class="error-text">
              {{ realtimeError }}
            </p>

            <div class="stats-box">
              <div class="stats-title">实时状态</div>
              <div class="stats-item">摄像头状态：{{ cameraRunning ? '已启动' : '未启动' }}</div>
              <div class="stats-item">后端状态：{{ realtimeLoading ? '正在处理当前帧' : '空闲' }}</div>
              <div class="stats-item">检测目标数量：{{ realtimeNumDetections }}</div>
            </div>
          </section>

          <section class="panel preview-panel">
            <h2>实时画面</h2>

            <div class="preview-grid">
              <div class="preview-card">
                <div class="preview-title">摄像头原始画面</div>
                <div class="image-frame live-frame">
                  <video ref="videoRef" autoplay muted playsinline></video>
                  <div v-if="!cameraRunning" class="placeholder">
                    点击左侧按钮启动摄像头
                  </div>
                </div>
              </div>

              <div class="preview-card">
                <div class="preview-title">实时推理结果</div>
                <div class="image-frame live-frame">
                  <img
                    v-if="realtimeResultImageUrl"
                    :src="realtimeResultImageUrl"
                    alt="实时推理结果"
                  />
                  <div v-else class="placeholder">
                    {{ realtimeLoading ? '正在推理当前帧...' : '结果画面将在这里显示' }}
                  </div>
                </div>
              </div>
            </div>

            <canvas ref="canvasRef" class="hidden-canvas"></canvas>
          </section>
        </div>

        <section class="panel result-panel">
          <div class="result-header">
            <h2>实时检测结果列表</h2>
            <span class="result-count">共 {{ realtimeDetections.length }} 条</span>
          </div>

          <div v-if="realtimeDetections.length > 0" class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>类别名</th>
                  <th>类别 ID</th>
                  <th>置信度</th>
                  <th>框坐标（xyxy）</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, index) in realtimeDetections"
                  :key="`${item.class_id}-${index}`"
                >
                  <td>{{ index + 1 }}</td>
                  <td>{{ item.display_name || item.class_name }}</td>
                  <td>{{ item.class_id }}</td>
                  <td>{{ item.confidence }}</td>
                  <td>{{ item.xyxy.join(', ') }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="empty-state">
            还没有实时检测结果，请先启动摄像头
          </div>
        </section>
      </template>
    </div>
  </div>
</template>