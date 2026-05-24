import React, { useEffect, useState, useRef } from 'react';
import './ScreenStreamViewer.css';

export default function ScreenStreamViewer({ apiBase }) {
  const [currentFrame, setCurrentFrame] = useState(null);
  const [frameInfo, setFrameInfo] = useState(null);
  const [fps, setFps] = useState(0);
  const wsRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());

  useEffect(() => {
    const wsUrl = `${apiBase.replace('http', 'ws')}/screen/ws/screen`;
    
    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('屏幕流 WebSocket 已连接');
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'screen') {
              setCurrentFrame(`data:image/jpeg;base64,${data.data}`);
              setFrameInfo({
                timestamp: new Date(data.timestamp * 1000).toLocaleTimeString('zh-CN'),
                width: data.width,
                height: data.height,
                size_kb: data.size_kb,
              });
              
              frameCountRef.current += 1;
              const now = Date.now();
              if (now - lastFpsUpdateRef.current >= 1000) {
                setFps(frameCountRef.current);
                frameCountRef.current = 0;
                lastFpsUpdateRef.current = now;
              }
            }
          } catch (err) {
            console.error('消息解析失败:', err);
          }
        };
        
        ws.onerror = (event) => {
          console.error('WebSocket 错误:', event);
        };
        
        ws.onclose = () => {
          console.log('屏幕流 WebSocket 已断开');
          setTimeout(connect, 3000);
        };
        
        wsRef.current = ws;
      } catch (err) {
        setTimeout(connect, 3000);
      }
    };
    
    connect();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [apiBase]);

  if (!currentFrame) return null;

  return (
    <div className="screen-stream-viewer">
      <div className="screen-header">
        <h4>📺 实时屏幕</h4>
        <span className="fps-counter">{fps} FPS</span>
      </div>
      
      <div className="screen-canvas-container">
        <img 
          src={currentFrame} 
          alt="Agent 屏幕" 
          className="screen-image"
        />
        {frameInfo && (
          <div className="screen-overlay">
            <div className="screen-info">
              <span>📐 {frameInfo.width}×{frameInfo.height}</span>
              <span>📦 {frameInfo.size_kb} KB</span>
              <span>🕐 {frameInfo.timestamp}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
