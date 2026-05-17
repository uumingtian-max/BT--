# 手机端随时随地访问

目标：手机端保持干净界面，但不管在哪里都能连到电脑上的模型和 Agent。

默认 FastAPI 端口为 **8002**（可在 `backend/.env` 设置 `BACKEND_PORT`）。

## 当前实现

- 同 Wi-Fi：继续打开 `http://电脑IP:8002/mobile/`（若你改了 `BACKEND_PORT` 则替换端口号），不增加登录步骤。
- 公网域名/隧道：第一次打开会出现极简口令页。
- 解锁后仍是一个干净聊天界面。
- 大模型、文件、浏览器、部署发布动作都在电脑端执行。

## 推荐方式

### 方式 A：Tailscale

最稳，适合个人用。电脑和 iPhone 都登录同一个 Tailscale 账号，然后手机访问电脑的 Tailscale IP：

```text
http://电脑TailscaleIP:8002/mobile/
```

### 方式 B：Cloudflare Tunnel

适合想要一个 HTTPS 域名。把隧道指向本机后端（端口与 `BACKEND_PORT` 一致，默认 8002）：

```text
http://127.0.0.1:8002
```

手机打开：

```text
https://你的域名/mobile/
```

公网域名会要求输入 `MOBILE_ACCESS_TOKEN`。

## 设置口令

运行：

```bat
START_REMOTE_MOBILE.bat
```

脚本会写入 `backend\.env`：

```env
MOBILE_ACCESS_TOKEN=随机口令
```

## 启动

电脑上保持运行二选一：

```bat
START_MOBILE.bat
```

如果桌面端（Electron）已经占用默认后端端口，远程手机可另开：

```bat
START_TAILSCALE_MOBILE.bat
```

（可通过环境变量 `BACKEND_PORT` 与 `backend\.env` 对齐端口。）

然后手机用 Tailscale IP 或 Cloudflare Tunnel 域名访问 `/mobile/`。

## 安全边界

不要把后端监听端口直接裸露到公网。远程访问必须走 VPN 或 HTTPS 隧道，并保留访问口令。
