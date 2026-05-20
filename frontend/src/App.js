import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import ReactMarkdown from 'react-markdown';
import './App.css';
import './electron-frame.css';
import BrandLogo, { BrandHero } from './BrandLogo';
import { DashboardPanel, SystemPanel, SkillsPanel, SchedulerPanel } from './OperatorPanels';
import { LOCKED_MODEL_ID, LOCKED_MODEL_LABEL, labelForModel } from './modelCatalog';
import { extractClipboardFiles } from './clipboardAttachments';

// Electron 通过 preload 注入真实后端地址；其余场景可由构建环境覆盖。
const API =
  (typeof window !== 'undefined' && window.electronAPI?.backendUrl) ||
  process.env.REACT_APP_API_URL ||
  'http://127.0.0.1:8000';
const APP_NAME = 'BT（黑光）';
const APP_TAGLINE = '本地 AI Agent 工作台';
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const Icon = ({ name, size = 16 }) => {
  const icons = {
    send: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
    paperclip: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.4 11.6l-8.5 8.5a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/></svg>,
    plus: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
    trash: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>,
    agent: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>,
    chat: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
    tool: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>,
    minimize: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>,
    maximize: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>,
    close: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
    copy: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
    check: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>,
    zap: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
    search: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
    file: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    cpu: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>,
    db: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>,
    globe: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>,
    activity: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
    chevron: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>,
    layers: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>,
  };
  return icons[name] || null;
};

const TOOL_META = {
  web_search: { icon: 'search', color: '#38bdf8', label: 'Web 搜索' },
  local_search: { icon: 'search', color: '#0ea5e9', label: '本地搜索' },
  local_scrape_url: { icon: 'globe', color: '#06b6d4', label: '抓取网页' },
  read_file: { icon: 'file', color: '#a78bfa', label: '读取文件' },
  write_file: { icon: 'file', color: '#f472b6', label: '写入文件' },
  list_files: { icon: 'layers', color: '#94a3b8', label: '列出文件' },
  execute_python: { icon: 'cpu', color: '#4ade80', label: '执行代码' },
  get_device_profile: { icon: 'activity', color: '#fb923c', label: '设备画像' },
  get_recent_desktop_files: { icon: 'file', color: '#fbbf24', label: '桌面文件' },
  get_recent_work_summary: { icon: 'activity', color: '#fb923c', label: '活动摘要' },
  get_evolution_profile: { icon: 'zap', color: '#a78bfa', label: '进化画像' },
  run_task_orchestration: { icon: 'layers', color: '#f43f5e', label: '多模型编排' },
  notebook_ingest: { icon: 'db', color: '#34d399', label: '写入知识库' },
  notebook_synthesize: { icon: 'db', color: '#6ee7b7', label: 'AI整理知识' },
  generate_image: { icon: 'zap', color: '#f59e0b', label: '生成图片' },
  generate_video: { icon: 'zap', color: '#ef4444', label: '生成视频' },
  text_to_speech: { icon: 'zap', color: '#8b5cf6', label: '文字转语音' },
  run_project_check: { icon: 'cpu', color: '#eab308', label: '项目检查' },
  open_url: { icon: 'globe', color: '#22d3ee', label: '打开链接' },
  open_path: { icon: 'file', color: '#94a3b8', label: '打开路径' },
  get_foreground_window: { icon: 'activity', color: '#fb923c', label: '前台窗口' },
  list_windows: { icon: 'layers', color: '#a1a1aa', label: '窗口列表' },
  focus_window: { icon: 'layers', color: '#f472b6', label: '聚焦窗口' },
  send_hotkey: { icon: 'zap', color: '#fbbf24', label: '快捷键' },
  type_text: { icon: 'chat', color: '#c4b5fd', label: '键入文字' },
  click_screen: { icon: 'cpu', color: '#4ade80', label: '屏幕点击' },
  browser_navigate: { icon: 'globe', color: '#38bdf8', label: '浏览器打开' },
  browser_screenshot: { icon: 'globe', color: '#0ea5e9', label: '网页截图' },
  browser_click_and_extract: { icon: 'globe', color: '#06b6d4', label: '浏览器点击' },
  browser_fill_form: { icon: 'globe', color: '#22d3ee', label: '浏览器填表' },
  run_parallel_subagents: { icon: 'layers', color: '#f43f5e', label: '并行子任务' },
  http_request: { icon: 'globe', color: '#22d3ee', label: 'HTTP 请求' },
  query_database: { icon: 'db', color: '#f97316', label: '查询数据库' },
};

function TimelineStep({ step, index, isLast }) {
  const [expanded, setExpanded] = useState(step.type === 'final_answer');
  const meta = TOOL_META[step.tool] || { icon: 'tool', color: '#7c6bff', label: step.tool || '工具' };

  const typeConfig = {
    thinking: { icon: 'cpu', color: '#7c6bff', label: '推理中', bg: 'rgba(124,107,255,0.08)', border: 'rgba(124,107,255,0.2)' },
    tool_call: { icon: meta.icon, color: meta.color, label: meta.label, bg: 'rgba(251,146,60,0.06)', border: 'rgba(251,146,60,0.18)' },
    tool_confirm_required: { icon: 'zap', color: '#fbbf24', label: '待确认', bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.25)' },
    tool_result: { icon: 'check', color: '#4ade80', label: '执行结果', bg: 'rgba(74,222,128,0.06)', border: 'rgba(74,222,128,0.15)' },
    final_answer: { icon: 'zap', color: '#a78bfa', label: '最终回答', bg: 'rgba(167,139,250,0.07)', border: 'rgba(167,139,250,0.2)' },
  };

  const cfg = typeConfig[step.type] || typeConfig.thinking;
  const isFinal = step.type === 'final_answer';

  return (
    <div className={`tl-step tl-step-${step.type}`} style={{ '--step-color': cfg.color }}>
      <div className="tl-connector">
        <div className="tl-dot" style={{ background: cfg.color, boxShadow: `0 0 8px ${cfg.color}55` }}>
          <Icon name={cfg.icon} size={10} />
        </div>
        {!isLast && <div className="tl-line" />}
      </div>
      <div className="tl-body" style={{ background: cfg.bg, borderColor: cfg.border }}>
        <button type="button" className="tl-header" onClick={() => setExpanded((e) => !e)}>
          <span className="tl-badge" style={{ color: cfg.color }}>
            {cfg.label}
            {step.tool && step.type === 'tool_call' && (
              <span className="tl-tool-name">→ {step.tool}</span>
            )}
          </span>
          <span className="tl-timing">步骤 {index + 1}</span>
          <span className={`tl-chevron ${expanded ? 'expanded' : ''}`}><Icon name="chevron" size={12} /></span>
        </button>
        {expanded && (
          <div className="tl-content">
            {step.type === 'thinking' && step.content && (
              <p className="tl-text">{step.content}</p>
            )}
            {step.type === 'tool_confirm_required' && step.content && (
              <p className="tl-text">{step.content}</p>
            )}
            {step.type === 'tool_call' && (
              <div className="tl-params">
                <div className="tl-params-label">参数</div>
                <pre>{JSON.stringify(step.params, null, 2)}</pre>
              </div>
            )}
            {step.type === 'tool_result' && (
              <div className="tl-result">
                <MediaPreview result={step.result} />
                <pre>{typeof step.result === 'string' ? step.result.slice(0, 2000) : JSON.stringify(step.result, null, 2)}</pre>
              </div>
            )}
            {isFinal && (
              <div className="tl-final-content">
                <ReactMarkdown components={markdownComponents}>{step.content}</ReactMarkdown>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ExecutionProgress({ steps, isRunning }) {
  const toolSteps = steps.filter((s) => s.type === 'tool_call');
  const resultSteps = steps.filter((s) => s.type === 'tool_result');
  const done = steps.some((s) => s.type === 'final_answer');
  const midCount = steps.filter((s) => s.type !== 'final_answer').length;

  return (
    <div className="exec-progress">
      <div className="exec-status">
        {isRunning && !done && (
          <span className="exec-running">
            <span className="exec-pulse" />
            {toolSteps.length > resultSteps.length
              ? `执行 ${toolSteps[toolSteps.length - 1]?.tool || '工具'}…`
              : '推理中…'}
          </span>
        )}
        {done && (
          <span className="exec-done">
            <Icon name="check" size={12} /> 完成 · {midCount} 个过程步骤 + 回答
          </span>
        )}
      </div>
      <div className="exec-bar">
        {steps.map((s, i) => (
          <div
            key={i}
            className={`exec-seg exec-seg-${s.type}`}
            title={s.type === 'tool_call' ? s.tool : s.type}
          />
        ))}
        {isRunning && !done && <div className="exec-seg exec-seg-pending" />}
      </div>
    </div>
  );
}

const CodeBlock = ({ children, className }) => {
  const [copied, setCopied] = useState(false);
  const lang = className?.replace('language-', '') || 'text';
  const copy = () => {
    navigator.clipboard.writeText(String(children));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-lang">{lang}</span>
        <button type="button" className="copy-btn" onClick={copy}><Icon name="copy" size={12} />{copied ? 'Copied!' : 'Copy'}</button>
      </div>
      <pre className="code-pre"><code className={`language-${lang}`}>{String(children).replace(/\n$/, '')}</code></pre>
    </div>
  );
};

const markdownComponents = {
  p: ({ children }) => <div className="md-block">{children}</div>,
  code: ({ inline, className, children, ...props }) => {
    const block = !inline && className && String(className).includes('language-');
    if (block) return <CodeBlock className={className}>{children}</CodeBlock>;
    return <code className={className || 'inline-code'} {...props}>{children}</code>;
  },
};

const MEDIA_EXT = {
  image: ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'],
  video: ['.mp4', '.webm', '.mov', '.mkv'],
  audio: ['.wav', '.mp3', '.m4a', '.ogg', '.flac'],
};

function normalizeOutputUrl(rawPath) {
  if (!rawPath || typeof rawPath !== 'string') return null;
  const cleaned = rawPath.trim().replace(/^["']|["']$/g, '').replace(/\\/g, '/');
  const idx = cleaned.toLowerCase().lastIndexOf('/outputs/');
  if (idx >= 0) return API + cleaned.slice(idx);
  if (cleaned.toLowerCase().startsWith('outputs/')) return API + '/' + cleaned;
  if (cleaned.toLowerCase().startsWith('/outputs/')) return API + cleaned;
  return null;
}

function mediaTypeFromPath(path) {
  const lower = (path || '').toLowerCase();
  if (MEDIA_EXT.image.some((ext) => lower.endsWith(ext))) return 'image';
  if (MEDIA_EXT.video.some((ext) => lower.endsWith(ext))) return 'video';
  if (MEDIA_EXT.audio.some((ext) => lower.endsWith(ext))) return 'audio';
  return null;
}

function collectMediaFromToolResult(result) {
  const text = typeof result === 'string' ? result : JSON.stringify(result || {});
  const candidates = [];
  try {
    const parsed = JSON.parse(text);
    ['image_path', 'video_path', 'audio_path', 'path', 'output_path'].forEach((key) => {
      if (typeof parsed?.[key] === 'string') candidates.push(parsed[key]);
    });
  } catch (_) {
    // Tool output is often plain text; regex pass below handles that.
  }

  const pathPattern = /(?:[A-Za-z]:[\\/][^"'\n\r]+?|(?:^|[\s"'`])outputs[\\/][^"'\s\n\r]+?\.(?:png|jpe?g|webp|gif|bmp|mp4|webm|mov|mkv|wav|mp3|m4a|ogg|flac))/gi;
  for (const match of text.matchAll(pathPattern)) {
    candidates.push((match[0] || '').trim());
  }

  const seen = new Set();
  return candidates
    .map((p) => ({ path: p, url: normalizeOutputUrl(p), type: mediaTypeFromPath(p) }))
    .filter((item) => item.url && item.type && !seen.has(item.url) && seen.add(item.url));
}

function MediaPreview({ result }) {
  const media = collectMediaFromToolResult(result);
  if (!media.length) return null;
  return (
    <div className="media-preview-list">
      {media.map((item) => (
        <div className="media-preview" key={item.url}>
          {item.type === 'image' && <img src={item.url} alt={item.path} />}
          {item.type === 'video' && <video src={item.url} controls preload="metadata" />}
          {item.type === 'audio' && <audio src={item.url} controls />}
          <div className="media-path">{item.path}</div>
        </div>
      ))}
    </div>
  );
}

function AttachmentPreview({ attachments = [] }) {
  if (!attachments.length) return null;
  return (
    <div className="attachment-list">
      {attachments.map((item) => {
        const url = item.url?.startsWith('http') ? item.url : API + item.url;
        const type = mediaTypeFromPath(item.filename || item.url || item.path);
        return (
          <a className="attachment-card" key={item.url || item.path} href={url} target="_blank" rel="noreferrer">
            {type === 'image' && <img src={url} alt={item.filename} />}
            {type === 'video' && <video src={url} controls preload="metadata" />}
            {type === 'audio' && <audio src={url} controls />}
            {!type && <span className="attachment-file-icon"><Icon name="file" size={18} /></span>}
            <span className="attachment-name">{item.filename || 'attachment'}</span>
            <span className="attachment-meta">{item.content_type || 'file'} · {formatBytes(item.size)}</span>
          </a>
        );
      })}
    </div>
  );
}

function formatBytes(size) {
  const n = Number(size || 0);
  if (!n) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = n;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function AgentStepsMessage({ msg, isStreaming }) {
  const steps = msg.steps || [];
  const finalStep = steps.find((s) => s.type === 'final_answer');
  const otherSteps = steps.filter((s) => s.type !== 'final_answer');
  const [timelineOpen, setTimelineOpen] = useState(true);

  return (
    <div className="msg msg-assistant">
      <div className="agent-avatar"><Icon name="agent" size={14} /></div>
      <div className="agent-steps-wrap">
        <ExecutionProgress steps={steps} isRunning={isStreaming && !finalStep} />

        {otherSteps.length > 0 && (
          <button type="button" className="tl-toggle" onClick={() => setTimelineOpen((o) => !o)}>
            <Icon name="activity" size={12} />
            {timelineOpen ? '收起' : '展开'}过程步骤（{otherSteps.length}）
            <span className={`tl-chevron-sm ${timelineOpen ? 'expanded' : ''}`}><Icon name="chevron" size={11} /></span>
          </button>
        )}

        {timelineOpen && otherSteps.length > 0 && (
          <div className="timeline">
            {otherSteps.map((step, i) => (
              <TimelineStep key={i} step={step} index={i} isLast={i === otherSteps.length - 1} />
            ))}
          </div>
        )}

        {finalStep && (
          <div className="final-answer-card">
            <div className="final-answer-label"><Icon name="zap" size={11} /> 回答</div>
            <div className="final-answer-content">
              <ReactMarkdown components={markdownComponents}>{finalStep.content}</ReactMarkdown>
            </div>
          </div>
        )}

        {isStreaming && !finalStep && (
          <div className="typing"><span /><span /><span /></div>
        )}
      </div>
    </div>
  );
}

const Message = ({ msg, isStreaming }) => {
  if (msg.role === 'user') {
    return (
      <div className="msg msg-user">
        <div className="msg-bubble">
          <div>{msg.content}</div>
          <AttachmentPreview attachments={msg.attachments || []} />
        </div>
      </div>
    );
  }

  if (msg.role === 'agent-steps') {
    return <AgentStepsMessage msg={msg} isStreaming={isStreaming} />;
  }

  return (
    <div className="msg msg-assistant">
      <div className="assistant-avatar">Q</div>
      <div className="msg-content">
        <ReactMarkdown components={markdownComponents}>{msg.content}</ReactMarkdown>
      </div>
    </div>
  );
};

function ToolPanel({ onInject }) {
  const [httpUrl, setHttpUrl] = useState('');
  const [httpMethod, setHttpMethod] = useState('GET');
  const [dbQuery, setDbQuery] = useState('');
  const [dbPath, setDbPath] = useState('');

  const quickTools = [
    { label: '搜索 AI 新闻', msg: '搜索最新 AI 新闻', icon: 'search' },
    { label: '本地搜索+抓取', msg: '用本地搜索查最新 AI 新闻并抓取正文摘要', icon: 'search' },
    { label: '抓取网页', msg: '抓取这个网页正文：https://www.reuters.com/technology/artificial-intelligence/', icon: 'globe' },
    { label: '列桌面文件', msg: '列出我的桌面文件', icon: 'file' },
    { label: '设备画像', msg: '给我看设备画像', icon: 'activity' },
    { label: '今日总结', msg: '总结我今天在做什么', icon: 'cpu' },
    { label: '进化画像', msg: '展示自进化画像', icon: 'zap' },
    { label: '多模型编排', msg: '用编排做一个复杂方案对比', icon: 'layers' },
  ];

  return (
    <div className="tool-panel">
      <div className="tool-panel-title">快捷工具</div>

      <div className="quick-tools">
        {quickTools.map((t) => (
          <button type="button" key={t.label} className="quick-tool-btn" onClick={() => onInject(t.msg)}>
            <Icon name={t.icon} size={12} />
            {t.label}
          </button>
        ))}
      </div>

      <div className="tool-divider">HTTP 请求</div>
      <div className="tool-form">
        <div className="tool-row">
          <select value={httpMethod} onChange={(e) => setHttpMethod(e.target.value)} className="tool-select-sm">
            {['GET', 'POST', 'PUT', 'DELETE'].map((m) => <option key={m}>{m}</option>)}
          </select>
          <input
            className="tool-input"
            placeholder="https://api.example.com/v1/..."
            value={httpUrl}
            onChange={(e) => setHttpUrl(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="tool-run-btn"
          disabled={!httpUrl.trim()}
          onClick={() => {
            onInject(`用 http_request 工具 ${httpMethod} 请求 ${httpUrl.trim()}`);
            setHttpUrl('');
          }}
        >
          发送请求
        </button>
      </div>

      <div className="tool-divider">查询数据库</div>
      <div className="tool-form">
        <input
          className="tool-input"
          placeholder="数据库路径（.db 文件）"
          value={dbPath}
          onChange={(e) => setDbPath(e.target.value)}
        />
        <textarea
          className="tool-textarea"
          placeholder="SELECT * FROM ..."
          value={dbQuery}
          onChange={(e) => setDbQuery(e.target.value)}
          rows={3}
        />
        <button
          type="button"
          className="tool-run-btn"
          disabled={!dbQuery.trim()}
          onClick={() => {
            const p = dbPath.trim() || 'backend/memory.db';
            onInject(`对数据库 ${p} 执行 SQL 查询：${dbQuery.trim()}`);
            setDbQuery('');
          }}
        >
          执行查询
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('chat');
  const [panel, setPanel] = useState('chat');
  const [model, setModel] = useState(LOCKED_MODEL_ID);
  const [modelLabel, setModelLabel] = useState(LOCKED_MODEL_LABEL);
  const [streamingMsg, setStreamingMsg] = useState('');
  const [dash, setDash] = useState(null);
  const [dashLoading, setDashLoading] = useState(false);
  const [reportText, setReportText] = useState('');
  const [memoryDash, setMemoryDash] = useState(null);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [showToolPanel, setShowToolPanel] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const [operatorDash, setOperatorDash] = useState(null);
  const [logBundle, setLogBundle] = useState(null);
  const [skillsCatalog, setSkillsCatalog] = useState(null);
  const [schedulerJobs, setSchedulerJobs] = useState([]);
  const [agentToolsInfo, setAgentToolsInfo] = useState(null);
  const [alignment, setAlignment] = useState(null);
  const [pendingSkill, setPendingSkill] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [schedForm, setSchedForm] = useState({ name: '定时任务', message: '', interval_sec: 3600, task_kind: 'agent' });
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  /** 与 activeSession 同步；发送时优先读 ref，避免 setState 滞后导致每条请求 session_id 不一致 */
  const sessionIdRef = useRef(null);

  useEffect(() => {
    sessionIdRef.current = activeSession;
  }, [activeSession]);

  const loadSkillsCatalog = async () => {
    try {
      const r = await fetch(API + '/meta/skills');
      if (r.ok) setSkillsCatalog(await r.json());
    } catch (_) {
      setSkillsCatalog(null);
    }
  };

  const loadSchedulerJobs = async () => {
    try {
      const r = await fetch(API + '/scheduler/jobs');
      if (r.ok) {
        const j = await r.json();
        setSchedulerJobs(j.jobs || []);
      }
    } catch (_) {
      setSchedulerJobs([]);
    }
  };

  const loadAgentTools = async () => {
    try {
      const r = await fetch(API + '/agent/tools');
      if (r.ok) setAgentToolsInfo(await r.json());
    } catch (_) {
      setAgentToolsInfo(null);
    }
  };

  const loadAlignment = async () => {
    try {
      const r = await fetch(API + '/meta/alignment');
      if (r.ok) setAlignment(await r.json());
    } catch (_) {
      setAlignment(null);
    }
  };

  const loadOperatorDashboard = async () => {
    try {
      const r = await fetch(API + '/meta/operator-dashboard');
      if (r.ok) {
        const j = await r.json();
        setOperatorDash(j);
        return j;
      }
    } catch (_) {
      // ignore
    }
    setOperatorDash(null);
    return null;
  };

  const loadLogs = async () => {
    try {
      const r = await fetch(API + '/meta/logs?lines=80');
      if (r.ok) {
        const j = await r.json();
        setLogBundle(j);
        return j;
      }
    } catch (_) {
      // ignore
    }
    setLogBundle(null);
    return null;
  };

  const refreshOperatorSurfaces = async (healthOptions) => {
    await Promise.all([
      loadSystemHealth(healthOptions),
      loadOperatorDashboard(),
      loadLogs(),
    ]);
  };

  const runSlashCommand = (raw) => {
    const line = raw.trim();
    const parts = line.split(/\s+/);
    const cmd = (parts[0] || '').toLowerCase();
    const arg = parts.slice(1).join(' ').trim();

    if (cmd === '/doctor' || cmd === '/system') {
      loadSystemHealth();
      setPanel('system');
      return true;
    }
    if (cmd === '/dashboard' || cmd === '/home') {
      refreshOperatorSurfaces();
      setPanel('chat');
      return true;
    }
    if (cmd === '/habit') {
      runHabitCheckNow();
      setPanel('system');
      return true;
    }
    if (cmd === '/skills') {
      loadSkillsCatalog();
      setPanel('skills');
      return true;
    }
    if (cmd === '/skill' && arg) {
      setPendingSkill(arg.split(/\s+/)[0]);
      setPanel('chat');
      setMessages((prev) => [...prev, { role: 'assistant', content: `下一条消息将挂载技能「${arg}」` }]);
      return true;
    }
    if (cmd === '/scheduler') {
      loadSchedulerJobs();
      setPanel('scheduler');
      return true;
    }
    if (cmd === '/mode' && arg) {
      const m = arg.toLowerCase();
      if (m === 'agent' || m === 'chat') {
        setMode(m);
        setPanel('chat');
        return true;
      }
    }
    if (cmd === '/model') {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `当前后端模型为 ${modelLabel}（${model || '由后端默认配置决定'}）。`,
      }]);
      return true;
    }
    if (cmd === '/tools') {
      loadAgentTools().then(() => setPanel('system'));
      return true;
    }
    if (cmd === '/help') {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '斜杠命令：/dashboard /doctor /habit /skills /skill <id> /scheduler /mode chat|agent /tools /help /model',
      }]);
      return true;
    }
    return false;
  };

  const loadSystemHealth = async (options = {}) => {
    const retries = Number.isInteger(options.retries) ? options.retries : 0;
    const retryDelayMs = Number.isInteger(options.retryDelayMs) ? options.retryDelayMs : 500;
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      try {
        const [dr, mr, hr] = await Promise.all([
          fetch(API + '/meta/doctor'),
          fetch(API + '/meta/models'),
          fetch(API + '/meta/habit'),
        ]);
        const doctor = dr.ok ? await dr.json() : null;
        const modelsJson = mr.ok ? await mr.json() : null;
        const habit = hr.ok ? await hr.json() : null;
        const firstModel = (modelsJson?.models || [])
          .map((m) => (typeof m === 'string' ? m : m?.id || m?.model || m?.name))
          .filter(Boolean)[0];
        if (firstModel) {
          setModel(firstModel);
          setModelLabel(labelForModel(firstModel));
        }
        setSystemHealth({ doctor, modelsJson, habit, at: Date.now() });
        return { doctor, modelsJson, habit };
      } catch (_) {
        if (attempt < retries) {
          await wait(retryDelayMs);
          continue;
        }
        setSystemHealth({ doctor: null, modelsJson: null, habit: null, backendDown: true, at: Date.now() });
        return null;
      }
    }
  };

  const runHabitCheckNow = async () => {
    try {
      const r = await fetch(API + '/meta/habit/run', { method: 'POST' });
      const j = r.ok ? await r.json() : null;
      await refreshOperatorSurfaces();
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: j?.summary
            ? `习惯体检完成。\n\n${j.summary}`
            : '习惯体检请求失败，请确认后端已启动。',
        },
      ]);
    } catch (_) {
      setMessages((prev) => [...prev, { role: 'assistant', content: '习惯体检请求失败。' }]);
    }
  };

  useEffect(() => {
    loadSessions();
    (async () => {
      let prefs = {};
      let cfg = {};
      try {
        const [health] = await Promise.all([
          loadSystemHealth({ retries: 12, retryDelayMs: 500 }),
          loadOperatorDashboard(),
          loadLogs(),
        ]);
        const [pr, cr] = await Promise.all([
          fetch(API + '/chat/preferences'),
          fetch(API + '/agent/config'),
        ]);
        if (pr.ok) prefs = await pr.json();
        if (cr.ok) cfg = await cr.json();

        const backendModel = (health?.modelsJson?.models || [])
          .map((m) => (typeof m === 'string' ? m : m?.id || m?.model || m?.name))
          .filter(Boolean)[0] || LOCKED_MODEL_ID;
        if ((prefs.default_model || cfg.default_model || '').trim() !== backendModel) {
          fetch(API + '/chat/preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'default_model', value: backendModel }),
          }).catch(() => {});
        }
      } catch (e) { /* ignore */ }
    })();
    const t = setInterval(() => {
      refreshOperatorSurfaces();
    }, 30000);
    return () => clearInterval(t);
  }, []);

  const loadDashboard = async () => {
    setDashLoading(true);
    try {
      const r = await fetch(API + '/observe/dashboard');
      setDash(await r.json());
    } catch (e) {
      setDash(null);
    }
    setDashLoading(false);
  };

  const loadMemoryDashboard = async () => {
    setMemoryLoading(true);
    try {
      const r = await fetch(API + '/chat/memories/dashboard');
      setMemoryDash(await r.json());
    } catch (e) {
      setMemoryDash(null);
    }
    setMemoryLoading(false);
  };

  useEffect(() => {
    if (panel === 'profile') {
      loadDashboard();
      loadMemoryDashboard();
    }
    if (panel === 'skills') loadSkillsCatalog();
    if (panel === 'scheduler') loadSchedulerJobs();
    if (panel === 'system') {
      loadSystemHealth();
      loadAgentTools();
      loadAlignment();
    }
  }, [panel]);

  useEffect(() => {
    if (panel === 'chat' && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMsg, panel, loading]);

  const loadSessions = async () => {
    try {
      const r = await fetch(API + '/chat/sessions');
      setSessions(await r.json());
    } catch (e) { /* ignore */ }
  };

  const newSession = () => {
    sessionIdRef.current = null;
    setActiveSession(null);
    setMessages([]);
    setStreamingMsg('');
    setPanel('chat');
    setShowToolPanel(false);
    refreshOperatorSurfaces();
  };

  const loadSession = async (id) => {
    sessionIdRef.current = id;
    setActiveSession(id);
    setStreamingMsg('');
    try {
      const r = await fetch(API + '/chat/sessions/' + id + '/messages');
      setMessages(await r.json());
    } catch (e) {
      setMessages([]);
    }
  };

  const deleteSession = async (id, e) => {
    e.stopPropagation();
    await fetch(API + '/chat/sessions/' + id, { method: 'DELETE' });
    if (activeSession === id) {
      sessionIdRef.current = null;
      setActiveSession(null);
      setMessages([]);
    }
    loadSessions();
  };

  const injectMessage = (text) => {
    setInput(text);
    setMode('agent');
    setPanel('chat');
    textareaRef.current?.focus();
  };

  const addAttachments = async (files) => {
    const picked = Array.from(files || []);
    if (!picked.length) return;
    setUploading(true);
    try {
      const uploaded = [];
      for (const file of picked) {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(API + '/upload_file', { method: 'POST', body: form });
        if (!res.ok) throw new Error(await res.text());
        uploaded.push(await res.json());
      }
      setAttachments((prev) => [...prev, ...uploaded]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'assistant', content: '附件上传失败：' + (e.message || e) }]);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (idx) => {
    setAttachments((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleComposerPaste = (e) => {
    const files = extractClipboardFiles(e.clipboardData);
    if (!files.length || loading || uploading) return;
    const pastedText = e.clipboardData?.getData?.('text/plain') || '';
    if (!pastedText) e.preventDefault();
    void addAttachments(files);
  };

  const sendMessage = async () => {
    if ((!input.trim() && !attachments.length) || loading || uploading) return;
    const text = input.trim();
    const outgoingAttachments = attachments;
    setInput('');
    setAttachments([]);
    if (text.startsWith('/')) {
      if (runSlashCommand(text)) return;
    }
    let msgText = text;
    if (!msgText && outgoingAttachments.length) msgText = '请查看我上传的附件。';
    if (pendingSkill) {
      msgText = `[skill:${pendingSkill}] ${text}`;
      setPendingSkill(null);
    }
    if (outgoingAttachments.length) {
      const attachmentContext = outgoingAttachments
        .map((a, i) => {
          const url = a.url?.startsWith('http') ? a.url : API + a.url;
          return `${i + 1}. ${a.filename} | ${a.content_type} | ${formatBytes(a.size)} | url=${url} | local_path=${a.path}`;
        })
        .join('\n');
      msgText += `\n\n[上传附件]\n${attachmentContext}`;
    }
    let sid = sessionIdRef.current || activeSession;
    if (!sid) {
      sid = uuidv4();
      sessionIdRef.current = sid;
      setActiveSession(sid);
    } else if (!activeSession) {
      setActiveSession(sid);
    }
    setLoading(true);
    setMessages((prev) => [...prev, { role: 'user', content: text || '请查看我上传的附件。', attachments: outgoingAttachments }]);
    if (mode === 'agent') await sendAgent(msgText, sid);
    else await sendChat(msgText, sid);
    loadSessions();
    setLoading(false);
  };

  const sendChat = async (text, sid) => {
    setStreamingMsg('');
    let sseBuf = '';
    let gotDone = false;
    try {
      const res = await fetch(API + '/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sid, message: text, model, stream: true }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`HTTP ${res.status}: ${t.slice(0, 240)}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = '';
      const flushLines = (flushAll) => {
        const parts = sseBuf.split('\n');
        sseBuf = flushAll ? '' : (parts.pop() || '');
        for (const line of parts) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              full += data.content;
              setStreamingMsg(full);
            }
            if (data.done) {
              gotDone = true;
              if (data.error) {
                const hint = data.error.includes('Ollama') || data.error.includes('Connect')
                  ? '请先启动 Ollama（托盘图标或 ollama serve），再点顶部「重新检测」。'
                  : '';
                full += (full ? '\n\n' : '') + '[后端: ' + data.error + ']' + (hint ? '\n\n' + hint : '');
              }
              if (!full.trim()) full = '（模型无回复，请检查 Ollama 与所选模型是否可用）';
              setMessages((prev) => [...prev, { role: 'assistant', content: full }]);
              setStreamingMsg('');
              refreshOperatorSurfaces();
            }
          } catch (_) { /* ignore */ }
        }
      };
      while (true) {
        const { done, value } = await reader.read();
        if (value) {
          sseBuf += decoder.decode(value, { stream: true });
          flushLines(false);
          if (gotDone) return;
        }
        if (done) {
          sseBuf += decoder.decode();
          flushLines(true);
          if (!gotDone) {
            full += (full ? '\n\n' : '') + '[连接在流式传输完成前断开]';
            setMessages((prev) => [...prev, { role: 'assistant', content: full }]);
            setStreamingMsg('');
          }
          return;
        }
      }
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]);
      setStreamingMsg('');
      refreshOperatorSurfaces();
    }
  };

  const sendAgent = async (text) => {
    const steps = [];
    setMessages((prev) => [...prev, { role: 'agent-steps', steps: [], streaming: true }]);
    try {
      const res = await fetch(API + '/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, model }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`HTTP ${res.status}: ${t.slice(0, 240)}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let sseBuf = '';
      const flushLines = (flushAll) => {
        const parts = sseBuf.split('\n');
        sseBuf = flushAll ? '' : (parts.pop() || '');
        for (const line of parts) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (!data.done) {
              steps.push(data);
              setMessages((prev) => {
                const n = [...prev];
                n[n.length - 1] = { role: 'agent-steps', steps: [...steps], streaming: true };
                return n;
              });
            }
          } catch (_) { /* ignore */ }
        }
      };
      while (true) {
        const { done, value } = await reader.read();
        if (value) {
          sseBuf += decoder.decode(value, { stream: true });
          flushLines(false);
        }
        if (done) {
          sseBuf += decoder.decode();
          flushLines(true);
          break;
        }
      }
    } catch (e) {
      steps.push({ type: 'final_answer', content: 'Error: ' + e.message });
    }
    setMessages((prev) => {
      const n = [...prev];
      n[n.length - 1] = { role: 'agent-steps', steps: [...steps], streaming: false };
      return n;
    });
    refreshOperatorSurfaces();
  };

  const placeholderForMode = () =>
    mode === 'agent'
      ? '用自然语言说任务，Agent 会自动选工具执行…'
      : '聊天模式：问答与建议（不会自动改文件/跑命令）。要搜网页、列目录请切到 Agent…';

  const ollamaCheck = systemHealth?.doctor?.checks?.find((c) => c.name === 'ollama_reachable');
  const ollamaOk = ollamaCheck ? ollamaCheck.status === 'ok' : null;
  const healthBanner = (() => {
    if (systemHealth?.backendDown) {
      return { tone: 'err', text: '后端未连接（端口 8000）。请重新打开 BT（黑光）或运行 START_APP.bat。' };
    }
    if (ollamaOk === false) {
      return {
        tone: 'warn',
        text: `Ollama 未就绪：${ollamaCheck?.detail || '无法连接 11434'}。模型不会回复 — 请运行 ollama serve 或重启应用。`,
      };
    }
    if (systemHealth?.modelsJson && systemHealth.modelsJson.ok === false) {
      return { tone: 'warn', text: `模型列表拉取失败：${systemHealth.modelsJson.error || '未知错误'}` };
    }
    return null;
  })();
  const agentBusy = loading && mode === 'agent';

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <div className="titlebar">
        <div className="titlebar-drag">
          <BrandLogo className="titlebar-logo" size={22} alt="" />
          <span className="app-name">{APP_NAME}</span>
          <span className="app-tag">{APP_TAGLINE}</span>
        </div>
        <div className="titlebar-controls">
          <button type="button" onClick={() => window.electronAPI?.minimizeWindow()}><Icon name="minimize" size={12} /></button>
          <button type="button" onClick={() => window.electronAPI?.maximizeWindow()}><Icon name="maximize" size={12} /></button>
          <button type="button" className="close-btn" onClick={() => window.electronAPI?.closeWindow()}><Icon name="close" size={12} /></button>
        </div>
      </div>

      <div className="layout">
        <div className="sidebar">
          <button
            type="button"
            className={`sidebar-brand sidebar-brand-button${agentBusy ? ' is-thinking' : ''}`}
            onClick={() => {
              setPanel('chat');
              setShowToolPanel(false);
              refreshOperatorSurfaces();
            }}
          >
            <div className="sidebar-brand-frame">
              <BrandHero className="sidebar-brand-hero" alt={APP_NAME} />
              <div className="sidebar-brand-plate">
                <strong className="sidebar-brand-name">{APP_NAME}</strong>
                <span className="sidebar-brand-tag">
                  {agentBusy ? 'Agent 推理中，正在处理任务…' : APP_TAGLINE}
                </span>
              </div>
              <span className="sidebar-brand-busy">{agentBusy ? '推理中' : '待命'}</span>
            </div>
          </button>
          <button type="button" className="new-chat-btn" onClick={newSession}><Icon name="plus" size={14} /> New Chat</button>
          <div className="mode-toggle">
            <button
              type="button"
              className={mode === 'chat' && panel === 'chat' ? 'active' : ''}
              onClick={() => {
                setMode('chat');
                setPanel('chat');
                setShowToolPanel(false);
              }}
            >
              <Icon name="chat" size={13} /> 聊天
            </button>
            <button
              type="button"
              className={mode === 'agent' && panel === 'chat' ? 'active' : ''}
              onClick={() => {
                setMode('agent');
                setPanel('chat');
              }}
            >
              <Icon name="agent" size={13} /> Agent
            </button>
          </div>

          {mode === 'agent' && (
            <button
              type="button"
              className={'sidebar-sub-btn' + (showToolPanel ? ' active' : '')}
              onClick={() => setShowToolPanel((v) => !v)}
            >
              <Icon name="tool" size={12} /> 工具面板
            </button>
          )}

          <button type="button" className={'sidebar-sub-btn' + (panel === 'system' ? ' active' : '')} onClick={() => setPanel('system')}>
            <Icon name="cpu" size={12} /> 系统
          </button>
          <button type="button" className={'sidebar-sub-btn' + (panel === 'skills' ? ' active' : '')} onClick={() => setPanel('skills')}>
            <Icon name="layers" size={12} /> 技能
          </button>
          <button type="button" className={'sidebar-sub-btn' + (panel === 'scheduler' ? ' active' : '')} onClick={() => setPanel('scheduler')}>
            <Icon name="zap" size={12} /> 定时
          </button>
          <button type="button" className={'profile-entry' + (panel === 'profile' ? ' active' : '')} onClick={() => setPanel('profile')}>
            设备画像
          </button>

          <div className="model-select model-locked" title={model || 'backend default'}>
            <span className="model-locked-label">{modelLabel}</span>
          </div>

          <div className="sessions">
            {sessions.map((s) => (
              <div key={s.id} className={'session-item' + (activeSession === s.id ? ' active' : '')} onClick={() => loadSession(s.id)}>
                <span className="session-title">{s.title || 'Untitled'}</span>
                <button type="button" className="session-delete" onClick={(e) => deleteSession(s.id, e)}><Icon name="trash" size={12} /></button>
              </div>
            ))}
          </div>
        </div>

        {showToolPanel && mode === 'agent' && panel === 'chat' && (
          <ToolPanel onInject={injectMessage} />
        )}

        <div className="main">
          {healthBanner && (
            <div className={`system-banner system-banner-${healthBanner.tone}`} role="status">
              <span>{healthBanner.text}</span>
              <button type="button" className="system-banner-btn" onClick={loadSystemHealth}>重新检测</button>
            </div>
          )}
          {panel === 'system' ? (
            <SystemPanel
              systemHealth={systemHealth}
              agentToolsInfo={agentToolsInfo}
              alignment={alignment}
              onRefresh={() => { loadSystemHealth(); loadAgentTools(); loadAlignment(); }}
              onHabitCheck={runHabitCheckNow}
            />
          ) : panel === 'skills' ? (
            <SkillsPanel
              skillsCatalog={skillsCatalog}
              onRefresh={loadSkillsCatalog}
              onPick={(sk) => {
                setPendingSkill(sk.id);
                setPanel('chat');
                setMessages((prev) => [...prev, { role: 'assistant', content: `已选择技能「${sk.title}」，下一条消息将挂载。` }]);
              }}
            />
          ) : panel === 'scheduler' ? (
            <SchedulerPanel
              jobs={schedulerJobs}
              form={schedForm}
              setForm={setSchedForm}
              onRefresh={loadSchedulerJobs}
              onCreate={async () => {
                await fetch(API + '/scheduler/jobs', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ ...schedForm, model }),
                });
                loadSchedulerJobs();
              }}
              onRun={async (id) => { await fetch(API + `/scheduler/jobs/${id}/run`, { method: 'POST' }); }}
            />
          ) : panel === 'profile' ? (
            <div className="profile-panel">
              <div className="profile-header">
                <h2>设备画像</h2>
                <div className="profile-actions">
                  <button type="button" className="profile-btn" disabled={dashLoading} onClick={loadDashboard}>{dashLoading ? '加载中…' : '刷新数据'}</button>
                  <button type="button" className="profile-btn" disabled={memoryLoading} onClick={loadMemoryDashboard}>{memoryLoading ? '记忆加载中…' : '刷新记忆'}</button>
                  <button type="button" className="profile-btn" onClick={async () => { await fetch(API + '/observe/sample', { method: 'POST' }); loadDashboard(); loadMemoryDashboard(); }}>立即采集</button>
                  <button type="button" className="profile-btn" onClick={async () => { const r = await fetch(API + '/observe/report/today', { method: 'POST' }); const j = await r.json(); setReportText(j.summary || ''); }}>生成今日简报</button>
                  <button type="button" className="profile-btn" onClick={async () => { const r = await fetch(API + '/observe/report/latest'); const j = await r.json(); setReportText(j.summary || j.hint || ''); }}>加载最新简报</button>
                  <button type="button" className="profile-btn" onClick={async () => { if (!window.confirm('清空所有行为采样记录？')) return; await fetch(API + '/observe/samples', { method: 'DELETE' }); loadDashboard(); }}>清空采样</button>
                </div>
              </div>
              {!dash ? (
                <p className="profile-muted">无法连接后端或未加载。请确认已启动 FastAPI（端口 8000）。</p>
              ) : (
                <>
                  <div className="profile-card">
                    <h3>采集状态</h3>
                    <p>近24h 样本数：<strong>{dash.status?.samples_last_24h ?? 0}</strong></p>
                    <p>后台采集：{dash.status?.background_enabled ? '已开启（约每 ' + dash.status?.interval_sec_default + ' 秒）' : '已关闭'}</p>
                  </div>
                  <div className="profile-card">
                    <h3>归纳洞察</h3>
                    <ul className="profile-bullets">{(dash.insights || []).map((t, i) => <li key={i}>{t}</li>)}</ul>
                  </div>
                  <div className="profile-grid">
                    <div className="profile-card">
                      <h3>常见前台标题（7天）</h3>
                      <ol className="profile-list">{(dash.profile_7d?.top_titles || []).slice(0, 12).map((x, i) => <li key={i}><span className="profile-count">{x.count}</span>{x.title}</li>)}</ol>
                    </div>
                    <div className="profile-card">
                      <h3>常见进程（7天）</h3>
                      <ol className="profile-list">{(dash.profile_7d?.top_processes || []).slice(0, 12).map((x, i) => <li key={i}><span className="profile-count">{x.count}</span>{x.name}</li>)}</ol>
                    </div>
                  </div>
                  <div className="profile-card">
                    <h3>桌面近期文件</h3>
                    <ul className="profile-files">{(dash.desktop_recent_files || []).map((f, i) => <li key={i} title={f.path}>{f.name}</li>)}</ul>
                  </div>
                  <div className="profile-card">
                    <h3>记忆与知识树</h3>
                    {!memoryDash ? <p className="profile-muted">暂时还没读到记忆数据。</p> : (
                      <>
                        <p>长期记忆：<strong>{memoryDash.memory_count ?? 0}</strong> · 知识树节点：<strong>{memoryDash.knowledge_tree?.node_count ?? 0}</strong></p>
                        <p>知识库位置：<span className="profile-path">{memoryDash.vault_dir || '未生成'}</span></p>
                        <div className="profile-card profile-inner-card">
                          <h3>当前记忆摘要</h3>
                          <ul className="profile-bullets">
                            {(memoryDash.summaries || []).slice(0, 4).map((item, i) => (
                              <li key={i}>
                                <strong>{item.title}</strong>
                                <div className="memory-summary-text">{item.summary}</div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </>
                    )}
                  </div>
                  {reportText && <div className="profile-card profile-report"><h3>简报</h3><pre>{reportText}</pre></div>}
                </>
              )}
            </div>
          ) : (
            <>
              <div className="messages">
                {messages.length === 0 && (
                  <DashboardPanel
                    operatorDash={operatorDash}
                    logBundle={logBundle}
                    onRefresh={refreshOperatorSurfaces}
                    onOpenChat={() => textareaRef.current?.focus()}
                    onHabitCheck={runHabitCheckNow}
                  />
                )}

                {messages.map((msg, i) => (
                  <Message
                    key={i}
                    msg={msg}
                    isStreaming={loading && i === messages.length - 1 && msg.role === 'agent-steps'}
                  />
                ))}

                {streamingMsg && (
                  <div className="msg msg-assistant">
                    <div className="assistant-avatar">Q</div>
                    <div className="msg-content streaming">
                      <ReactMarkdown components={markdownComponents}>{streamingMsg}</ReactMarkdown>
                      <span className="cursor" />
                    </div>
                  </div>
                )}
                {loading && !streamingMsg && mode === 'chat' && (
                  <div className="msg msg-assistant">
                    <div className="assistant-avatar">Q</div>
                    <div className="typing"><span /><span /><span /></div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              <div className="input-area">
                {attachments.length > 0 && (
                  <div className="pending-attachments">
                    {attachments.map((item, idx) => {
                      const url = item.url?.startsWith('http') ? item.url : API + item.url;
                      const type = mediaTypeFromPath(item.filename || item.url || item.path);
                      return (
                        <div className="pending-attachment" key={item.url || item.path}>
                          {type === 'image' ? <img src={url} alt="" /> : <Icon name="file" size={14} />}
                          <span title={item.filename}>{item.filename}</span>
                          <button type="button" onClick={() => removeAttachment(idx)}><Icon name="close" size={11} /></button>
                        </div>
                      );
                    })}
                  </div>
                )}
                <div className="input-box">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="file-input-hidden"
                    onChange={(e) => addAttachments(e.target.files)}
                  />
                  <button
                    type="button"
                    className="attach-btn"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={loading || uploading}
                    title="添加图片、视频、音频或文件"
                  >
                    <Icon name="paperclip" size={16} />
                  </button>
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onPaste={handleComposerPaste}
                    onKeyDown={onKey}
                    placeholder={placeholderForMode()}
                    rows={1}
                    style={{ height: Math.min(120, 20 + input.split('\n').length * 20) + 'px' }}
                  />
                  <button type="button" className="send-btn" onClick={sendMessage} disabled={(!input.trim() && !attachments.length) || loading || uploading}>
                    <Icon name="send" size={16} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

