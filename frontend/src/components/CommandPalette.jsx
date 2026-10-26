import React, { useState, useEffect } from 'react';
import { 
  Search, 
  BookOpen, 
  Layers, 
  CheckCircle2, 
  TrendingUp, 
  Moon, 
  Sun, 
  Plus, 
  UploadCloud, 
  FileText,
  X
} from 'lucide-react';

export default function CommandPalette({
  isOpen,
  onClose,
  notebooks,
  onSelectNotebook,
  onNewNotebook,
  onOpenUpload,
  onOpenFlashcards,
  onOpenQuiz,
  onOpenProgress,
  onToggleTheme,
  theme
}) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // will be controlled from parent
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    {
      id: 'act-new-nb',
      label: 'Create new notebook',
      category: 'Actions',
      icon: <Plus size={15} color="var(--accent-primary)" />,
      run: () => { onNewNotebook(); onClose(); }
    },
    {
      id: 'act-upload',
      label: 'Upload study material to active notebook',
      category: 'Actions',
      icon: <UploadCloud size={15} color="var(--accent-primary)" />,
      run: () => { onOpenUpload(); onClose(); }
    },
    {
      id: 'act-cards',
      label: 'Review due flashcards (FSRS scheduler)',
      category: 'Study Tools',
      icon: <Layers size={15} color="var(--status-info-badge)" />,
      run: () => { onOpenFlashcards(); onClose(); }
    },
    {
      id: 'act-quiz',
      label: 'Start diagnostic practice quiz',
      category: 'Study Tools',
      icon: <CheckCircle2 size={15} color="var(--status-success-badge)" />,
      run: () => { onOpenQuiz(); onClose(); }
    },
    {
      id: 'act-progress',
      label: 'View Learning Memory & Cognitive State',
      category: 'Progress',
      icon: <TrendingUp size={15} color="var(--accent-primary)" />,
      run: () => { onOpenProgress(); onClose(); }
    },
    {
      id: 'act-theme',
      label: `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`,
      category: 'Preferences',
      icon: theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />,
      run: () => { onToggleTheme(); onClose(); }
    }
  ];

  // Also include notebooks
  const notebookItems = notebooks.map((nb) => ({
    id: `nb-${nb.id}`,
    label: nb.title,
    subLabel: `${nb.course || 'Course'} • ${nb.sourcesCount} sources`,
    category: 'Notebooks',
    icon: <BookOpen size={15} color="var(--accent-primary)" />,
    run: () => { onSelectNotebook(nb); onClose(); }
  }));

  const allItems = [...actions, ...notebookItems].filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase()) ||
    (item.subLabel && item.subLabel.toLowerCase().includes(query.toLowerCase()))
  );

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div 
        className="modal-content" 
        onClick={(e) => e.stopPropagation()} 
        style={{ maxWidth: '560px', borderRadius: '12px', padding: 0 }}
      >
        {/* Search Input Bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '14px 18px',
          borderBottom: '1px solid var(--border-default)'
        }}>
          <Search size={18} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Type a command or search notebooks, flashcards, sources..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            autoFocus
            style={{
              flex: 1,
              border: 'none',
              background: 'transparent',
              color: 'var(--text-primary)',
              fontSize: '0.94rem',
              outline: 'none',
              fontFamily: 'inherit'
            }}
          />
          <kbd style={{
            fontSize: '0.7rem',
            padding: '2px 6px',
            borderRadius: '4px',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)'
          }}>
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '8px' }}>
          {allItems.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.84rem' }}>
              No matching commands or notebooks found.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {allItems.map((item, idx) => (
                <div
                  key={item.id}
                  onClick={item.run}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '9px 12px',
                    borderRadius: '7px',
                    cursor: 'pointer',
                    backgroundColor: idx === selectedIndex ? 'var(--bg-surface-hover)' : 'transparent',
                    color: 'var(--text-primary)',
                    transition: 'all 0.1s ease'
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {item.icon}
                    <div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 500 }}>
                        {item.label}
                      </div>
                      {item.subLabel && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {item.subLabel}
                        </div>
                      )}
                    </div>
                  </div>

                  <span className="badge badge-neutral" style={{ fontSize: '0.68rem' }}>
                    {item.category}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
