import React, { useRef, useEffect, useState } from 'react';
import { GitFork, Info, PlayCircle, RefreshCw } from 'lucide-react';

export default function ConceptGraphCanvas({ onPracticeConcept, reloadTrigger }) {
  const canvasRef = useRef(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);

  // Simulation physics state
  const simulationRef = useRef({
    nodes: [],
    edges: [],
    draggingNode: null,
    dragOffset: { x: 0, y: 0 }
  });

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/graph/data?user_id=student_1');
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
        initSimulation(data);
      }
    } catch (err) {
      console.error('Failed to fetch graph data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [reloadTrigger]);

  const initSimulation = (data) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const width = canvas.width;
    const height = canvas.height;

    // Distribute nodes in a circle or radial prerequisite layout
    const simNodes = data.nodes.map((n, i) => {
      const angle = (i / Math.max(1, data.nodes.length)) * 2 * Math.PI;
      const radius = 130 + (i % 2) * 50;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        radius: n.type === 'misconception' ? 14 : 20
      };
    });

    simulationRef.current.nodes = simNodes;
    simulationRef.current.edges = data.edges;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      const { nodes, edges, draggingNode } = simulationRef.current;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Simple force-directed relaxation
      const width = canvas.width;
      const height = canvas.height;
      const k = 0.04; // Spring constant
      const repulsion = 1800; // Node repulsion

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 260) {
            const force = repulsion / (dist * dist);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            if (nodes[i] !== draggingNode) { nodes[i].vx -= fx; nodes[i].vy -= fy; }
            if (nodes[j] !== draggingNode) { nodes[j].vx += fx; nodes[j].vy += fy; }
          }
        }

        // Center gravity
        const cdx = width / 2 - nodes[i].x;
        const cdy = height / 2 - nodes[i].y;
        if (nodes[i] !== draggingNode) {
          nodes[i].vx += cdx * 0.002;
          nodes[i].vy += cdy * 0.002;
        }

        // Damping
        nodes[i].vx *= 0.88;
        nodes[i].vy *= 0.88;
        if (nodes[i] !== draggingNode) {
          nodes[i].x += nodes[i].vx;
          nodes[i].y += nodes[i].vy;
        }

        // Boundary bounds
        nodes[i].x = Math.max(30, Math.min(width - 30, nodes[i].x));
        nodes[i].y = Math.max(30, Math.min(height - 30, nodes[i].y));
      }

      // Draw Edges (Prerequisite arrows)
      edges.forEach((edge) => {
        const source = nodes.find((n) => n.id === edge.source);
        const target = nodes.find((n) => n.id === edge.target);
        if (!source || !target) return;

        const isMisconception = edge.relation === 'REFUTES';
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = isMisconception ? 'rgba(139, 92, 246, 0.4)' : 'rgba(99, 102, 241, 0.35)';
        ctx.lineWidth = isMisconception ? 1.5 : 2;
        ctx.setLineDash(isMisconception ? [4, 4] : []);
        ctx.stroke();
        ctx.setLineDash([]);

        // Arrow head pointing to target
        const angle = Math.atan2(target.y - source.y, target.x - source.x);
        const arrowDist = target.radius + 6;
        const ax = target.x - Math.cos(angle) * arrowDist;
        const ay = target.y - Math.sin(angle) * arrowDist;

        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - 8 * Math.cos(angle - Math.PI / 6), ay - 8 * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(ax - 8 * Math.cos(angle + Math.PI / 6), ay - 8 * Math.sin(angle + Math.PI / 6));
        ctx.fillStyle = isMisconception ? '#8B5CF6' : '#6366F1';
        ctx.fill();
      });

      // Draw Nodes
      nodes.forEach((n) => {
        const isSelected = selectedNode && selectedNode.id === n.id;

        // Node Glow
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + (isSelected ? 6 : 2), 0, 2 * Math.PI);
        ctx.fillStyle = isSelected ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.4)';
        ctx.fill();

        // Node Body
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
        ctx.fillStyle = n.color || '#6366F1';
        ctx.fill();
        ctx.strokeStyle = isSelected ? '#FFFFFF' : 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = isSelected ? 3 : 1.5;
        ctx.stroke();

        // Label
        ctx.font = '600 11px Plus Jakarta Sans, sans-serif';
        ctx.fillStyle = '#F3F4F6';
        ctx.textAlign = 'center';
        ctx.fillText(n.label, n.x, n.y + n.radius + 14);

        // Sublabel (Mastery %)
        if (n.type !== 'misconception') {
          ctx.font = '500 9px JetBrains Mono, monospace';
          ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
          ctx.fillText(`${Math.round(n.p_mastery * 100)}%`, n.x, n.y + n.radius + 26);
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [selectedNode]);

  // Mouse interaction handlers
  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const hit = simulationRef.current.nodes.find((n) => {
      const dx = n.x - x;
      const dy = n.y - y;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 6;
    });

    if (hit) {
      simulationRef.current.draggingNode = hit;
      setSelectedNode(hit);
    } else {
      setSelectedNode(null);
    }
  };

  const handleMouseMove = (e) => {
    const dragging = simulationRef.current.draggingNode;
    if (!dragging) return;
    const rect = canvasRef.current.getBoundingClientRect();
    dragging.x = e.clientX - rect.left;
    dragging.y = e.clientY - rect.top;
    dragging.vx = 0;
    dragging.vy = 0;
  };

  const handleMouseUp = () => {
    simulationRef.current.draggingNode = null;
  };

  return (
    <div className="glass-panel" style={{ height: 'calc(100vh - 110px)', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
      {/* Header & Legend */}
      <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '0.95rem' }} className="gradient-text">Concept Prerequisite DAG</h2>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Real-time Bayesian Knowledge Tracing (BKT) Overlay
          </p>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.72rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} /> Mastered (&gt;75%)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B' }} /> In ZPD
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444' }} /> Needs Work
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#8B5CF6' }} /> Misconception
          </span>
          <button onClick={fetchGraph} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <canvas
          ref={canvasRef}
          width={650}
          height={480}
          style={{ width: '100%', height: '100%', cursor: 'grab' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        />

        {/* Selected Node Drawer */}
        {selectedNode && (
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              left: '16px',
              right: '16px',
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid var(--border-glass-bright)',
              borderRadius: '12px',
              padding: '14px 18px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
              backdropFilter: 'blur(16px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '16px'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#FFF' }}>{selectedNode.label}</span>
                <span className={`badge ${selectedNode.status === 'mastered' ? 'badge-quiz' : selectedNode.status === 'developing' ? 'badge-socratic' : 'badge-remediate'}`}>
                  {selectedNode.type === 'misconception' ? 'Misconception' : `Mastery: ${Math.round(selectedNode.p_mastery * 100)}%`}
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {selectedNode.description || 'Core curriculum concept in Deep Learning.'}
              </p>
            </div>

            {selectedNode.type !== 'misconception' && (
              <button
                onClick={() => onPracticeConcept(selectedNode.label)}
                className="btn-primary"
                style={{ padding: '8px 14px', fontSize: '0.78rem', whiteSpace: 'nowrap' }}
              >
                <PlayCircle size={14} />
                <span>Practice Concept</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
