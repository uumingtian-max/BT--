const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

async function requestJson(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.error || `HTTP ${response.status}`);
  }
  return data;
}

export async function fetchAutomationCapabilities() {
  const data = await requestJson('/automation/capabilities');
  return data.capabilities || null;
}

export async function fetchAutomationRuns(limit = 20) {
  const data = await requestJson(`/automation/runs?limit=${encodeURIComponent(limit)}`);
  return data.runs || [];
}

export async function fetchAutomationEvents(limit = 50, runId = '') {
  const query = new URLSearchParams({ limit: String(limit) });
  if (runId) query.set('run_id', runId);
  const data = await requestJson(`/automation/events?${query.toString()}`);
  return data.events || [];
}

export async function runAutomationOnce(taskKind = 'project_check', target = 'all') {
  const data = await requestJson('/automation/run', {
    method: 'POST',
    body: JSON.stringify({ task_kind: taskKind, target }),
  });
  return data.run;
}

export async function createAutomationJob({ name, taskKind = 'project_check', target = 'all', enabled = true, params = {} }) {
  const data = await requestJson('/automation/jobs', {
    method: 'POST',
    body: JSON.stringify({ name, task_kind: taskKind, target, enabled, params }),
  });
  return data.job;
}

export async function runAutomationJob(jobId) {
  const data = await requestJson(`/automation/jobs/${encodeURIComponent(jobId)}/run`, { method: 'POST' });
  return data.run;
}

export async function setAutomationJobEnabled(jobId, enabled) {
  return requestJson(`/automation/jobs/${encodeURIComponent(jobId)}/enable?enabled=${enabled ? 'true' : 'false'}`, {
    method: 'POST',
  });
}
