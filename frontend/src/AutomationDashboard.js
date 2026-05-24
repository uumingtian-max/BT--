import React from 'react';
import './AutomationDashboard.css';
import {
  fetchAutomationCapabilities,
  fetchAutomationEvents,
  fetchAutomationRunGraph,
  fetchAutomationRunGraphs,
  runAutomationOnce,
} from './automationApi';

function fmtTime(value) {
  if (!value) return '暂无';
  const ts = Date.parse(value);
  if (!Number.isFinite(ts)) return '暂无';
  return new Date(ts).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function StatusBadge({ status }) {
  const value = status || 'unknown';
  return <span className={`auto-badge auto-badge-${value}`}>{value}</span>;
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

function GraphCard({ graph, active, onPick }) {
  return (
    <button type="button" className={`auto-graph-card ${active ? 'active' : ''}`} onClick={() => onPick(graph.id)}>
      <div>
        <strong>{graph.title || graph.kind || graph.id}</strong>
        <span>{graph.target || 'all'}</span>
      </div>
      <div className="auto-graph-meta">
        <StatusBadge status={graph.status} />
        <small>{fmtTime(graph.started_at)}</small>
      </div>
    </button>
  );
}

function TimelineStep({ step }) {
  return (
    <div className={`auto-step ${step.status === 'success' ? 'ok' : step.status === 'failed' ? 'fail' : ''}`}>
      <div className="auto-step-head">
        <strong>{step.name}</strong>
        <span>{step.step_type} · #{step.step_index}</span>
      </div>
      <div className="auto-step-body">
        <small>{fmtTime(step.started_at)} → {fmtTime(step.ended_at)}</small>
        {step.duration_ms != null && <small>耗时 {step.duration_ms} ms</small>}
      </div>
    </div>
  );
}

export default function AutomationDashboard() {
  const [capabilities, setCapabilities] = React.useState(null);
  const [graphs, setGraphs] = React.useState([]);
  const [events, setEvents] = React.useState([]);
  const [selectedRunId, setSelectedRunId] = React.useState('');
  const [selectedGraph, setSelectedGraph] = React.useState(null);
  const [taskKind, setTaskKind] = React.useState('project_check');
  const [target, setTarget] = React.useState('all');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  const refresh = React.useCallback(async (pinRunId = selectedRunId) => {
    setError('');
    try {
      const [nextCapabilities, nextGraphs] = await Promise.all([
        fetchAutomationCapabilities(),
        fetchAutomationRunGraphs(20),
      ]);
      setCapabilities(nextCapabilities);
      setGraphs(nextGraphs);
      const runId = pinRunId || nextGraphs[0]?.id || '';
      setSelectedRunId(runId);
      const [nextEvents, nextGraph] = await Promise.all([
        fetchAutomationEvents(80, runId),
        runId ? fetchAutomationRunGraph(runId) : Promise.resolve(null),
      ]);
      setEvents(nextEvents);
      setSelectedGraph(nextGraph);
    } catch (err) {
      setError(`自动化面板加载失败：${err.message || err}`);
    }
  }, [selectedRunId]);

  React.useEffect(() => {
    refresh();
    const timer = setInterval(() => refresh(), 10000);
    return () => clearInterval(timer);
  }, [refresh]);

  const runOnce = async () => {
    setLoading(true);
    setError('');
    try {
      await runAutomationOnce(taskKind, target);
      await refresh();
    } catch (err) {
      setError(`执行失败：${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const pickRun = async (runId) => {
    setSelectedRunId(runId);
    setLoading(true);
    try {
      const [nextEvents, nextGraph] = await Promise.all([
        fetchAutomationEvents(80, runId),
        fetchAutomationRunGraph(runId),
      ]);
      setEvents(nextEvents);
      setSelectedGraph(nextGraph);
    } catch (err) {
      setError(`加载运行详情失败：${err.message || err}`);
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
          <h2>自动化维护 / Run Graph</h2>
          <p className="profile-muted">按运行图查看事件时间线，支持重启后追溯与审计。</p>
        </div>
        <button type="button" className="profile-btn" onClick={() => refresh(selectedRunId)} disabled={loading}>刷新</button>
      </div>

      <div className="profile-card auto-control-card">
        <div className="auto-control-row">
          <label>任务<select value={taskKind} onChange={(e) => setTaskKind(e.target.value)}>{taskKinds.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <label>目标<select value={target} onChange={(e) => setTarget(e.target.value)}>{targets.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          <button type="button" className="profile-btn dashboard-primary-btn" onClick={runOnce} disabled={loading}>{loading ? '执行中…' : '立即运行'}</button>
        </div>
        {error && <p className="health-warn">{error}</p>}
      </div>

      <div className="dashboard-grid">
        <div className="profile-card dashboard-major-card">
          <div className="dash-card-head"><h3>运行图列表</h3><span>{graphs.length} 条</span></div>
          <div className="auto-run-list">{graphs.map((g) => <GraphCard key={g.id} graph={g} active={selectedRunId === g.id} onPick={pickRun} />)}{!graphs.length && <p className="profile-muted">暂无运行图记录。</p>}</div>
        </div>

        <div className="profile-card">
          <div className="dash-card-head"><h3>运行时间线</h3><span>{selectedGraph?.steps?.length || 0} 步</span></div>
          {selectedGraph && (
            <div className="auto-graph-summary">
              <div className="auto-meta-row"><span>RunID：{selectedGraph.id}</span><span>开始：{fmtTime(selectedGraph.started_at)}</span><span>结束：{fmtTime(selectedGraph.ended_at)}</span></div>
              <p>{selectedGraph.summary || '暂无摘要'}</p>
              <div className="auto-step-list">{(selectedGraph.steps || []).map((step) => <TimelineStep key={step.id} step={step} />)}</div>
            </div>
          )}
          {!selectedGraph && <p className="profile-muted">请选择运行图查看详情。</p>}
        </div>

        <div className="profile-card dashboard-major-card">
          <div className="dash-card-head"><h3>事件流（按 Run 过滤）</h3><span>{events.length} 条</span></div>
          <div className="auto-event-list">{events.map((event) => <EventRow key={event.id} event={event} />)}{!events.length && <p className="profile-muted">暂无可视化事件。</p>}</div>
        </div>
      </div>
    </div>
  );
}
