// API helpers for the Agent Workbench UI.
// Keep this file small and dependency-free so panels can reuse it without
// coupling to App.js internals.

export const DEFAULT_API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function fetchJson(path, { apiBase = DEFAULT_API_BASE, signal } = {}) {
  const response = await fetch(`${apiBase}${path}`, { signal });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`${path} failed: ${response.status} ${text}`.trim());
  }
  return response.json();
}

export function getToolRegistry(options) {
  return fetchJson('/meta/tools/registry', options);
}

export function getToolRiskSummary(options) {
  return fetchJson('/meta/tools/risks', options);
}

export function getAgentTimelineContract(options) {
  return fetchJson('/meta/agent/timeline/contract', options);
}

export function groupToolsByRegistry(tools = []) {
  return tools.reduce((acc, tool) => {
    const group = tool.group || 'other';
    if (!acc[group]) acc[group] = [];
    acc[group].push(tool);
    return acc;
  }, {});
}

export function riskBadgeLabel(riskLevel) {
  const labels = {
    safe: '低风险',
    confirm: '需确认',
    dangerous: '高风险',
  };
  return labels[riskLevel] || '未知';
}

export function normalizeTimelineEventForDisplay(event) {
  return {
    id: event.step_id || `${event.type}-${event.index}`,
    type: event.type || 'thinking',
    status: event.status || 'success',
    title: event.title || event.type || '事件',
    content: event.content || '',
    tool: event.tool || null,
    riskLevel: event.risk_level || null,
    params: event.params || null,
    result: event.result ?? null,
    error: event.error || null,
    createdAt: event.created_at || null,
    raw: event,
  };
}
