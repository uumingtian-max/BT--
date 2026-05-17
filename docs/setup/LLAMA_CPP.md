# llama.cpp 本机推理（多模态 Gemma 4）

BT（黑光）通过 **llama-server** 暴露 OpenAI 兼容 API（默认 `http://127.0.0.1:8001/v1`），后端在 `backend\.env` 里使用 `LLM_BACKEND=openai_compatible`。

## 当前本机模型（多模态）

- **主模型** `LLAMA_CPP_MODEL`：`C:\Users\ROG\Documents\Downloads\Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-Q5_K_P.gguf`
- **视觉** `LLAMA_CPP_MMPROJ`：`C:\Users\ROG\Documents\Downloads\mmproj-Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-f16.gguf`
- **API 模型名** `LLAMA_CPP_ALIAS` / `AGENT_DEFAULT_MODEL`：`Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced-Q5_K_P`

主权重约 18GB；**mmproj** 缺了只能纯文本，不能看图。

## 一键启动

1. 确认 `C:\llama-cpp\llama-server.exe` 存在（或在 `backend\.env` 改 `LLAMA_CPP_EXE`）。
2. 双击 **`launcher\START_APP.bat`**：会先跑 `scripts\ensure-llama-cpp.ps1`，再开 Electron。
3. 只起网关：双击 **`launcher\打开本机Gemma模型.cmd`**，或：

```powershell
powershell -File scripts\ensure-llama-cpp.ps1
```

## 配置模板

```bat
copy backend\.env.local-llamacpp.example backend\.env
```

改路径后重启应用；`LOCKED_MODEL_ID` 与 `LLAMA_CPP_ALIAS` 必须一致；前端 `frontend\src\modelCatalog.js` 里的 id 也要一致。

## 排障

- **8001 连不上**：看 `logs\llama-server.log`；显存紧就调低 `LLAMA_CPP_CTX_SIZE` 或 `LLAMA_CPP_FIT_TARGET`。
- **模型 id 不对**：浏览器打开 `http://127.0.0.1:8001/v1/models`，把返回的 `id` 写进 `.env` 和 `modelCatalog.js`。
- **不能识图**：检查 `LLAMA_CPP_MMPROJ` 路径是否与主模型配套。

日志：`logs\llama-server.log` · 启动器：`logs\launch-llama-server.cmd`
