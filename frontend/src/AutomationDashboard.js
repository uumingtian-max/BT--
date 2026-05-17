import React from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function fmtTime(value) {
  if (!value) return '暂无';
  const ts = Date.parse(value);
  if (!Number.isFinite(ts)) return '暂无';
  return new Date(ts).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatusBadge({ status }) {
  const value = status || 'unknown';
  return <span className={`auto-badge auto-badge-${value}`}>{value}</span>;
}

function RunCard({ run }) {
  let parsed = null;
  try {
    parsed = JSON.parse(run.result_json || '{}');
  } catch (_) {
    parsed = null;
  }
  const steps = parsed?.steps || [];
  return (
    <div className="auto-card auto-run-card">
      <div className="auto-card-head">
        <div>
          <strong>{run.task_kind}</strong>
          <span>{run.target}</span>
        </div>
        <StatusBadge status={run.status} />
      </div>
      <p>{run.summary || '暂无摘要'}</p>
      <div className="auto-meta-row">
        <span>开始：{fmtTime(run.started_at)}</span>
        <span>耗时：{run.duration_ms ?? '-'} ms</span>
      </div>
      {steps.length > 0 && (
        <div className="auto-step-list">
          {steps.map((step, index) => (
            <div key={`${step.label}-${index}`} className={`auto-step ${step.ok ? 'ok' : 'fail'}`}>
              <div className="auto-step-head">
                <strong>{step.label}</strong>
                <span>exit {step.exit_code ?? '-'}</span>
              </div>
              {step.output && <pre>{String(step.output).slice(0, 1200)}</pre>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EventRow({ event }) {
  return (
    <div className={`auto-event auto-event-${event.status || 'info'}`}>
      <div>
        <strong>{event.title}</strong>
        <span>{event.type}</span>
      </div>
      <time>{fmtTime(event.created_at)}</time>
    </div>
  );
}

export default function AutomationDashboard() {
  const [capabilities, setCapabilities] = React.useState(null);
  const [runs, setRuns] = React.useState([]);
  const [events, setEvents] = React.useState([]);
  const [taskKind, setTaskKind] = React.useState('project_check');
  const [target, setTarget] = React.useState('all');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  const refresh = React.useCallback(async () => {
    setError('');
    try {
      const [capRes, runsRes, eventsRes] = await Promise.all([
        fetch(`${API}/automation/capabilities`),
        fetch(`${API}/automation/runs?limit=20`),
        fetch(`${API}/automation/events?limit=50`),
      ]);
      if (capRes.ok) {
        const data = await capRes.json();
        setCapabilities(data.capabilities || null);
      }
      if (runsRes.ok) {
        const data = await runsRes.json();
        setRuns(data.runs || []);
      }
      if (eventsRes.ok) {
        const data = await eventsRes.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      setError(`自动化面板加载失败：${err.message || err}`);
    }
  }, []);

  React.useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 10000);
    return () => clearInterval(timer);
  }, [refresh]);

  const runOnce = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/automation/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_kind: taskKind, target }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`);
      await refresh();
    } catch (err) {
      setError(`执行失败：${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const taskKinds = capabilities?.task_kinds || ['project_check'];
  const targets = capabilities?.targets || ['all'];

  return (
    <div className="profile-panel automation-dashboard">
      <div className="profile-header">
        <div>
          <h2>自动化维护</h2>
          <p className="profile-muted">运行项目检查、查看维护历史和可视化事件。</p>
        </div>
        <button type="button" className="profile-btn" onClick={refresh} disabled={loading}>
          刷新
        </button>
      </div>

      <div className="profile-card auto-control-card">
        <div className="auto-control-row">
          <label>
            任务
            <select value={taskKind} onChange={(e) => setTaskKind(e.target.value)}>
              {taskKinds.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label>
            目标
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              {targets.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <button type="button" className="profile-btn dashboard-primary-btn" onClick={runOnce} disabled={loading}>
            {loading ? '执行中…' : '立即运行'}
          </button>
        </div>
        {error && <p className="health-warn">{error}</p>}
      </div>

      <div className="dashboard-grid">
        <div className="profile-card dashboard-major-card">
          <div className="dash-card-head">
            <h3>最近运行</h3>
            <span>{runs.length} 条</span>
          </div>
          <div className="auto-run-list">
            {runs.map((run) => <RunCard key={run.id} run={run} />)}
            {!runs.length && <p className="profile-muted">暂无自动化运行记录。</p>}
          </div>
        </div>

        <div className="profile-card">
          <div className="dash-card-head">
            <h3>事件流</h3>
            <span>{events.length} 条</span>
          </div>
          <div className="auto-event-list">
            {events.map((event) => <EventRow key={event.id} event={event} />)}
            {!events.length && <p className="profile-muted">暂无可视化事件。</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
