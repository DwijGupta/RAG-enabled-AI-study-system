import React, { useState } from 'react';
import { 
  Plus, 
  Search, 
  UploadCloud, 
  BookOpen, 
  ArrowRight, 
  Clock, 
  Folder, 
  CheckCircle2, 
  TrendingUp, 
  MoreHorizontal,
  Sparkles,
  Layers
} from 'lucide-react';

export default function HomeView({
  notebooks,
  onSelectNotebook,
  onNewNotebook,
  onOpenUpload,
  onOpenFlashcards,
  onOpenCommandPalette
}) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredNotebooks = notebooks.filter(
    (nb) =>
      nb.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      nb.course?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      backgroundColor: 'var(--bg-app)',
      padding: '36px 40px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }}>
      <div style={{ width: '100%', maxWidth: '1040px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {/* Welcome Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.025em' }}>
              What are you learning today?
            </h1>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Select a notebook to continue studying, or ground a new AI tutor in your course materials.
            </p>
          </div>

          <button
            onClick={onNewNotebook}
            className="btn btn-primary"
            style={{ padding: '9px 16px', fontSize: '0.86rem' }}
          >
            <Plus size={16} />
            <span>New notebook</span>
          </button>
        </div>

        {/* Global Search Bar */}
        <div style={{ position: 'relative', width: '100%' }}>
          <Search size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '16px', top: '13px' }} />
          <input
            type="text"
            placeholder="Search across all notebooks, textbooks, notes, and study guides... (⌘K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClick={() => {}}
            className="input-field"
            style={{
              paddingLeft: '44px',
              paddingTop: '12px',
              paddingBottom: '12px',
              fontSize: '0.92rem',
              borderRadius: '10px'
            }}
          />
        </div>

        {/* Primary Action Card: Quick Start & Continue */}
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: 'var(--shadow-sm)',
          display: 'grid',
          gridTemplateColumns: '1.4fr 1fr',
          gap: '24px'
        }}>
          {/* Left Column: Continue Learning */}
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span className="badge badge-info" style={{ fontSize: '0.72rem' }}>
                  Continue where you left off
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  12 mins ago
                </span>
              </div>

              <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Machine Learning Fundamentals
              </h2>

              <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: 1.5 }}>
                Last discussion: <strong>Gradient Descent & Loss Optimization</strong> with 4 active textbooks and lecture notes.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '18px' }}>
              <button
                onClick={() => onSelectNotebook(notebooks[0])}
                className="btn btn-primary btn-sm"
                style={{ padding: '7px 14px', fontSize: '0.82rem' }}
              >
                <span>Resume conversation</span>
                <ArrowRight size={14} />
              </button>
              <button
                onClick={onOpenFlashcards}
                className="btn btn-secondary btn-sm"
                style={{ padding: '7px 14px', fontSize: '0.82rem' }}
              >
                <Layers size={14} />
                <span>Review flashcards</span>
              </button>
            </div>
          </div>

          {/* Right Column: Quick Ingestion Dropzone */}
          <div
            onClick={onOpenUpload}
            style={{
              border: '1px dashed var(--border-strong)',
              borderRadius: '10px',
              padding: '20px',
              backgroundColor: 'var(--bg-subtle)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-strong)'}
          >
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              backgroundColor: 'var(--bg-surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '10px',
              boxShadow: 'var(--shadow-xs)'
            }}>
              <UploadCloud size={20} color="var(--accent-primary)" />
            </div>

            <div style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Upload new study material
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Drag & drop PDFs, slides, or notes to ground your tutor
            </div>
          </div>
        </div>

        {/* Notebooks Grid Section */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Your Study Notebooks ({filteredNotebooks.length})
            </h2>
            <button onClick={onNewNotebook} className="btn btn-ghost btn-sm" style={{ fontSize: '0.78rem' }}>
              + Create notebook
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))',
            gap: '16px'
          }}>
            {filteredNotebooks.map((nb) => (
              <div
                key={nb.id}
                onClick={() => onSelectNotebook(nb)}
                className="card"
                style={{
                  padding: '18px 20px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minHeight: '160px'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                      {nb.course || 'Independent Study'}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {nb.lastActive}
                    </span>
                  </div>

                  <h3 style={{ fontSize: '0.96rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
                    {nb.title}
                  </h3>

                  <p style={{
                    fontSize: '0.78rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.45,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>
                    {nb.description}
                  </p>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '12px',
                  marginTop: '14px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    <BookOpen size={13} />
                    <span>{nb.sourcesCount} sources</span>
                  </div>

                  <span style={{ fontSize: '0.74rem', color: 'var(--accent-primary)', fontWeight: 500 }}>
                    Open notebook →
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
