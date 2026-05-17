# iPhone 安装方式

当前推荐用 iPhone PWA 安装，不需要 App Store，不需要 Apple 开发者账号。

## 安装到主屏幕

1. 电脑和 iPhone 连接同一个 Wi-Fi。
2. 电脑双击 `START_MOBILE.bat`，保持窗口不要关闭。
3. iPhone 用 Safari 打开脚本显示的地址，例如：

   `http://192.168.100.62:8000/mobile/`

4. 点 Safari 底部分享按钮。
5. 选择“添加到主屏幕”。
6. 名称填 `ONYX` 或 `ONYX-OVERRIDE`，点“添加”。

之后从 iPhone 主屏幕打开，它会以独立 App 形式全屏运行。

## 说明

- 这不是 `.ipa`，但使用体验接近 App。
- 语音录制需要 Safari 允许麦克风权限。
- 照片/视频上传走浏览器文件选择器。
- 手机端没有 Agent 面板；说“电脑帮我……”这类命令时，会自动交给电脑端 Agent 执行。

## 真正 IPA

如果要 `.ipa` 或上架 TestFlight / App Store，需要：

- 一台 Mac
- Xcode
- Apple Developer 账号
- 用 Capacitor / React Native / 原生 WebView 包装当前 `/mobile/` 前端
- 签名并打包

Windows 上不能直接生成可安装到 iPhone 的正式签名 IPA。
