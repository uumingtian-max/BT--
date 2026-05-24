/**
 * 与 backend/.env 中 LOCKED_MODEL_ID / LLAMA_CPP_ALIAS 保持一致。
 * 当前：LLM_BACKEND=openai_compatible，模型网关一般在 http://127.0.0.1:8001/v1
 */
export const LOCKED_MODEL_ID = 'nemotron-omni';
export const LOCKED_MODEL_LABEL = '黑光 · 动态多模态';

export const UI_MODEL_OPTIONS = [{ id: LOCKED_MODEL_ID, label: LOCKED_MODEL_LABEL }];

export const UI_MODEL_IDS = new Set([LOCKED_MODEL_ID]);

const MODEL_ALIAS = [
  [/^nemotron-omni$/i, '黑光 · 动态多模态'],
  [/nemotron-3-nano-omni/i, '黑光 · 动态多模态'],
  [/llama-3\.1-nemotron-safety-guard-8b-v3/i, '黑光 · 安全护栏'],
  [/gemma-4/i, '黑光 · Gemma 4'],
];

export function labelForModel(modelId = '') {
  const compact = String(modelId || '').trim();
  for (const [pattern, alias] of MODEL_ALIAS) {
    if (pattern.test(compact)) return alias;
  }
  const hit = UI_MODEL_OPTIONS.find((option) => option.id === modelId);
  if (hit) return hit.label;
  if (!modelId) return '后端默认模型';
  if (modelId.startsWith('gpt-') || modelId.startsWith('o')) return `OpenAI · ${modelId}`;
  if (modelId.includes('Gemma') || modelId.includes('gemma')) return `Gemma · ${modelId}`;
  if (modelId.includes('Llama') || modelId.includes('llama')) return `Llama · ${modelId}`;
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
