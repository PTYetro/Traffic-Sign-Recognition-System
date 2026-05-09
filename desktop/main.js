const { app, BrowserWindow, ipcMain, Menu, Tray } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn } = require('child_process')

const BACKEND_URL = 'http://127.0.0.1:8001'
const isDev = !app.isPackaged

let mainWindow = null
let tray = null
let isAppQuitting = false
let backendProcess = null

function getIconPath() {
  return path.join(__dirname, 'assets', 'icon.ico')
}

function getProjectRoot() {
  return path.resolve(__dirname, '..')
}

function getPythonPath() {
  return path.join(getProjectRoot(), '.venv', 'Scripts', 'python.exe')
}

function getDevRendererURL() {
  return 'http://localhost:5173'
}

function getProdRendererPath() {
  return path.join(__dirname, 'renderer-dist', 'index.html')
}

function hasProdRenderer() {
    return fs.existsSync(getProdRendererPath())
  }
  
  function loadRenderer(window) {
    if (app.isPackaged) {
      window.loadFile(getProdRendererPath())
      return
    }
  
    if (hasProdRenderer()) {
      window.loadFile(getProdRendererPath())
    } else {
      window.loadURL(getDevRendererURL())
    }
  }

function getProdBackendExePath() {
  return path.join(process.resourcesPath, 'backend', 'backend_service.exe')
}

function sendWindowState() {
  if (!mainWindow || mainWindow.isDestroyed()) return
  mainWindow.webContents.send('window:state', {
    isMaximized: mainWindow.isMaximized(),
  })
}

function restoreMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) return

  if (mainWindow.isMinimized()) {
    mainWindow.restore()
  }

  mainWindow.show()
  mainWindow.focus()
  sendWindowState()
}

function ensureTray() {
  if (tray) return

  tray = new Tray(getIconPath())
  tray.setToolTip('交通标志识别系统')

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => restoreMainWindow(),
    },
    { type: 'separator' },
    {
      label: '退出应用',
      click: () => {
        isAppQuitting = true
        app.quit()
      },
    },
  ])

  tray.setContextMenu(contextMenu)
  tray.on('click', () => restoreMainWindow())
  tray.on('double-click', () => restoreMainWindow())
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 980,
    minWidth: 1280,
    minHeight: 800,
    backgroundColor: '#0b1020',
    autoHideMenuBar: true,
    title: '交通标志识别系统',
    icon: getIconPath(),
    frame: false,
    titleBarStyle: 'hidden',
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  })

  loadRenderer(mainWindow)

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    sendWindowState()
  })

  mainWindow.on('maximize', sendWindowState)
  mainWindow.on('unmaximize', sendWindowState)
  mainWindow.on('restore', sendWindowState)
  mainWindow.on('enter-full-screen', sendWindowState)
  mainWindow.on('leave-full-screen', sendWindowState)

  mainWindow.on('close', () => {
    isAppQuitting = true
  })

  mainWindow.on('closed', () => {
    mainWindow = null
    if (!isAppQuitting) {
      app.quit()
    }
  })
}

function startBackend() {
  if (backendProcess) return

  if (isDev) {
    const pythonPath = getPythonPath()
    if (!fs.existsSync(pythonPath)) {
      console.error('未找到虚拟环境 Python：', pythonPath)
      return
    }

    backendProcess = spawn(
      pythonPath,
      ['backend_service.py'],
      {
        cwd: getProjectRoot(),
        windowsHide: true,
        stdio: 'ignore',
      }
    )
  } else {
    const backendExe = getProdBackendExePath()
    if (!fs.existsSync(backendExe)) {
      console.error('未找到后端可执行文件：', backendExe)
      return
    }

    backendProcess = spawn(
      backendExe,
      [],
      {
        cwd: path.dirname(backendExe),
        windowsHide: true,
        stdio: 'ignore',
      }
    )
  }

  backendProcess.on('exit', (code, signal) => {
    console.log(`backend exited, code=${code}, signal=${signal}`)
    backendProcess = null
  })

  backendProcess.on('error', (err) => {
    console.error('backend start error:', err)
    backendProcess = null
  })
}

function stopBackend() {
  if (!backendProcess || !backendProcess.pid) {
    backendProcess = null
    return
  }

  const pid = backendProcess.pid

  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(pid), '/t', '/f'], {
        windowsHide: true,
        stdio: 'ignore',
      })
    } else {
      backendProcess.kill('SIGTERM')
    }
  } catch (err) {
    console.error('stop backend error:', err)
  }

  backendProcess = null
}

app.whenReady().then(() => {
  app.setName('交通标志识别系统')

  if (app.setAppUserModelId) {
    app.setAppUserModelId('com.traffic.sign.desktop')
  }

  startBackend()
  ensureTray()
  createWindow()

  app.on('activate', () => {
    if (mainWindow === null) {
      createWindow()
    } else {
      restoreMainWindow()
    }
  })
})

ipcMain.handle('window:close', () => {
  isAppQuitting = true
  app.quit()
  return true
})

ipcMain.handle('window:minimizeToTray', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    ensureTray()
    mainWindow.hide()
  }
  return true
})

ipcMain.handle('window:minimize', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.minimize()
  }
  return true
})

ipcMain.handle('window:toggleMaximize', () => {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return { isMaximized: false }
  }

  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize()
  } else {
    mainWindow.maximize()
  }

  const state = { isMaximized: mainWindow.isMaximized() }
  sendWindowState()
  return state
})

ipcMain.handle('window:getState', () => {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return { isMaximized: false }
  }

  return {
    isMaximized: mainWindow.isMaximized(),
  }
})

app.on('before-quit', () => {
  isAppQuitting = true
  stopBackend()

  if (tray) {
    tray.destroy()
    tray = null
  }
})

app.on('will-quit', () => {
  stopBackend()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin' && isAppQuitting) {
    app.quit()
  }
})