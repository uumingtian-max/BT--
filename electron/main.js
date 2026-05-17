const { app, BrowserWindow, ipcMain, nativeImage } = require('electron')
const fs = require('fs')
const path = require('path')
const http = require('http')
const { spawn, execSync } = require('child_process')

let mainWindow
let splashWindow
let backendProcess
const isDev = process.env.NODE_ENV === 'development'

function loadBackendEnv() {
  const envPath = path.join(__dirname, '..', 'backend', '.env')
  if (!fs.existsSync(envPath)) return
  const raw = fs.readFileSync(envPath, 'utf8')
  for (const line of raw.split(/\r?\n/)) {
    let s = line.trim()
    if (!s || s.startsWith('#')) continue
    if (s.startsWith('export ')) s = s.slice(7).trim()
    const eq = s.indexOf('=')
    if (eq <= 0) continue
    const key = s.slice(0, eq).trim()
    let value = s.slice(eq + 1).trim()
    if (!key || process.env[key]) continue
    if (
      value.length >= 2 &&
      ((value[0] === '"' && value[value.length - 1] === '"') ||
        (value[0] === "'" && value[value.length - 1] === "'"))
    ) {
      value = value.slice(1, -1)
    }
    process.env[key] = value
  }
}

loadBackendEnv()

function backendPort() {
  const raw = String(process.env.BACKEND_PORT || '8000').trim()
  const parsed = Number.parseInt(raw, 10)
  if (Number.isInteger(parsed) && parsed > 0 && parsed <= 65535) return parsed
  return 8000
}

const BACKEND_PORT = backendPort()
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`
process.env.BKLT_BACKEND_URL = BACKEND_URL
process.env.ONYX_BACKEND_URL = BACKEND_URL // compatibility for older frontend/scripts

// vLLM 模式下跳过 Ollama 检查（LLM_BACKEND=openai_compatible）
const isVllmMode =
  process.env.LLM_BACKEND === 'openai_compatible' ||
  process.env.LLM_BACKEND === 'vllm' ||
  process.env.SKIP_OLLAMA === '1'

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
  if (isVllmMode) {
    console.log('[Ollama] skipped — vLLM / openai_compatible mode')
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
    const req = http.get(`${BACKEND_URL}/health`, (res) => {
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
  const args = ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)]
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
    title: 'BKLT 黑光',
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
    // Vite 构建输出仍在 frontend/build（vite.config.js outDir: 'build'）
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'build', 'index.html'))
  }
}

app.whenReady().then(async () => {
  if (process.platform === 'win32' && !appIcon.isEmpty()) {
    app.setAppUserModelId('com.bklt.blacklight.desktop')
  }
  showSplash()
  ensureOllama()
  const backendReady = await pingBackend()
  if (!backendReady) {
    startBackend()
    const ready = await waitForBackend()
    if (!ready) {
      console.warn(`[Backend] 健康检查超时，界面仍会打开；请确认后端 ${BACKEND_PORT} 端口已启动`)
    }
  } else {
    console.log(`[Backend] reusing existing backend on 127.0.0.1:${BACKEND_PORT}`)
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
