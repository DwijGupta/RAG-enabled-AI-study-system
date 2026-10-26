import React, { useState } from 'react';
import { 
  BookOpen, 
  Layers, 
  CheckCircle2, 
  FileText, 
  Search, 
  Moon, 
  Sun, 
  Sparkles, 
  SlidersHorizontal,
  ChevronDown,
  PanelLeft,
  PanelRight
} from 'lucide-react';
import { tutorModes } from '../data/mockData.js';

export default function Header({
  notebook,
  onUpdateNotebookTitle,
  activeSourcesCount,
  totalSourcesCount,
  tutorMode,
  setTutorMode,
  onOpenStudyGuide,
  onOpenFlashcards,
  onOpenQuiz,
  onOpenNotes,
  onOpenCommandPalette,
  theme,
  onToggleTheme,
  onGoHome,
  isSourcesOpen,
  onToggleSources,
  isEvidenceOpen,
  onToggleEvidence
}) {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState(notebook?.title || 'Machine Learning Fundamentals');
  const [isModeOpen, setIsModeOpen] = useState(false);

  const handleTitleSubmit = () => {
    setIsEditingTitle(false);
    if (titleValue.trim() && onUpdateNotebookTitle) {
      onUpdateNotebookTitle(titleValue.trim());
    }
  };

  const currentModeObj = tutorModes.find((m) => m.id === tutorMode) || tutorModes[0];

  return (
    <header style={{
      height: '56px',
      backgroundColor: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-default)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      gap: '16px',
      flexShrink: 0,
      zIndex: 40
    }}>
      {/* Left: Signature Brand Logo + Notebook Title & Metadata */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0 }}>
        {/* Signature Logo Mark */}
        <div 
          onClick={onGoHome}
          title="AI Study Buddy System"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            paddingRight: '14px',
            borderRight: '1px solid var(--border-default)',
            cursor: 'pointer',
            userSelect: 'none',
            flexShrink: 0
          }}
        >
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 6px rgba(37, 99, 235, 0.28)'
          }}>
            <Sparkles size={15} />
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{
              fontFamily: "'Caveat', 'Dancing Script', cursive",
              fontSize: '1.45rem',
              fontWeight: 700,
              letterSpacing: '0.01em',
              lineHeight: 1,
              background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              AI Study Buddy
            </span>
            <span style={{
              fontSize: '0.62rem',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--accent-primary)',
              backgroundColor: 'var(--accent-primary-subtle)',
              padding: '1px 5px',
              borderRadius: '4px',
              border: '1px solid var(--accent-primary-border)',
              transform: 'translateY(-2px)'
            }}>
              SYSTEM
            </span>
          </div>
        </div>
        {isEditingTitle ? (
          <input
            type="text"
            value={titleValue}
            onChange={(e) => setTitleValue(e.target.value)}
            onBlur={handleTitleSubmit}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleTitleSubmit();
              if (e.key === 'Escape') setIsEditingTitle(false);
            }}
            autoFocus
            style={{
              fontWeight: 600,
              fontSize: '1rem',
              padding: '3px 8px',
              borderRadius: '6px',
              border: '1px solid var(--border-focus)',
              backgroundColor: 'var(--bg-app)',
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          />
        ) : (
          <h1 
            onClick={() => setIsEditingTitle(true)}
            title="Click to rename notebook"
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {notebook?.title || 'Machine Learning Fundamentals'}
          </h1>
        )}

        {notebook?.course && (
          <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
            {notebook.course}
          </span>
        )}

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          backgroundColor: 'var(--bg-subtle)',
          padding: '2px 8px',
          borderRadius: '6px',
          border: '1px solid var(--border-subtle)',
          whiteSpace: 'nowrap'
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: activeSourcesCount > 0 ? 'var(--status-success-badge)' : 'var(--text-muted)'
          }} />
          <span>{activeSourcesCount} of {totalSourcesCount} sources active</span>
        </div>
      </div>

      {/* Center / Right: Mode Selector & Study Tool Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {/* Tutor Mode Selector */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsModeOpen(!isModeOpen)}
            className="btn btn-secondary btn-sm"
            style={{ gap: '6px' }}
            title="Switch Tutor Mode"
          >
            <Sparkles size={13} color="var(--accent-primary)" />
            <span>Mode: <strong>{currentModeObj.label}</strong></span>
            <ChevronDown size={13} color="var(--text-muted)" />
          </button>

          {isModeOpen && (
            <div style={{
              position: 'absolute',
              top: '110%',
              right: 0,
              width: '230px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: '9px',
              boxShadow: 'var(--shadow-md)',
              padding: '6px',
              zIndex: 100,
              display: 'flex',
              flexDirection: 'column',
              gap: '2px'
            }}>
              <div style={{ padding: '4px 8px', fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Select Tutor Mode
              </div>
              {tutorModes.map((mode) => (
                <div
                  key={mode.id}
                  onClick={() => {
                    setTutorMode(mode.id);
                    setIsModeOpen(false);
                  }}
                  style={{
                    padding: '6px 8px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    backgroundColor: tutorMode === mode.id ? 'var(--accent-primary-subtle)' : 'transparent',
                    color: tutorMode === mode.id ? 'var(--accent-primary-text)' : 'var(--text-primary)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px'
                  }}
                  onMouseEnter={(e) => {
                    if (tutorMode !== mode.id) e.currentTarget.style.backgroundColor = 'var(--bg-surface-hover)';
                  }}
                  onMouseLeave={(e) => {
                    if (tutorMode !== mode.id) e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.8rem' }}>{mode.label}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{mode.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ width: '1px', height: '20px', backgroundColor: 'var(--border-default)', margin: '0 4px' }} />

        {/* Quick Tools: Study Guide, Flashcards, Quiz */}
        <button 
          onClick={onOpenStudyGuide}
          className="btn btn-secondary btn-sm"
          title="Generate or view structured Study Guide"
        >
          <BookOpen size={14} color="var(--text-secondary)" />
          <span>Study Guide</span>
        </button>

        <button 
          onClick={onOpenFlashcards}
          className="btn btn-secondary btn-sm"
          title="Review Flashcards"
        >
          <Layers size={14} color="var(--text-secondary)" />
          <span>Flashcards</span>
        </button>

        <button 
          onClick={onOpenQuiz}
          className="btn btn-secondary btn-sm"
          title="Take a practice quiz"
        >
          <CheckCircle2 size={14} color="var(--text-secondary)" />
          <span>Practice Quiz</span>
        </button>

        <div style={{ width: '1px', height: '20px', backgroundColor: 'var(--border-default)', margin: '0 4px' }} />

        {/* Side Panel Shift/Toggle Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <button 
            onClick={onToggleSources}
            className={`btn btn-sm ${isSourcesOpen ? 'btn-secondary' : 'btn-ghost'}`}
            style={{ padding: '4px 8px', fontSize: '0.74rem' }}
            title={isSourcesOpen ? "Collapse Sources side panel" : "Expand Sources side panel"}
          >
            <PanelLeft size={14} color={isSourcesOpen ? "var(--accent-primary)" : "var(--text-muted)"} />
            <span>Sources</span>
          </button>

          <button 
            onClick={onToggleEvidence}
            className={`btn btn-sm ${isEvidenceOpen ? 'btn-secondary' : 'btn-ghost'}`}
            style={{ padding: '4px 8px', fontSize: '0.74rem' }}
            title={isEvidenceOpen ? "Collapse Evidence side panel" : "Expand Evidence side panel"}
          >
            <PanelRight size={14} color={isEvidenceOpen ? "var(--accent-primary)" : "var(--text-muted)"} />
            <span>Evidence</span>
          </button>
        </div>

        <div style={{ width: '1px', height: '20px', backgroundColor: 'var(--border-default)', margin: '0 4px' }} />

        {/* Command Search Palette trigger */}
        <button 
          onClick={onOpenCommandPalette}
          className="btn btn-ghost btn-sm" 
          style={{ gap: '6px', color: 'var(--text-muted)' }}
          title="Command Palette (Ctrl+K)"
        >
          <Search size={14} />
          <kbd style={{
            fontSize: '0.7rem',
            padding: '1px 5px',
            borderRadius: '4px',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)'
          }}>
            ⌘K
          </kbd>
        </button>

        {/* Theme Toggle */}
        <button 
          onClick={onToggleTheme} 
          className="btn-icon" 
          title={theme === 'dark' ? 'Switch to Light mode' : 'Switch to Dark mode'}
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
}
