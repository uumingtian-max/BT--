# 能力：会话记忆与 FTS

Triggers: memories,记忆,consolidate,vault,会话搜索,preferences,feature_chat_memory,feature chat memory,feature-chat-memory,chat memory,能力,会话记忆与,FTS,记住这个,上次说过,我的偏好,别忘了

---

**何时使用**：用户涉及 ONYX **会话记忆与 FTS**（`feature_chat_memory`）或相关 API/面板/斜杠命令时**应**挂载；系统体检 `/meta/doctor` 失败也可附带本技能。

## 执行步骤
1. API：`/chat/memories/*`、`/chat/sessions/search`、偏好 `/chat/preferences`
2. 写入前合并近似条目；引用记忆时标注可能过时
3. 导出：`/chat/memories/vault/export` 需用户知情同意

## 避免
- 无工具/无读取就声称「已完成」或编造文件/命令输出。
- 把 `.env`、token、密钥写入聊天或长期记忆。

## ONYX 对接
- `/chat/memories/*` · `/chat/sessions/search` · `/chat/preferences`

## 关联技能
- `persistent_context`
- `memory_eval_consolidation`
- `skills_master_index`

## 自测用语（习惯体检 / 人工抽检）
- 查一下chat memory功能状态
- [skill:feature_chat_memory] 走对应 API 试一步
