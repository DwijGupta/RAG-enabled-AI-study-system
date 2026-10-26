import React from 'react';
import { Sparkles, Brain, BookOpen, Layers, UploadCloud, CheckCircle2 } from 'lucide-react';

export default function Navbar({ onOpenUpload, onOpenReview, onOpenPractice, dueCardsCount }) {
  return (
    <header className="glass-panel" style={{ margin: '16px 20px 0 20px', padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 10 }}>
      {/* Brand & Architecture Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #6366F1 0%, #A855F7 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)'
        }}>
          <Brain size={24} color="#FFF" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.15rem' }} className="gradient-text">StudyBuddy</h1>
            <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '9999px', background: 'rgba(99, 102, 241, 0.2)', color: '#A5B4FC', border: '1px solid rgba(99, 102, 241, 0.4)', fontWeight: 600 }}>
              PLAN 1: LEARNER-AWARE RAG
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Ollama Qwen 2.5 • BKT Cognitive Overlay • BGE-M3 Dense + BM25 Hybrid
          </p>
        </div>
      </div>

      {/* Global Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button onClick={onOpenPractice} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem' }}>
          <Sparkles size={16} color="#F59E0B" />
          <span>Diagnostic Quiz</span>
        </button>

        <button onClick={onOpenReview} className="btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8rem', position: 'relative' }}>
          <Layers size={16} color="#06B6D4" />
          <span>Spaced Practice</span>
          {dueCardsCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              background: '#EF4444',
              color: '#FFF',
              fontSize: '0.65rem',
              fontWeight: 700,
              padding: '2px 6px',
              borderRadius: '9999px',
              boxShadow: '0 2px 6px rgba(239, 68, 68, 0.5)'
            }}>
              {dueCardsCount}
            </span>
          )}
        </button>

        <button onClick={onOpenUpload} className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.8rem' }}>
          <UploadCloud size={16} />
          <span>Ingest PDF</span>
        </button>
      </div>
    </header>
  );
}
