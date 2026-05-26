import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import './DigitalHumanStage.css';

const ASSET_BASE = `${(import.meta.env.BASE_URL || '/').replace(/\/$/, '')}/digital-human`;

function assetUrl(name) {
  return `${ASSET_BASE}/${name}`;
}

export default function DigitalHumanStage({
  agentBusy = false,
  modelLabel = '',
  onStartTask,
  fullscreen = true,
}) {
  const mountRef = useRef(null);
  const frameRef = useRef(0);
  const pointerRef = useRef({ x: 0, y: 0 });
  const [hasPhoto, setHasPhoto] = useState(false);
  const [hasDepth, setHasDepth] = useState(false);

  const statusText = agentBusy ? '意识流运行' : '低频觉醒';
  const loopSignals = [
    ['TICK', agentBusy ? '12s' : '60s'],
    ['FOCUS', '栈追踪'],
    ['MEMORY', '超级记忆'],
    ['SKILL', '候选生长'],
  ];

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [pr, dr] = await Promise.all([
          fetch(assetUrl('photo.png'), { method: 'HEAD' }),
          fetch(assetUrl('depth.png'), { method: 'HEAD' }),
        ]);
        if (!cancelled) {
          setHasPhoto(pr.ok);
          setHasDepth(pr.ok && dr.ok);
        }
      } catch {
        if (!cancelled) {
          setHasPhoto(false);
          setHasDepth(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onPointerMove = useCallback((e) => {
    const el = e.currentTarget;
    const r = el.getBoundingClientRect();
    pointerRef.current = {
      x: ((e.clientX - r.left) / r.width - 0.5) * 2,
      y: ((e.clientY - r.top) / r.height - 0.5) * 2,
    };
    el.style.setProperty('--dh-px', String(pointerRef.current.x));
    el.style.setProperty('--dh-py', String(pointerRef.current.y));
  }, []);

  useEffect(() => {
    if (!hasDepth || !mountRef.current) return undefined;

    const container = mountRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    camera.position.set(0, 0, 2.2);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    container.appendChild(renderer.domElement);

    const loader = new THREE.TextureLoader();
    const colorMap = loader.load(assetUrl('photo.png'));
    const depthMap = loader.load(assetUrl('depth.png'));
    colorMap.colorSpace = THREE.SRGBColorSpace;

    const uniforms = {
      uColor: { value: colorMap },
      uDepth: { value: depthMap },
      uDepthScale: { value: 0.18 },
      uPointer: { value: new THREE.Vector2(0, 0) },
      uTime: { value: 0 },
      uActive: { value: 0 },
      uBreath: { value: 0 },
    };

    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: `
        uniform sampler2D uDepth;
        uniform float uDepthScale;
        uniform vec2 uPointer;
        varying vec2 vUv;
        varying float vLift;
        void main() {
          vUv = uv;
          float d = texture2D(uDepth, uv).r;
          vLift = d;
          vec3 displaced = position;
          float faceDepth = 1.0 - d;
          displaced.z += faceDepth * uDepthScale;
          displaced.x += uPointer.x * 0.028 * faceDepth;
          displaced.y += uPointer.y * 0.026 * faceDepth;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
        }
      `,
      fragmentShader: `
        uniform sampler2D uColor;
        uniform float uTime;
        uniform float uActive;
        uniform float uBreath;
        varying vec2 vUv;
        varying float vLift;
        void main() {
          vec4 base = texture2D(uColor, vUv);
          vec3 col = base.rgb;
          vec2 p = vUv - vec2(0.5, 0.45);
          float oval = 1.0 - smoothstep(0.18, 0.72, length(p * vec2(0.82, 1.18)));
          float brow = smoothstep(0.64, 0.18, vUv.y);
          float cheek = 1.0 - smoothstep(0.04, 0.34, length((vUv - vec2(0.45, 0.49)) * vec2(1.1, 1.8)));
          float topLight = smoothstep(0.18, 0.95, vUv.y) * 0.08;
          float sideLight = smoothstep(-0.18, 0.62, vUv.x) * 0.07;
          float rim = smoothstep(0.54, 0.94, vLift) * 0.12;
          vec3 gold = vec3(0.86, 0.68, 0.42);
          vec3 rose = vec3(0.92, 0.58, 0.46);
          col = mix(col, col * vec3(1.08, 1.01, 0.94), oval * 0.24);
          col += gold * (topLight + sideLight + rim);
          col += rose * cheek * 0.035;
          col *= 1.0 - brow * 0.035;
          col *= 1.0 + uBreath * oval * 0.018;
          col *= 1.0 - uActive * 0.025;
          float vig = 1.0 - length((vUv - 0.5) * vec2(0.95, 1.22));
          col *= clamp(vig, 0.72, 1.04);
          gl_FragColor = vec4(col, base.a);
        }
      `,
      transparent: true,
    });

    const geometry = new THREE.PlaneGeometry(0.92, 1.15, 280, 280);
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    const keyLight = new THREE.DirectionalLight(0xd4b896, 0.28);
    keyLight.position.set(-1.8, 1.2, 2.5);
    scene.add(keyLight);

    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      const t = performance.now() * 0.001;
      const breath = Math.sin(t * 0.82) * 0.5 + 0.5;
      uniforms.uTime.value = t;
      uniforms.uBreath.value = breath;
      uniforms.uActive.value += ((agentBusy ? 1 : 0) - uniforms.uActive.value) * 0.06;
      uniforms.uPointer.value.lerp(
        new THREE.Vector2(pointerRef.current.x, pointerRef.current.y),
        0.07,
      );
      mesh.rotation.y = pointerRef.current.x * 0.045;
      mesh.rotation.x = -pointerRef.current.y * 0.032;
      mesh.scale.setScalar(1 + breath * 0.004);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameRef.current);
      window.removeEventListener('resize', onResize);
      geometry.dispose();
      material.dispose();
      colorMap.dispose();
      depthMap.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [hasDepth, agentBusy]);

  const photoSrc = assetUrl('photo.png');

  return (
    <section
      className={`dh-stage dh-atom${fullscreen ? ' dh-fullscreen' : ''}${agentBusy ? ' is-busy' : ''}${hasDepth ? ' has-3d' : ''}${hasPhoto ? ' has-photo' : ''}`}
      onPointerMove={onPointerMove}
      aria-label="黑光数字人"
      style={{ '--dh-px': 0, '--dh-py': 0 }}
    >
      {hasPhoto && (
        <div className="dh-backdrop" aria-hidden>
          <img className="dh-backdrop-img" src={photoSrc} alt="" draggable={false} />
          <div className="dh-backdrop-shade" />
        </div>
      )}

      <div className="dh-vignette" />
      <div className="dh-grain" />

      <aside className="dh-rail dh-rail-left">
        <div className="dh-rail-block">
          <span className="dh-rail-kicker">黑光</span>
          <span className="dh-rail-title">Maison Agent</span>
        </div>
        <div className="dh-rail-block dh-rail-muted">
          <span className="dh-rail-label">状态</span>
          <span className="dh-rail-value">{statusText}</span>
        </div>
        <div className="dh-rail-block dh-rail-muted">
          <span className="dh-rail-label">Loop</span>
          <span className="dh-rail-value">TICK · 抢占 · 复盘</span>
        </div>
        <div className="dh-rail-block dh-rail-muted">
          <span className="dh-rail-label">Model</span>
          <span className="dh-rail-value">{modelLabel || '双引擎'}</span>
        </div>
      </aside>

      <aside className="dh-rail dh-rail-right">
        <div className="dh-rail-block dh-rail-muted">
          <span className="dh-rail-label">Focus</span>
          <span className="dh-rail-value">多帧注意力栈</span>
        </div>
        <div className="dh-rail-block dh-rail-muted">
          <span className="dh-rail-label">Memory</span>
          <span className="dh-rail-value">语气反思</span>
        </div>
        <div className="dh-rail-block dh-rail-muted">
          <span className="dh-rail-label">Growth</span>
          <span className="dh-rail-value">联网候选技能</span>
        </div>
        <div className="dh-rail-block">
          <span className="dh-rail-label">Depth</span>
          <span className="dh-rail-value">{hasDepth ? '真脸浮雕' : '待 depth.png'}</span>
        </div>
      </aside>

      <div className="dh-center">
        <div className="dh-consciousness-ring" aria-hidden>
          {loopSignals.map(([label, value], index) => (
            <span
              key={label}
              className="dh-loop-chip"
              style={{ '--loop-i': index }}
            >
              <b>{label}</b>
              <em>{value}</em>
            </span>
          ))}
        </div>
        <div className="dh-viewport" ref={mountRef} />
        {!hasPhoto && (
          <div className="dh-fallback">
            <p className="dh-fallback-title">等待肖像</p>
            <p className="dh-fallback-hint">
              把肖像存为 <code>face.png</code> 后运行
              <code>python scripts/depth_infer.py --device cpu</code>
            </p>
          </div>
        )}
        {hasPhoto && !hasDepth && (
          <p className="dh-parallax-hint">平面肖像 · 生成 depth.png 后启用真人浮雕</p>
        )}
      </div>

      <footer className="dh-statusbar">
        <span className="dh-statusbar-item">BT Conscious Maison Agent</span>
        <span className="dh-statusbar-sep" />
        <span className="dh-statusbar-item">{statusText}</span>
        <span className="dh-statusbar-sep" />
        <span className="dh-statusbar-item">真人 3D · 自成长技能</span>
        <span className="dh-statusbar-spacer" />
        <button type="button" className="dh-statusbar-cta" onClick={onStartTask}>
          下达指令
        </button>
      </footer>
    </section>
  );
}
