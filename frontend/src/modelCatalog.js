/**
 * 与 backend/.env 中 LOCKED_MODEL_ID 保持一致。
 * 当前模式：LLM_BACKEND=openai_compatible，vLLM 跑在 WSL localhost:8001
 * 若切回 Ollama 路线，改为 Ollama tag（如 'qwen3:14b'）并更新 LABEL。
 */
export const LOCKED_MODEL_ID = '/mnt/d/models/Gemma-4-26B-A4B-NVFP4';
export const LOCKED_MODEL_LABEL = 'Gemma 4 26B · vLLM (本地)';

export const UI_MODEL_OPTIONS = [{ id: LOCKED_MODEL_ID, label: LOCKED_MODEL_LABEL }];

export const UI_MODEL_IDS = new Set([LOCKED_MODEL_ID]);

export function labelForModel(modelId = '') {
  const hit = UI_MODEL_OPTIONS.find((option) => option.id === modelId);
  if (hit) return hit.label;
  if (!modelId) return '后端默认模型';
  if (modelId.startsWith('gpt-') || modelId.startsWith('o')) return `OpenAI · ${modelId}`;
  if (modelId.includes('Gemma') || modelId.includes('gemma')) return `Gemma · ${modelId}`;
  return modelId;
}

export function filterModelsForUi(models = []) {
  const resolved = (Array.isArray(models) ? models : [])
    .map((m) => {
      const id = typeof m === 'string' ? m : m?.id || m?.model || m?.name;
      return id ? { id, source: m?.source || 'runtime' } : null;
    })
    .filter(Boolean);
  if (resolved.length) return resolved;
  return [{ id: LOCKED_MODEL_ID, source: 'locked' }];
}
