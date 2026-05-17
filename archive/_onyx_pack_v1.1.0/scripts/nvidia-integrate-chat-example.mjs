/**
 * 调用 NVIDIA Integrate API（OpenAI 兼容 Chat Completions）。
 *
 * 用法（不要把 key 写进文件）：
 *   set NVIDIA_API_KEY=nvapi-你的密钥
 *   node scripts/nvidia-integrate-chat-example.mjs
 *
 * 与后端对齐：backend/.env 中
 *   LLM_BACKEND=openai_compatible
 *   OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
 *   OPENAI_API_KEY=同上
 *   AGENT_DEFAULT_MODEL=与 Build 面板 / 文档一致的 model id
 */
const invokeUrl = "https://integrate.api.nvidia.com/v1/chat/completions";
const stream = false;

const apiKey = process.env.NVIDIA_API_KEY || process.env.OPENAI_API_KEY;
if (!apiKey) {
  console.error("请设置环境变量 NVIDIA_API_KEY 或 OPENAI_API_KEY（勿提交到 Git）。");
  process.exit(1);
}

const headers = {
  Authorization: `Bearer ${apiKey}`,
  Accept: stream ? "text/event-stream" : "application/json",
  "Content-Type": "application/json",
};

const payload = {
  model: process.env.NVIDIA_MODEL || "meta/llama-4-maverick-17b-128e-instruct",
  messages: [{ role: "user", content: process.env.NVIDIA_PROMPT || "用一句话介绍你自己。" }],
  max_tokens: 512,
  temperature: 1.0,
  top_p: 1.0,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
  stream,
};

const res = await fetch(invokeUrl, {
  method: "POST",
  headers,
  body: JSON.stringify(payload),
});

if (!res.ok) {
  const t = await res.text();
  console.error(res.status, t);
  process.exit(1);
}

if (stream) {
  for await (const chunk of res.body) {
    process.stdout.write(chunk);
  }
  process.stdout.write("\n");
} else {
  const data = await res.json();
  console.log(JSON.stringify(data, null, 2));
}
