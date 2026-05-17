const { app, BrowserWindow, ipcMain, nativeImage } = require('electron')
const fs = require('fs')
const path = require('path')
const http = require('http')
const { spawn, execSync } = require('child_process')

let mainWindow
let splashWindow
let backendProcess
const isDev = process.env.NODE_ENV === 'development'

function loadAppIcon() {
  const candidates = ['icon-1024.png', 'icon-512.png', 'icon-256.png', 'icon.png', 'icon.ico']
  for (const name of candidates) {
    const p = path.join(__dirname, name)
    if (!fs.existsSync(p)) continue
    const img = nativeImage.createFromPath(p)
    if (!img.isEmpty()) {
      if (img.getSize().width < 256 && fs.existsSync(path.join(__dirname, 'icon-256.png'))) {
        return nativeImage.createFromPath(path.join(__dirname, 'icon-256.png'))
      }
      return img
    }
  }
  return nativeImage.createEmpty()
}

const appIcon = loadAppIcon()

if (isDev) {
  process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = 'true'
}
if (!process.env.PLAYWRIGHT_BROWSERS_PATH && process.platform === 'win32') {
  process.env.PLAYWRIGHT_BROWSERS_PATH = path.join(
    process.env.LOCALAPPDATA || '',
    'ms-playwright'
  )
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function ensureOllama() {
  if (process.env.SKIP_OLLAMA === '1') {
    console.log('[Ollama] skipped (SKIP_OLLAMA=1, local vLLM mode)')
    return
  }
  if (process.platform !== 'win32') return
  const script = path.join(__dirname, '..', 'scripts', 'ensure-ollama.ps1')
  if (!fs.existsSync(script)) return
  try {
    execSync(
      `powershell -NoProfile -ExecutionPolicy Bypass -File "${script}"`,
      { cwd: path.join(__dirname, '..'), windowsHide: true, timeout: 35000 }
    )
    console.log('[Ollama] ready')
  } catch (e) {
    console.warn('[Ollama] not ready — models may not reply:', e.message || e)
  }
}

function pingBackend() {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:8000/health', (res) => {
      resolve(res.statusCode === 200)
      res.resume()
    })
    req.on('error', () => resolve(false))
    req.setTimeout(5000, () => {
      req.destroy()
      resolve(false)
    })
  })
}

async function waitForBackend(maxAttempts = 60) {
  for (let i = 0; i < maxAttempts; i += 1) {
    if (await pingBackend()) return true
    await wait(500)
  }
  return false
}

function resolvePythonExecutable() {
  const fromEnv = (process.env.AI_AGENT_PYTHON || '').trim()
  if (fromEnv) return fromEnv
  try {
    const script = path.join(__dirname, '..', 'scripts', 'resolve-python.cjs')
    const out = execSync(`node "${script}"`, { encoding: 'utf8', windowsHide: true }).trim()
    if (out) return out
  } catch (_) {
    /* fall through */
  }
  return 'python'
}

function startBackend() {
  const pythonPath = resolvePythonExecutable()
  const backendDir = path.join(__dirname, '..', 'backend')
  const logsDir = path.join(__dirname, '..', 'logs')
  fs.mkdirSync(logsDir, { recursive: true })
  const backendOutLog = fs.createWriteStream(path.join(logsDir, 'backend.out.log'), { flags: 'a' })
  const backendErrLog = fs.createWriteStream(path.join(logsDir, 'backend.err.log'), { flags: 'a' })
  const startedAt = new Date().toISOString()
  backendOutLog.write(`\n[Electron] starting backend at ${startedAt}\n`)
  backendErrLog.write(`\n[Electron] starting backend at ${startedAt}\n`)
  const args = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000']
  const opts = { cwd: backendDir, stdio: 'pipe', windowsHide: true }
  if (process.platform === 'win32' && pythonPath === 'python') {
    opts.shell = true
  }
  backendProcess = spawn(pythonPath, args, opts)
  backendProcess.stdout.on('data', (d) => {
    backendOutLog.write(d)
    console.log('[Backend]', d.toString())
  })
  backendProcess.stderr.on('data', (d) => {
    backendErrLog.write(d)
    console.error('[Backend]', d.toString())
  })
  backendProcess.on('exit', (code) => {
    const msg = `[Backend] exited with code ${code}\n`
    backendOutLog.write(msg)
    backendErrLog.write(msg)
    backendOutLog.end()
    backendErrLog.end()
    console.log(msg.trim())
  })
}

function showSplash() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 320,
    frame: false,
    transparent: true,
    resizable: false,
    center: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    icon: appIcon,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  })
  splashWindow.loadFile(path.join(__dirname, 'splash.html'))
}

function closeSplash() {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.close()
    splashWindow = null
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    show: false,
    frame: false,
    backgroundColor: '#0a0a0f',
    icon: appIcon,
    title: 'ONYX-OVERRIDE',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  })
  mainWindow.once('ready-to-show', () => {
    closeSplash()
    mainWindow.show()
    mainWindow.focus()
  })
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'build', 'index.html'))
  }
}

app.whenReady().then(async () => {
  if (process.platform === 'win32' && !appIcon.isEmpty()) {
    app.setAppUserModelId('com.onyxoverride.desktop')
  }
  showSplash()
  ensureOllama()
  const backendReady = await pingBackend()
  if (!backendReady) {
    startBackend()
    const ready = await waitForBackend()
    if (!ready) {
      console.warn('[Backend] 健康检查超时，界面仍会打开；若无法对话请确认后端 8000 端口与 Ollama 已启动')
    }
  } else {
    console.log('[Backend] reusing existing backend on 127.0.0.1:8000')
  }
  createWindow()
})

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill()
  if (process.platform !== 'darwin') app.quit()
})

ipcMain.on('window-minimize', () => mainWindow?.minimize())
ipcMain.on('window-maximize', () =>
  mainWindow?.isMaximized() ? mainWindow.unmaximize() : mainWindow?.maximize()
)
ipcMain.on('window-close', () => {
  if (backendProcess) backendProcess.kill()
  mainWindow?.close()
})
