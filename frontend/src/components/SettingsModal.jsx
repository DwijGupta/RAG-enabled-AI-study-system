import React, { useState } from 'react';
import { 
  X, 
  Moon, 
  Sun, 
  Sparkles, 
  Brain, 
  ShieldCheck, 
  Sliders, 
  Trash2, 
  Check, 
  RotateCcw
} from 'lucide-react';
import { tutorModes } from '../data/mockData.js';

export default function SettingsModal({
  isOpen,
  onClose,
  theme,
  onToggleTheme,
  tutorMode,
  setTutorMode
}) {
  const [responseLength, setResponseLength] = useState('standard'); // 'concise' | 'standard' | 'detailed'
  const [useMemory, setUseMemory] = useState(true);
  const [mathRendering, setMathRendering] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 600);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '540px' }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Settings & Learning Preferences
            </h2>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Customize theme, tutoring persona, and privacy
            </div>
          </div>

          <button onClick={onClose} className="btn-icon">
            <X size={16} />
          </button>
        </div>

        {/* Settings Body */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
          {/* Appearance Section */}
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Appearance & Interface
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div>
                <div style={{ fontSize: '0.86rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                  Interface Theme
                </div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Currently using {theme === 'dark' ? 'Dark theme' : 'Light theme'}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  onClick={() => theme === 'dark' && onToggleTheme()}
                  className={`btn btn-sm ${theme === 'light' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  <Sun size={13} />
                  <span>Light</span>
                </button>
                <button
                  onClick={() => theme === 'light' && onToggleTheme()}
                  className={`btn btn-sm ${theme === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  <Moon size={13} />
                  <span>Dark</span>
                </button>
              </div>
            </div>
          </div>

          {/* Default Tutoring Persona */}
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Default Tutoring Mode
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '8px'
            }}>
              {tutorModes.map((mode) => (
                <div
                  key={mode.id}
                  onClick={() => setTutorMode(mode.id)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    border: `1px solid ${tutorMode === mode.id ? 'var(--accent-primary)' : 'var(--border-default)'}`,
                    backgroundColor: tutorMode === mode.id ? 'var(--accent-primary-subtle)' : 'var(--bg-surface)',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '2px'
                  }}
                >
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: tutorMode === mode.id ? 'var(--accent-primary-text)' : 'var(--text-primary)' }}>
                    {mode.label}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {mode.description}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Explanation Detail Level */}
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Explanation Detail Length
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              {['concise', 'standard', 'detailed'].map((len) => (
                <button
                  key={len}
                  onClick={() => setResponseLength(len)}
                  className={`btn btn-sm ${responseLength === len ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, textTransform: 'capitalize' }}
                >
                  {len}
                </button>
              ))}
            </div>
          </div>

          {/* Memory & Privacy */}
          <div>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Cognitive Memory & Privacy
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              padding: '12px 14px',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)'
            }}>
              <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
                <div>
                  <div style={{ fontSize: '0.84rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                    Enable Persistent Concept State
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    Personalizes explanations based on your Bayesian Knowledge Tracing scores.
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={useMemory}
                  onChange={(e) => setUseMemory(e.target.checked)}
                  style={{ accentColor: 'var(--accent-primary)', width: '16px', height: '16px' }}
                />
              </label>

              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Clear current session memory cache
                </span>
                <button className="btn btn-ghost btn-sm" style={{ color: 'var(--status-danger-badge)', fontSize: '0.72rem' }}>
                  Clear Memory
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '8px'
        }}>
          <button onClick={onClose} className="btn btn-ghost">
            Cancel
          </button>
          <button onClick={handleSave} className="btn btn-primary">
            {savedSuccess ? <Check size={14} /> : null}
            <span>{savedSuccess ? 'Saved' : 'Save Changes'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
