import React, { useEffect, useRef, useMemo } from 'react';
import * as THREE from 'three';
import './WorkflowVisualization3D.css';

const WORKFLOW_NODES_3D = [
  { id: 'input', label: '输入', position: [-8, 0, 0], color: 0x22d3ee },
  { id: 'router', label: '路由', position: [-4, 0, 0], color: 0x0ea5e9 },
  { id: 'core', label: '黑光核心', position: [0, 0, 0], color: 0x8a2be2, size: 1.5 },
  { id: 'planner', label: '规划', position: [4, 3, 0], color: 0x7dd3fc },
  { id: 'vision', label: '多模感知', position: [4, -3, 0], color: 0xc4b5fd },
  { id: 'tools', label: '工具执行', position: [8, 1, 0], color: 0xfb923c },
  { id: 'memory', label: '记忆检索', position: [8, -1, 0], color: 0x4ade80 },
  { id: 'critic', label: '校验', position: [12, 0, 0], color: 0xf87171 },
  { id: 'output', label: '输出', position: [16, 0, 0], color: 0x34d399 },
];

export default function WorkflowVisualization3D({ agentSteps = [] }) {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const nodesRef = useRef({});
  const particlesRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a14);
    scene.fog = new THREE.Fog(0x0a0a14, 60, 100);
    sceneRef.current = scene;

    // Camera
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(4, 2, 14);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowShadowMap;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambLight);

    const pointLight = new THREE.PointLight(0x22d3ee, 1, 100);
    pointLight.position.set(10, 10, 10);
    pointLight.castShadow = true;
    scene.add(pointLight);

    // Create nodes
    const nodes = {};
    WORKFLOW_NODES_3D.forEach((nodeData) => {
      const size = nodeData.size || 1;
      const geometry = new THREE.IcosahedronGeometry(size * 0.6, 4);
      const material = new THREE.MeshPhongMaterial({
        color: nodeData.color,
        emissive: nodeData.color,
        emissiveIntensity: 0.3,
        shininess: 100,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(...nodeData.position);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = nodeData;

      // Glow effect
      const glowGeometry = new THREE.IcosahedronGeometry(size * 0.75, 4);
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: nodeData.color,
        transparent: true,
        opacity: 0.15,
      });
      const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
      glowMesh.position.copy(mesh.position);
      mesh.add(glowMesh);
      mesh.glowMesh = glowMesh;

      scene.add(mesh);
      nodes[nodeData.id] = mesh;
    });
    nodesRef.current = nodes;

    // Create connections (edges)
    const edges = [
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

    edges.forEach(([from, to]) => {
      const fromNode = nodes[from];
      const toNode = nodes[to];
      if (!fromNode || !toNode) return;

      const geometry = new THREE.BufferGeometry();
      const positions = [
        ...fromNode.position.toArray(),
        ...toNode.position.toArray(),
      ];
      geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(positions), 3));

      const material = new THREE.LineBasicMaterial({
        color: 0x334155,
        linewidth: 2,
        fog: false,
      });
      const line = new THREE.Line(geometry, material);
      line.userData = { from, to };
      scene.add(line);
    });

    // Particle system for flow
    const particleCount = 500;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 40;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMaterial = new THREE.PointsMaterial({
      color: 0x22d3ee,
      size: 0.1,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.6,
      fog: false,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
    particlesRef.current = particles;

    // Animation loop
    let animationId;
    const animate = () => {
      animationId = requestAnimationFrame(animate);

      // Rotate nodes
      Object.values(nodes).forEach((node) => {
        node.rotation.x += 0.005;
        node.rotation.y += 0.008;
        node.glowMesh.rotation.copy(node.rotation);

        // Pulse glow
        const pulse = Math.sin(Date.now() * 0.003) * 0.5 + 0.5;
        node.glowMesh.material.opacity = 0.1 + pulse * 0.15;
      });

      // Animate particles
      if (particles) {
        particles.rotation.x += 0.0001;
        particles.rotation.y += 0.0003;
      }

      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      const newWidth = containerRef.current?.clientWidth || width;
      const newHeight = containerRef.current?.clientHeight || height;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      renderer.dispose();
      containerRef.current?.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div className="workflow-3d-container">
      <div ref={containerRef} className="workflow-3d-canvas" />
      <div className="workflow-3d-overlay">
        <h3>🌌 Agent 执行拓扑（3D）</h3>
        <p>{agentSteps.length} 个步骤 • 实时渲染</p>
      </div>
    </div>
  );
}
