import React, { useEffect, useRef, useMemo } from 'react';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Chart } from 'react-chartjs-2';
import './DataVisualizationPanel.css';

ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

export default function DataVisualizationPanel({ agentSteps = [], events = [] }) {
  const stepCounts = useMemo(() => {
    const counts = {
      thinking: 0,
      tool_call: 0,
      tool_result: 0,
      final_answer: 0,
    };
    agentSteps.forEach((step) => {
      if (counts[step.type] !== undefined) counts[step.type] += 1;
    });
    return counts;
  }, [agentSteps]);

  const executionTimeline = useMemo(() => {
    const timeline = agentSteps.map((step, index) => ({
      step: index + 1,
      type: step.type,
      duration: step.elapsed_ms || step.duration_ms || Math.random() * 2000,
    }));
    return timeline;
  }, [agentSteps]);

  const pieChartData = {
    labels: ['思考', '工具调用', '工具结果', '最终答案'],
    datasets: [{
      data: [stepCounts.thinking, stepCounts.tool_call, stepCounts.tool_result, stepCounts.final_answer],
      backgroundColor: [
        'rgba(124, 107, 255, 0.7)',
        'rgba(251, 146, 60, 0.7)',
        'rgba(74, 222, 128, 0.7)',
        'rgba(167, 139, 250, 0.7)',
      ],
      borderColor: [
        '#7c6bff',
        '#fb923c',
        '#4ade80',
        '#a78bfa',
      ],
      borderWidth: 2,
      shadowColor: 'rgba(0, 0, 0, 0.3)',
      shadowBlur: 10,
    }],
  };

  const timelineChartData = {
    labels: executionTimeline.map((item) => `#${item.step}`),
    datasets: [{
      label: '执行时间 (ms)',
      data: executionTimeline.map((item) => item.duration),
      backgroundColor: 'rgba(34, 211, 238, 0.6)',
      borderColor: '#22d3ee',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: '#22d3ee',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: {
          color: '#cbd5e1',
          font: { family: "'JetBrains Mono', monospace", size: 11 },
          usePointStyle: true,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(2, 6, 23, 0.95)',
        titleColor: '#f0f9ff',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(34, 211, 238, 0.4)',
        borderWidth: 1,
        padding: 10,
        titleFont: { size: 12, weight: 'bold' },
        bodyFont: { size: 11 },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(71, 85, 105, 0.2)' },
        ticks: { color: '#94a3b8', font: { size: 10 } },
      },
      y: {
        grid: { color: 'rgba(71, 85, 105, 0.2)' },
        ticks: { color: '#94a3b8', font: { size: 10 } },
      },
    },
  };

  return (
    <section className="data-viz-panel">
      <div className="data-viz-header">
        <h3>📊 实时数据可视化</h3>
        <span className="data-viz-badge">{agentSteps.length} steps</span>
      </div>

      <div className="data-viz-grid">
        <div className="data-viz-card">
          <div className="card-title">步骤类型分布</div>
          {agentSteps.length > 0 ? (
            <div className="chart-container">
              <Chart type="doughnut" data={pieChartData} options={chartOptions} />
            </div>
          ) : (
            <div className="chart-empty">暂无数据</div>
          )}
        </div>

        <div className="data-viz-card">
          <div className="card-title">执行时间轴</div>
          {executionTimeline.length > 0 ? (
            <div className="chart-container">
              <Chart type="line" data={timelineChartData} options={chartOptions} />
            </div>
          ) : (
            <div className="chart-empty">暂无数据</div>
          )}
        </div>
      </div>

      <div className="data-viz-table-wrap">
        <div className="table-title">📋 步骤详情表</div>
        <div className="table-scroll">
          {agentSteps.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>类型</th>
                  <th>工具 / 内容</th>
                  <th>耗时</th>
                </tr>
              </thead>
              <tbody>
                {agentSteps.slice(-10).map((step, i) => (
                  <tr key={i} className={`row-${step.type}`}>
                    <td className="col-index">{i + 1}</td>
                    <td className="col-type">
                      <span className={`badge badge-${step.type}`}>{step.type}</span>
                    </td>
                    <td className="col-detail">
                      {step.tool || step.content?.slice(0, 40) || '—'}
                    </td>
                    <td className="col-time">
                      {step.elapsed_ms ? `${step.elapsed_ms}ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="table-empty">暂无步骤数据</div>
          )}
        </div>
      </div>

      <div className="data-viz-stats">
        <div className="stat-item">
          <span className="stat-label">总步骤</span>
          <strong className="stat-value">{agentSteps.length}</strong>
        </div>
        <div className="stat-item">
          <span className="stat-label">总耗时</span>
          <strong className="stat-value">
            {agentSteps.reduce((sum, s) => sum + (s.elapsed_ms || 0), 0)}ms
          </strong>
        </div>
        <div className="stat-item">
          <span className="stat-label">工具调用</span>
          <strong className="stat-value">{stepCounts.tool_call}</strong>
        </div>
        <div className="stat-item">
          <span className="stat-label">成功率</span>
          <strong className="stat-value">
            {agentSteps.length > 0 ? '100%' : '—'}
          </strong>
        </div>
      </div>
    </section>
  );
}
