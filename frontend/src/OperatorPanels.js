import React from 'react';
import { filterModelsForUi } from './modelCatalog';

function formatTime(value) {
  if (!value) return '暂无';
  const n = typeof value === 'number' ? value * 1000 : Date.parse(value);
  if (!Number.isFinite(n)) return '暂无';
  return new Date(n).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatusPill({ ok, label }) {
  return <span className={`dash-pill ${ok ? 'ok' : 'fail'}`}>{label}</span>;
}

function LogCard({ item }) {
  const lines = item?.lines || [];
  return (
    <div className="dash-log-card">
      <div className="dash-log-head">
        <div>
          <strong>{item?.name || 'log'}</strong>
          <span>{item?.exists ? `${(item.size / 1024).toFixed(1)} KB` : '未生成'}</span>
        </div>
        <span>{formatTime(item?.updated_at)}</span>
      </div>
      <pre className="dash-log-pre">{lines.length ? lines.join('\n') : '暂无日志输出'}</pre>
    </div>
  );
}

export function DashboardPanel({
  operatorDash,
  logBundle,
  onRefresh,
  onOpenChat,
  onHabitCheck,
}) {
  const [healthExpanded, setHealthExpanded] = React.useState(false);
  const doctor = operatorDash?.doctor;
  const habit = operatorDash?.habit;
  const models = filterModelsForUi(operatorDash?.models?.models || []);
  const recentReviews = operatorDash?.workflow?.recent_reviews || [];
  const failures = operatorDash?.failures || [];
  const logs = logBundle?.logs || [];
  const checks = doctor?.checks || [];
  const failChecks = checks.filter((c) => c.status === 'fail');
  const skipChecks = checks.filter((c) => c.status === 'skip');

  return (
    <div className="profile-panel dashboard-panel">
      <div className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="dashboard-kicker">Operator Dashboard</p>
          <h1>本地 Agent 指挥台</h1>
          <p className="dashboard-hero-text">
            顶部四颗灯表示：后端自检、习惯体检、模型是否就绪、工具是否加载。红条表示仍有<strong>硬性</strong>失败项；点下方「展开自检」可看全部明细（含可选依赖）。
          </p>
          <div className="dashboard-hero-actions">
            <button type="button" className="profile-btn dashboard-primary-btn" onClick={onRefresh}>立即刷新</button>
            <button type="button" className="profile-btn" onClick={onOpenChat}>进入对话</button>
            <button type="button" className="profile-btn" onClick={onHabitCheck}>立即体检</button>
          </div>
        </div>
        <div className="dashboard-hero-metrics">
          <div className="dash-stat-card">
            <span>模型状态</span>
            <strong>{models.length || 0}</strong>
            <small>{models[0]?.id || '未发现模型'}</small>
          </div>
          <div className="dash-stat-card">
            <span>后端健康</span>
            <strong>{doctor?.ok ? '正常' : '待修'}</strong>
            <small>{doctor?.ok ? '核心项通过' : `${doctor?.failed_count || 0} 项未通过`}</small>
          </div>
          <div className="dash-stat-card">
            <span>工具数</span>
            <strong>{operatorDash?.agent_tools?.count || 0}</strong>
            <small>已注册工具</small>
          </div>
          <div className="dash-stat-card">
            <span>最近任务</span>
            <strong>{operatorDash?.workflow?.review_count || 0}</strong>
            <small>{operatorDash?.chat?.session_count || 0} 个会话</small>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="profile-card dashboard-major-card">
          <div className="dash-card-head">
            <h3>运行态</h3>
            <span>最近刷新 {formatTime(operatorDash?.generated_at)}</span>
          </div>
          <div className="dash-pill-row">
            <StatusPill ok={doctor?.ok} label={doctor?.ok ? '后端正常' : `后端待修 (${doctor?.failed_count || failChecks.length})`} />
            <StatusPill ok={habit?.enabled !== false} label={habit?.enabled !== false ? '习惯体检开' : '习惯体检关'} />
            <StatusPill ok={models.length > 0} label={models.length > 0 ? '模型就绪' : '无模型'} />
            <StatusPill ok={(operatorDash?.agent_tools?.count || 0) > 0} label="工具已加载" />
          </div>
          {!doctor?.ok && failChecks.length > 0 && (
            <p className="dash-fail-hint profile-muted">
              未通过：{failChecks.map((c) => c.name).join('、')}。点「展开自检明细」看原因。
            </p>
          )}
          {doctor?.ok && skipChecks.length > 0 && (
            <p className="dash-fail-hint profile-muted">
              有 {skipChecks.length} 项为可选依赖（已跳过），不影响对话与 Agent 核心。
            </p>
          )}
          <button
            type="button"
            className="profile-btn dash-expand-btn"
            onClick={() => setHealthExpanded((e) => !e)}
          >
            {healthExpanded ? '收起自检明细' : '展开自检明细'}
            {checks.length ? `（共 ${checks.length} 项）` : ''}
          </button>
          {healthExpanded && (
            <div className="dash-health-grid">
              {checks.map((check) => (
                <div key={check.name} className={`dash-health-item ${check.status}`}>
                  <div>
                    <strong>{check.name}</strong>
                    <p>{check.detail || '正常'}</p>
                  </div>
                  <span>{check.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="profile-card">
          <div className="dash-card-head">
            <h3>习惯体检</h3>
            <span>{habit?.enabled ? '自动运行中' : '未启用'}</span>
          </div>
          <p className="dash-summary-line">本地时段：{(habit?.check_hours_local || []).join(':00、')}:00</p>
          <p className="dash-summary-line">
            上次执行：{habit?.last_run ? `${habit.last_run.phase} · ${habit.last_run.doctor_ok ? '通过' : `${habit.last_run.doctor_failed} 项未通过`}` : '暂无'}
          </p>
          <p className="dash-summary-line">learned 技能：{habit?.learned_skill_file || '尚未生成'}</p>
        </div>

        <div className="profile-card">
          <div className="dash-card-head">
            <h3>模型与记忆</h3>
            <span>{operatorDash?.memory?.memory_count || 0} 条记忆</span>
          </div>
          <ul className="profile-bullets">
            {models.slice(0, 6).map((model) => (
              <li key={model.id}>{model.id}</li>
            ))}
          </ul>
          <p className="dash-summary-line">
            知识树节点：{operatorDash?.memory?.knowledge_tree?.node_count || 0}
          </p>
          <p className="dash-summary-line">知识库：{operatorDash?.memory?.vault_dir || '未生成'}</p>
        </div>

        <div className="profile-card">
          <div className="dash-card-head">
            <h3>近期任务</h3>
            <span>{recentReviews.length} 条</span>
          </div>
          <div className="dash-review-list">
            {recentReviews.slice(0, 8).map((item, index) => (
              <div key={`${item.created_at}-${index}`} className={`dash-review-item ${item.status}`}>
                <div className="dash-review-meta">
                  <strong>{item.tool_name || item.task_type || 'task'}</strong>
                  <span>{formatTime(item.created_at)}</span>
                </div>
                <p>{item.task_text}</p>
              </div>
            ))}
            {!recentReviews.length && <p className="profile-muted">最近还没有任务复盘。</p>}
          </div>
        </div>

        <div className="profile-card dashboard-failure-card">
          <div className="dash-card-head">
            <h3>失败项</h3>
            <span>{failures.length} 条</span>
          </div>
          <div className="dash-failure-list">
            {failures.slice(0, 8).map((item, index) => (
              <div key={`${item.source}-${index}`} className="dash-failure-item">
                <strong>{item.name}</strong>
                <span>{item.source}</span>
                <p>{item.detail || '无细节'}</p>
              </div>
            ))}
            {!failures.length && <p className="profile-muted">当前没有失败项，状态很干净。</p>}
          </div>
        </div>
      </div>

      <div className="profile-card dashboard-log-section">
        <div className="dash-card-head">
          <h3>实时日志</h3>
          <span>最近几十行</span>
        </div>
        <div className="dash-log-grid">
          {logs.map((item) => <LogCard key={item.name} item={item} />)}
        </div>
      </div>
    </div>
  );
}

export function SystemPanel({ systemHealth, agentToolsInfo, alignment, onRefresh, onHabitCheck }) {
  return (
    <div className="profile-panel">
      <div className="profile-header">
        <h2>系统</h2>
        <button type="button" className="profile-btn" onClick={onRefresh}>刷新</button>
      </div>
      {systemHealth?.doctor ? (
        <div className="profile-card profile-health-card">
          <h3>自检 /meta/doctor</h3>
          <p className={systemHealth.doctor.ok ? 'health-ok' : 'health-warn'}>
            {systemHealth.doctor.ok ? '全部通过' : `${systemHealth.doctor.failed_count} 项需处理`}
          </p>
          <ul className="profile-health-list">
            {(systemHealth.doctor.checks || []).map((c) => (
              <li key={c.name} className={c.status === 'ok' ? 'ok' : c.status === 'skip' ? 'skip' : 'fail'}>
                <span>{c.name}</span>
                <span>{c.status === 'ok' ? '✓' : c.status === 'skip' ? '○' : '✗'}</span>
                {c.detail ? <small>{c.detail}</small> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="profile-muted">无法加载自检，请确认后端已启动。</p>
      )}
      {systemHealth?.habit && (
        <div className="profile-card">
          <h3>习惯体检（每天两次）</h3>
          <p className="profile-muted">
            本地时段：{(systemHealth.habit.check_hours_local || []).join(':00、')}:00
            {systemHealth.habit.enabled ? '' : ' · 已关闭'}
          </p>
          {systemHealth.habit.last_run ? (
            <p className={systemHealth.habit.last_run.doctor_ok ? 'health-ok' : 'health-warn'}>
              上次：{systemHealth.habit.last_run.phase}
              {systemHealth.habit.last_run.doctor_ok ? ' · 体检通过' : ` · ${systemHealth.habit.last_run.doctor_failed} 项未通过`}
              {systemHealth.habit.last_run.skill_written ? ' · 已更新 learned 技能' : ''}
            </p>
          ) : (
            <p className="profile-muted">尚未执行过；到点自动跑，或点下方立即体检。</p>
          )}
          {systemHealth.habit.learned_skill_file ? (
            <p className="profile-muted">自我扩展：`agent_skills/{systemHealth.habit.learned_skill_file}`</p>
          ) : null}
          {onHabitCheck ? (
            <button type="button" className="profile-btn" onClick={onHabitCheck}>立即习惯体检</button>
          ) : null}
        </div>
      )}
      {agentToolsInfo && (
        <div className="profile-card">
          <h3>Agent 工具 ({agentToolsInfo.count})</h3>
          <ul className="profile-bullets">{(agentToolsInfo.tools || []).map((t) => <li key={t}>{t}</li>)}</ul>
        </div>
      )}
      {alignment?.themes?.length > 0 && (
        <div className="profile-card">
          <h3>社区风向对照</h3>
          <p className="profile-muted">对标 GitHub Trending 主题 → 本仓库 API/技能</p>
          <ul className="profile-bullets">
            {alignment.themes.slice(0, 8).map((t) => (
              <li key={t.id}>
                <strong>{t.label}</strong>
                <small>{(t.local || []).slice(0, 2).join(' · ')}</small>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function SkillsPanel({ skillsCatalog, onRefresh, onPick }) {
  return (
    <div className="profile-panel">
      <div className="profile-header">
        <h2>技能库</h2>
        <button type="button" className="profile-btn" onClick={onRefresh}>刷新</button>
      </div>
      <p className="profile-muted">
        backend/agent_skills
        {skillsCatalog?.count != null ? ` · 共 ${skillsCatalog.count} 条` : ''}
        {skillsCatalog?.enabled === false ? ' · 技能包已关闭 (AGENT_SKILL_PACK=0)' : ''}
        {' · 点击后下一条消息挂载'}
      </p>
      {!skillsCatalog ? (
        <p className="profile-muted">加载中…</p>
      ) : (
        <div className="skills-grid">
          {(skillsCatalog.skills || []).map((sk) => (
            <button type="button" key={sk.id} className="skill-card" onClick={() => onPick(sk)}>
              <strong>{sk.title}</strong>
              <span className="skill-id">{sk.id}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function SchedulerPanel({ jobs, form, setForm, onRefresh, onCreate, onRun }) {
  return (
    <div className="profile-panel">
      <div className="profile-header">
        <h2>定时任务</h2>
        <button type="button" className="profile-btn" onClick={onRefresh}>刷新</button>
      </div>
      <div className="profile-card">
        <h3>新建</h3>
        <input className="tool-input" placeholder="名称" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <textarea className="tool-textarea" rows={2} placeholder="提示词" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
        <input className="tool-input" type="number" min={60} value={form.interval_sec} onChange={(e) => setForm({ ...form, interval_sec: Number(e.target.value) })} />
        <button type="button" className="profile-btn" onClick={onCreate}>创建</button>
      </div>
      <ul className="profile-list">
        {jobs.map((j) => (
          <li key={j.id}>
            {j.name} · {j.interval_sec}s · {j.enabled ? '开' : '关'}
            <button type="button" className="profile-btn" onClick={() => onRun(j.id)}>运行</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
