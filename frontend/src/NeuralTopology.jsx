import React, { useEffect, useMemo, useState } from 'react';
import './NeuralTopology.css';

const NODES = [
  { id: 'router', label: '路由', x: 50, y: 18 },
  { id: 'memory', label: '记忆', x: 18, y: 50 },
  { id: 'tools', label: '工具', x: 82, y: 50 },
  { id: 'reason', label: '推理', x: 35, y: 82 },
  { id: 'critic', label: 'Critic', x: 65, y: 82 },
  { id: 'core', label: 'Agent', x: 50, y: 50 },
];

const EDGES = [
  ['router', 'core'],
  ['memory', 'core'],
  ['tools', 'core'],
  ['core', 'reason'],
  ['core', 'critic'],
  ['tools', 'memory'],
];

function nodeById(id) {
  return NODES.find((n) => n.id === id);
}

export default function NeuralTopology({ apiBase, agentSteps = [] }) {
  const [events, setEvents] = useState([]);
  const [pulse, setPulse] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await fetch(`${apiBase}/meta/visual-events?limit=40`);
        if (!r.ok) return;
        const data = await r.json();
        if (!cancelled) setEvents(data.events || []);
      } catch {
        /* ignore */
      }
    };
    load();
    const t = setInterval(load, 2500);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [apiBase]);

  useEffect(() => {
    const last = agentSteps[agentSteps.length - 1];
    if (!last) return;
    if (last.type === 'tool_call') setPulse('tools');
    else if (last.type === 'thinking') setPulse('reason');
    else if (last.type === 'policy_denied') setPulse('critic');
    else setPulse('core');
    const t = setTimeout(() => setPulse(null), 900);
    return () => clearTimeout(t);
  }, [agentSteps]);

  const activeFromEvents = useMemo(() => {
    const e = events[0];
    if (!e) return null;
    if (e.type === 'neural_pulse') {
      const tool = e.payload?.tool || '';
      if (String(tool).includes('browser')) return 'tools';
      if (String(tool).includes('search') || String(tool).includes('memory')) return 'memory';
      return 'tools';
    }
    if (e.type === 'plan_created') return 'router';
    return 'core';
  }, [events]);

  const active = pulse || activeFromEvents;

  return (
    <div className="neural-topology" aria-label="神经元拓扑">
      <div className="neural-title">神经拓扑 · 实时</div>
      <svg viewBox="0 0 100 100" className="neural-svg">
        {EDGES.map(([a, b]) => {
          const na = nodeById(a);
          const nb = nodeById(b);
          if (!na || !nb) return null;
          const lit = active === a || active === b;
          return (
            <line
              key={`${a}-${b}`}
              x1={na.x}
              y1={na.y}
              x2={nb.x}
              y2={nb.y}
              className={lit ? 'neural-edge active' : 'neural-edge'}
            />
          );
        })}
        {NODES.map((n) => (
          <g key={n.id} className={`neural-node ${active === n.id ? 'pulse' : ''}`}>
            <circle cx={n.x} cy={n.y} r={n.id === 'core' ? 9 : 7} />
            <text x={n.x} y={n.y + 14} textAnchor="middle">
              {n.label}
            </text>
          </g>
        ))}
      </svg>
      <div className="neural-feed">
        {events.slice(0, 4).map((ev) => (
          <div key={ev.id} className="neural-feed-item">
            <span>{ev.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
