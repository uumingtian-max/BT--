import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import './NeuralTopology.css';

const WORKFLOW_NODES = [
  { id: 'input', label: '输入', x: 8, y: 50, kind: 'io' },
  { id: 'router', label: '路由', x: 20, y: 50, kind: 'control' },
  { id: 'core', label: '黑光核心', x: 36, y: 50, kind: 'core' },
  { id: 'planner', label: '规划', x: 52, y: 20, kind: 'reason' },
  { id: 'vision', label: '多模感知', x: 52, y: 80, kind: 'vision' },
  { id: 'tools', label: '工具执行', x: 70, y: 32, kind: 'tool' },
  { id: 'memory', label: '记忆检索', x: 70, y: 68, kind: 'memory' },
  { id: 'critic', label: '校验', x: 86, y: 50, kind: 'critic' },
  { id: 'output', label: '输出', x: 96, y: 50, kind: 'io' },
];

const WORKFLOW_EDGES = [
  ['input', 'router'],
  ['router', 'core'],
  ['core', 'planner'],
  ['core', 'vision'],
  ['core', 'tools'],
  ['core', 'memory'],
  ['planner', 'tools'],
  ['vision', 'tools'],
  ['tools', 'critic'],
  ['memory', 'critic'],
  ['critic', 'output'],
];

const STAGE_ORDER = ['core', 'planner', 'vision', 'tools', 'memory', 'critic', 'output'];

const TRAILS = {
  core: ['input', 'router', 'core'],
  planner: ['input', 'router', 'core', 'planner'],
  vision: ['input', 'router', 'core', 'vision'],
  tools: ['input', 'router', 'core', 'tools'],
  memory: ['input', 'router', 'core', 'memory'],
  critic: ['input', 'router', 'core', 'tools', 'critic'],
  output: ['input', 'router', 'core', 'tools', 'critic', 'output'],
};

const TOOL_STAGE_HINTS = {
  vision: ['image', 'video', 'vision', 'screen', 'ocr', 'camera', 'audio', 'speech', 'multimodal'],
  memory: ['memory', 'notebook', 'rag', 'retriev', 'search', 'knowledge', 'kb'],
};

const MODALITY_HINTS = {
  image: ['image', 'png', 'jpg', 'jpeg', 'gif', 'vision', 'ocr', 'screenshot', 'photo', 'img'],
  video: ['video', 'mp4', 'mov', 'hunyuan', 'clip', 'frame'],
  audio: ['audio', 'voice', 'speech', 'mic', 'asr', 'wav', 'mp3'],
  text: ['text', 'chat', 'answer', 'thinking', 'summary'],
};

function nodeById(id) {
  return WORKFLOW_NODES.find((n) => n.id === id);
}

function edgeKey(a, b) {
  return `${a}->${b}`;
}

function stringifySafe(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function detectStageFromTool(tool = '') {
  const lowered = String(tool).toLowerCase();
  if (TOOL_STAGE_HINTS.vision.some((k) => lowered.includes(k))) return 'vision';
  if (TOOL_STAGE_HINTS.memory.some((k) => lowered.includes(k))) return 'memory';
  return 'tools';
}

function stageFromStep(step) {
  if (!step) return 'core';
  if (step.type === 'final_answer') return 'output';
  if (step.type === 'thinking') return 'planner';
  if (step.type === 'tool_confirm_required' || step.type === 'policy_denied') return 'critic';
  if (step.type === 'tool_call' || step.type === 'tool_result') return detectStageFromTool(step.tool);
  return 'core';
}

function stageFromEvent(event) {
  if (!event) return 'core';
  const probe = `${event.type || ''} ${event.title || ''}`.toLowerCase();
  if (probe.includes('plan') || probe.includes('route')) return 'planner';
  if (probe.includes('memory') || probe.includes('notebook')) return 'memory';
  if (probe.includes('image') || probe.includes('video') || probe.includes('audio') || probe.includes('vision')) return 'vision';
  if (probe.includes('tool')) return 'tools';
  if (probe.includes('deny') || probe.includes('guard') || probe.includes('confirm')) return 'critic';
  if (probe.includes('final') || probe.includes('answer')) return 'output';
  return 'core';
}

function detectModalities(payload = '') {
  const text = String(payload).toLowerCase();
  const hit = new Set();
  Object.entries(MODALITY_HINTS).forEach(([key, terms]) => {
    if (terms.some((term) => text.includes(term))) hit.add(key);
  });
  if (!hit.size) hit.add('text');
  return hit;
}

function modalitiesFromStep(step) {
  if (!step) return new Set(['text']);
  const merged = [
    step.type,
    step.tool,
    step.title,
    step.content,
    step.text,
    stringifySafe(step.params),
    stringifySafe(step.result),
  ]
    .filter(Boolean)
    .join(' ');
  return detectModalities(merged);
}

function parseDurationMs(step) {
  if (!step) return 0;
  const candidate = step.elapsed_ms ?? step.duration_ms ?? step.latency_ms ?? step.cost_ms ?? 0;
  const value = Number(candidate);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function formatEventTime(ts) {
  if (!ts) return '';
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('zh-CN', { hour12: false });
}

function formatDuration(totalMs = 0) {
  if (!totalMs || totalMs <= 0) return '—';
  if (totalMs >= 1000) return `${(totalMs / 1000).toFixed(2)}s`;
  return `${Math.round(totalMs)}ms`;
}

function summarizeStep(step) {
  if (!step) return '等待';
  if (step.type === 'thinking') return '推理中';
  if (step.type === 'tool_call') return `调用 ${step.tool || '工具'}`;
  if (step.type === 'tool_result') return `${step.tool || '工具'} 返回`;
  if (step.type === 'tool_confirm_required') return '等待人工确认';
  if (step.type === 'policy_denied') return '策略拦截';
  if (step.type === 'final_answer') return '最终回答';
  return step.type || '步骤';
}

function trimPreview(raw, max = 240) {
  const text = String(raw || '').trim();
  if (!text) return '—';
  return text.length > max ? `${text.slice(0, max)}...` : text;
}

function detailForStep(step) {
  if (!step) return '暂无步骤详情。';
  if (step.type === 'tool_call') return trimPreview(JSON.stringify(step.params || {}, null, 2), 560);
  if (step.type === 'tool_result') return trimPreview(typeof step.result === 'string' ? step.result : JSON.stringify(step.result || {}, null, 2), 560);
  return trimPreview(step.content || step.message || step.text || '', 560);
}

export default function NeuralTopology({ apiBase, agentSteps = [] }) {
  const [events, setEvents] = useState([]);
  const [pulseNode, setPulseNode] = useState(null);
  const [selectedStepId, setSelectedStepId] = useState(null);
  const [heartbeat, setHeartbeat] = useState(0);
  const [playbackOn, setPlaybackOn] = useState(false);
  const [hoverStageId, setHoverStageId] = useState(null);
  const eventScrollRef = useRef(null);
  const trackScrollRef = useRef(null);

  useEffect(() => {
    const timer = setInterval(() => setHeartbeat((v) => v + 1), 880);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadEvents = async () => {
      try {
        const response = await fetch(`${apiBase}/meta/visual-events?limit=40`);
        if (!response.ok) return;
        const data = await response.json();
        if (!cancelled) setEvents(Array.isArray(data.events) ? data.events : []);
      } catch {
        /* ignore */
      }
    };

    loadEvents();
    const timer = setInterval(loadEvents, 2500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [apiBase]);

  useEffect(() => {
    const last = agentSteps[agentSteps.length - 1];
    if (!last) return;
    const stage = stageFromStep(last);
    setPulseNode(stage);
    const timer = setTimeout(() => setPulseNode(null), 820);
    return () => clearTimeout(timer);
  }, [agentSteps]);

  const idleStage = STAGE_ORDER[(heartbeat + 1) % STAGE_ORDER.length];
  const activeStage = useMemo(() => {
    if (pulseNode) return pulseNode;
    if (agentSteps.length) return stageFromStep(agentSteps[agentSteps.length - 1]);
    if (events.length) return stageFromEvent(events[0]);
    return idleStage;
  }, [agentSteps, events, pulseNode, idleStage]);

  const activeTrail = TRAILS[activeStage] || TRAILS.core;
  const activeEdgeSet = useMemo(() => {
    const set = new Set();
    for (let index = 0; index < activeTrail.length - 1; index += 1) {
      set.add(edgeKey(activeTrail[index], activeTrail[index + 1]));
    }
    return set;
  }, [activeTrail]);

  const flowParticles = useMemo(() => {
    const particles = [];
    for (let index = 0; index < activeTrail.length - 1; index += 1) {
      const from = nodeById(activeTrail[index]);
      const to = nodeById(activeTrail[index + 1]);
      if (!from || !to) continue;
      const phase = ((heartbeat * 0.18) + index * 0.27) % 1;
      particles.push({
        key: `${from.id}-${to.id}`,
        x: from.x + (to.x - from.x) * phase,
        y: from.y + (to.y - from.y) * phase,
      });
    }
    return particles;
  }, [activeTrail, heartbeat]);

  const recentSteps = useMemo(() => {
    const sliced = agentSteps.slice(-16);
    const offset = Math.max(0, agentSteps.length - sliced.length);
    return sliced.map((step, index) => ({
      ...step,
      __id: offset + index,
      __stage: stageFromStep(step),
      __summary: summarizeStep(step),
      __duration: parseDurationMs(step),
    }));
  }, [agentSteps]);

  useEffect(() => {
    if (!recentSteps.length) {
      setSelectedStepId(null);
      return;
    }
    const hasSelection = recentSteps.some((step) => step.__id === selectedStepId);
    if (!hasSelection) setSelectedStepId(recentSteps[recentSteps.length - 1].__id);
  }, [recentSteps, selectedStepId]);

  useEffect(() => {
    if (trackScrollRef.current) {
      trackScrollRef.current.scrollLeft = trackScrollRef.current.scrollWidth;
    }
  }, [recentSteps]);

  const selectedStep = recentSteps.find((step) => step.__id === selectedStepId) || recentSteps[recentSteps.length - 1] || null;
  const selectedIndex = recentSteps.findIndex((step) => step.__id === selectedStepId);
  const visualStage = hoverStageId || selectedStep?.__stage || activeStage;

  useEffect(() => {
    if (!playbackOn) return undefined;
    if (!recentSteps.length) return undefined;
    const timer = setInterval(() => {
      const next = (selectedIndex + 1 + recentSteps.length) % recentSteps.length;
      setSelectedStepId(recentSteps[next].__id);
    }, 1080);
    return () => clearInterval(timer);
  }, [playbackOn, selectedIndex, recentSteps]);

  const stageStats = useMemo(() => {
    const counts = Object.fromEntries(STAGE_ORDER.map((stage) => [stage, 0]));
    let total = 0;
    recentSteps.forEach((step) => {
      if (counts[step.__stage] !== undefined) {
        counts[step.__stage] += 1;
        total += 1;
      }
    });
    return { counts, total: total || 1 };
  }, [recentSteps]);

  const modalityStats = useMemo(() => {
    const counts = { text: 0, image: 0, video: 0, audio: 0 };
    recentSteps.forEach((step) => {
      const modalities = modalitiesFromStep(step);
      modalities.forEach((key) => {
        if (counts[key] !== undefined) counts[key] += 1;
      });
    });
    if (!recentSteps.length && events.length) {
      events.slice(0, 4).forEach((event) => {
        const eventModalities = detectModalities(`${event.type || ''} ${event.title || ''}`);
        eventModalities.forEach((key) => {
          if (counts[key] !== undefined) counts[key] += 1;
        });
      });
    }
    const total = Object.values(counts).reduce((acc, value) => acc + value, 0) || 1;
    return { counts, total };
  }, [recentSteps, events]);

  const metrics = useMemo(() => {
    const stepCount = agentSteps.length;
    const toolCalls = agentSteps.filter((step) => step.type === 'tool_call').length;
    const multimodalHits = agentSteps.filter((step) => stageFromStep(step) === 'vision').length;
    const done = agentSteps.some((step) => step.type === 'final_answer');
    const guardHits = agentSteps.filter((step) => step.type === 'tool_confirm_required' || step.type === 'policy_denied').length;
    const totalDurationMs = agentSteps.reduce((sum, step) => sum + parseDurationMs(step), 0);
    return { stepCount, toolCalls, multimodalHits, done, guardHits, totalDurationMs };
  }, [agentSteps]);

  const recentEvents = events.slice(0, 6).map((event, index) => {
    const stage = stageFromEvent(event);
    return {
      id: event.id || `${event.type || 'event'}-${index}`,
      stage,
      stageLabel: nodeById(stage)?.label || '核心',
      title: event.title || event.type || '事件',
      time: formatEventTime(event.ts || event.time || event.created_at),
    };
  });

  const gateInfo = useMemo(() => {
    const gateSteps = agentSteps.filter((step) => step.type === 'tool_confirm_required' || step.type === 'policy_denied');
    const latest = gateSteps[gateSteps.length - 1] || null;
    return {
      total: gateSteps.length,
      pending: gateSteps.filter((step) => step.type === 'tool_confirm_required').length,
      denied: gateSteps.filter((step) => step.type === 'policy_denied').length,
      latestSummary: latest ? summarizeStep(latest) : '暂无接管点',
      latestStage: latest ? stageFromStep(latest) : 'core',
    };
  }, [agentSteps]);

  const laneStats = useMemo(() => {
    const focusStages = ['planner', 'vision', 'tools', 'memory', 'critic'];
    const total = Math.max(1, recentSteps.length);
    return focusStages.map((stage) => {
      const count = recentSteps.filter((step) => step.__stage === stage).length;
      const ratio = Math.round((count / total) * 100);
      return {
        stage,
        label: nodeById(stage)?.label || stage,
        count,
        ratio,
      };
    });
  }, [recentSteps]);

  const handleNodeHover = useCallback((nodeId) => {
    setHoverStageId(nodeId);
  }, []);

  const handleNodeLeave = useCallback(() => {
    setHoverStageId(null);
  }, []);

  return (
    <section className="workflow-visual" aria-label="Agent 工作流可视化">
      <header className="workflow-head">
        <div className="workflow-head-title">
          <p className="workflow-kicker">⚡ BT Agent Control Plane</p>
          <h3>黑光 · 动态多模工作流</h3>
          <p className="workflow-subtitle">实时展示推理、工具、多模态感知、记忆与校验状态</p>
        </div>

        <div className="workflow-status-pill" data-state={metrics.done ? 'done' : 'running'}>
          <i />
          <span>{metrics.done ? '本轮已完成' : '实时运行中'}</span>
        </div>
      </header>

      <div className="workflow-metrics">
        <div className="workflow-metric">
          <span>步骤</span>
          <strong>{metrics.stepCount}</strong>
        </div>
        <div className="workflow-metric">
          <span>工具调用</span>
          <strong>{metrics.toolCalls}</strong>
        </div>
        <div className="workflow-metric">
          <span>多模触发</span>
          <strong>{metrics.multimodalHits}</strong>
        </div>
        <div className="workflow-metric">
          <span>校验触发</span>
          <strong>{metrics.guardHits}</strong>
        </div>
        <div className="workflow-metric">
          <span>累计耗时</span>
          <strong>{formatDuration(metrics.totalDurationMs)}</strong>
        </div>
      </div>

      <div className="workflow-main">
        <div className="workflow-canvas-wrap">
          <div className="workflow-canvas-head">
            <span>执行拓扑</span>
            <strong>{nodeById(visualStage)?.label || '核心 Agent'}</strong>
          </div>
          <svg viewBox="0 0 104 100" className="workflow-canvas">
            {WORKFLOW_EDGES.map(([fromId, toId]) => {
              const from = nodeById(fromId);
              const to = nodeById(toId);
              if (!from || !to) return null;
              const active = activeEdgeSet.has(edgeKey(fromId, toId));
              return (
                <line
                  key={`${fromId}-${toId}`}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  className={`workflow-edge${active ? ' active' : ''}`}
                />
              );
            })}

            {flowParticles.map((particle) => (
              <circle key={particle.key} className="workflow-flow-particle" cx={particle.x} cy={particle.y} r="0.88" />
            ))}

            {WORKFLOW_NODES.map((node) => {
              const isActive = visualStage === node.id;
              const isHover = hoverStageId === node.id;
              return (
                <g
                  key={node.id}
                  className={`workflow-node ${node.kind}${isActive ? ' active' : ''}${isHover ? ' hover' : ''}`}
                  onMouseEnter={() => handleNodeHover(node.id)}
                  onMouseLeave={handleNodeLeave}
                >
                  <circle cx={node.x} cy={node.y} r={node.id === 'core' ? 6.4 : 5.1} />
                  <text x={node.x} y={node.y + 10} textAnchor="middle">
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <aside className="workflow-side">
          <div className="workflow-stage-card">
            <span>阶段占比</span>
            <strong>{nodeById(visualStage)?.label || '核心 Agent'}</strong>
            <small>{metrics.done ? '任务完成，可复查详情' : '持续监听步骤与事件流变化'}</small>
            <div className="workflow-stage-bars">
              {STAGE_ORDER.map((stage) => {
                const count = stageStats.counts[stage] || 0;
                const ratio = Math.round((count / stageStats.total) * 100);
                return (
                  <div className="workflow-stage-bar" key={stage}>
                    <label>{nodeById(stage)?.label || stage}</label>
                    <div className="workflow-stage-track">
                      <span style={{ width: `${ratio}%` }} />
                    </div>
                    <em>{ratio}%</em>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="workflow-modality-card">
            <div className="workflow-modality-head">
              <span>多模态态势</span>
              <strong>动态 I/O</strong>
            </div>
            <div className="workflow-modality-grid">
              {[
                { key: 'text', label: '文本' },
                { key: 'image', label: '图像' },
                { key: 'video', label: '视频' },
                { key: 'audio', label: '音频' },
              ].map((item) => {
                const value = modalityStats.counts[item.key] || 0;
                const ratio = Math.round((value / modalityStats.total) * 100);
                return (
                  <div key={item.key} className={`workflow-modality-item ${item.key}`}>
                    <span>{item.label}</span>
                    <strong>{ratio}%</strong>
                    <i style={{ width: `${ratio}%` }} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="workflow-gate-card">
            <div className="workflow-gate-head">
              <span>人工接管点</span>
              <strong>{gateInfo.total}</strong>
            </div>
            <div className="workflow-gate-grid">
              <div>
                <label>待确认</label>
                <b>{gateInfo.pending}</b>
              </div>
              <div>
                <label>被拦截</label>
                <b>{gateInfo.denied}</b>
              </div>
            </div>
            <div className={`workflow-gate-latest stage-${gateInfo.latestStage}`}>
              {gateInfo.latestSummary}
            </div>
          </div>

          <div className="workflow-lane-card">
            <div className="workflow-lane-head">
              <span>并行负载</span>
              <strong>{nodeById(visualStage)?.label || '核心'}</strong>
            </div>
            <div className="workflow-lane-list">
              {laneStats.map((lane) => (
                <div className="workflow-lane-row" key={`lane-${lane.stage}`}>
                  <label>{lane.label}</label>
                  <div className="workflow-lane-track">
                    <i className={`stage-${lane.stage}`} style={{ width: `${lane.ratio}%` }} />
                  </div>
                  <em>{lane.ratio}%</em>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      <div className="workflow-events">
        <div className="workflow-events-head">
          <span>实时事件流</span>
          <i className={`workflow-live-dot ${recentEvents.length ? 'live' : ''}`} />
        </div>
        <div className="workflow-events-scroll" ref={eventScrollRef}>
          {recentEvents.length ? (
            recentEvents.map((event) => (
              <div className="workflow-event-row" key={event.id}>
                <div className="workflow-event-title">
                  <b className={`stage-${event.stage}`}>{event.stageLabel}</b>
                  <span>{event.title}</span>
                </div>
                <time>{event.time || '--:--:--'}</time>
              </div>
            ))
          ) : (
            <div className="workflow-event-empty">等待事件流…</div>
          )}
        </div>
      </div>

      <div className="workflow-track-wrap">
        <div className="workflow-track-head">
          <span>执行轨迹</span>
          <div className="workflow-track-actions">
            <strong>{recentSteps.length ? `${recentSteps.length} 步` : '暂无轨迹'}</strong>
            <button
              type="button"
              className={`workflow-playback-btn ${playbackOn ? 'active' : ''}`}
              disabled={!recentSteps.length}
              onClick={() => setPlaybackOn((value) => !value)}
            >
              {playbackOn ? '停止回放' : '回放轨迹'}
            </button>
          </div>
        </div>
        <div className="workflow-stage-line" aria-hidden="true">
          {recentSteps.map((step) => (
            <i
              key={`line-${step.__id}`}
              className={`stage-${step.__stage}${step.__id === selectedStepId ? ' active' : ''}`}
            />
          ))}
        </div>
        <div className="workflow-track" ref={trackScrollRef}>
          {recentSteps.length ? (
            recentSteps.map((step) => (
              <button
                type="button"
                key={step.__id}
                className={`workflow-track-step stage-${step.__stage}${step.__id === selectedStepId ? ' active' : ''}`}
                onClick={() => setSelectedStepId(step.__id)}
                title={step.__summary}
              >
                <span>#{step.__id + 1}</span>
                <strong>{step.__summary}</strong>
                <em>{formatDuration(step.__duration)}</em>
              </button>
            ))
          ) : (
            <div className="workflow-step-empty">暂无步骤，发起 Agent 任务后这里会显示动态轨迹。</div>
          )}
        </div>
      </div>

      <div className="workflow-detail">
        <div className="workflow-detail-head">
          <span>步骤详情</span>
          <strong>{selectedStep ? nodeById(selectedStep.__stage)?.label : '等待步骤'}</strong>
        </div>
        <pre>{detailForStep(selectedStep)}</pre>
      </div>
    </section>
  );
}
