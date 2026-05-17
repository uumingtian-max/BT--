# 本地超级智能体栈

Triggers: openhuman,本地超级代理,离线优先,private ai,personal_local_super_agent,personal local super agent,personal-local-super-agent,本地超级智能体栈,离线,本机agent,私有,不上传,无限流

---

**何时使用**：用户强调本机/离线/隐私/不上传/不要限流时**必须**挂载。

## 执行步骤
1. 本机优先：`copy backend\.env.local-gemma4.example backend\.env`（Gemma4 E4B + vLLM，无限流）。
2. 启动 `scripts\START_VLLM_GEMMA4.bat` → `START_APP_LOCAL.bat`；或 Ollama 路线用 `START_APP.bat`。
3. 组合：`/agent/run` + `AGENT_SKILL_PACK=1` + `/meta/doctor` + 习惯体检（`feature_habit_pipeline`）。
4. 云 API / Integrate 须用户显式配置；勿默认上传桌面/记忆数据。

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- 默认本机：`AGENT_SKILL_PACK=1` + `/agent/run` + `/meta/doctor`
- 推荐：`LLM_BACKEND=openai_compatible` + vLLM `google/gemma-4-E4B-it`（24GB）
- 勿默认把用户数据上传外网；云 API 须用户显式配置

## 关联技能
- `onyx_ollama_ops`
- `trust_and_decline`
- `feature_habit_pipeline`

## 自测用语（习惯体检 / 人工抽检）
- 我要完全本机不限流怎么用
- 离线优先怎么配置
