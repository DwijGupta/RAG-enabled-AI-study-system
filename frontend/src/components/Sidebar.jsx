import React from 'react';
import { 
  Sparkles, 
  Home, 
  BookOpen, 
  MessageSquare, 
  FileText, 
  Layers, 
  CheckCircle2, 
  TrendingUp, 
  Plus, 
  Folder, 
  Pin, 
  Brain, 
  Settings, 
  ChevronDown, 
  Moon, 
  Sun, 
  PanelLeftClose, 
  PanelLeftOpen, 
  Search,
  Trash2
} from 'lucide-react';

export default function Sidebar({
  currentView,
  setCurrentView,
  notebooks,
  currentNotebook,
  onSelectNotebook,
  onNewNotebook,
  onOpenSettings,
  onOpenCommandPalette,
  theme,
  onToggleTheme,
  isCollapsed,
  setIsCollapsed,
  chatSessions = [],
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession
}) {
  if (isCollapsed) {
    return (
      <aside style={{
        width: '64px',
        backgroundColor: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '16px 8px',
        gap: '16px',
        height: '100vh',
        transition: 'width 0.2s ease',
        zIndex: 50
      }}>
        {/* Logo Icon */}
        <div 
          onClick={() => setCurrentView('home')}
          title="AI Study Buddy System Home"
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '9px',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)'
          }}>
          <Sparkles size={20} />
        </div>

        {/* Expand Button */}
        <button 
          onClick={() => setIsCollapsed(false)}
          className="btn-icon" 
          title="Expand sidebar"
        >
          <PanelLeftOpen size={18} />
        </button>

        <div style={{ width: '100%', height: '1px', backgroundColor: 'var(--border-subtle)' }} />

        {/* Quick Nav Icons */}
        <button 
          onClick={() => setCurrentView('home')} 
          className={`btn-icon ${currentView === 'home' ? 'btn-subtle' : ''}`}
          title="Home"
        >
          <Home size={18} />
        </button>
        <button 
          onClick={() => setCurrentView('notebook')} 
          className={`btn-icon ${currentView === 'notebook' ? 'btn-subtle' : ''}`}
          title="Notebook Workspace"
        >
          <BookOpen size={18} />
        </button>
        <button 
          onClick={() => setCurrentView('flashcards')} 
          className={`btn-icon ${currentView === 'flashcards' ? 'btn-subtle' : ''}`}
          title="Flashcards"
        >
          <Layers size={18} />
        </button>
        <button 
          onClick={() => setCurrentView('quizzes')} 
          className={`btn-icon ${currentView === 'quizzes' ? 'btn-subtle' : ''}`}
          title="Quizzes & Practice"
        >
          <CheckCircle2 size={18} />
        </button>
        <button 
          onClick={() => setCurrentView('progress')} 
          className={`btn-icon ${currentView === 'progress' ? 'btn-subtle' : ''}`}
          title="Learning Memory & Progress"
        >
          <TrendingUp size={18} />
        </button>

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
          <button onClick={onToggleTheme} className="btn-icon" title="Toggle theme">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button onClick={onOpenSettings} className="btn-icon" title="Settings">
            <Settings size={18} />
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside style={{
      width: '264px',
      minWidth: '264px',
      backgroundColor: 'var(--bg-sidebar)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden',
      transition: 'width 0.2s ease',
      zIndex: 50
    }}>
      {/* Top Header & Logo */}
      <div style={{
        padding: '16px 16px 12px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        <div 
          onClick={() => setCurrentView('home')}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '7px',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-xs)'
          }}>
            <Sparkles size={16} />
          </div>
          <div>
            <div style={{
              fontFamily: "'Caveat', 'Dancing Script', cursive",
              fontWeight: 700,
              fontSize: '1.35rem',
              letterSpacing: '0.01em',
              lineHeight: 1.1,
              background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              AI Study Buddy
            </div>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              System Workspace
            </div>
          </div>
        </div>

        <button 
          onClick={() => setIsCollapsed(true)}
          className="btn-icon" 
          style={{ width: '28px', height: '28px' }}
          title="Collapse sidebar"
        >
          <PanelLeftClose size={16} />
        </button>
      </div>

      {/* Workspace Switcher */}
      <div style={{ padding: '10px 14px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 10px',
          borderRadius: '7px',
          border: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
          cursor: 'pointer',
          fontSize: '0.8rem',
          color: 'var(--text-primary)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-primary)' }} />
            <span style={{ fontWeight: 600 }}>Stanford CS229</span>
          </div>
          <ChevronDown size={14} color="var(--text-muted)" />
        </div>
      </div>

      {/* Action Buttons: New Notebook & Quick Search */}
      <div style={{ padding: '0 14px 10px 14px', display: 'flex', gap: '6px' }}>
        <button 
          onClick={onNewNotebook}
          className="btn btn-primary btn-sm"
          style={{ flex: 1, padding: '7px 10px', fontSize: '0.8rem', justifyContent: 'center' }}
        >
          <Plus size={14} />
          <span>New notebook</span>
        </button>

        <button 
          onClick={onOpenCommandPalette}
          className="btn btn-secondary btn-sm" 
          title="Quick search (Ctrl+K)"
          style={{ width: '34px', padding: 0 }}
        >
          <Search size={14} />
        </button>
      </div>

      {/* Scrollable Nav & Notebooks */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 10px' }}>
        {/* Core Navigation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginBottom: '16px' }}>
          <NavItem 
            icon={<Home size={16} />} 
            label="Home" 
            active={currentView === 'home'} 
            onClick={() => setCurrentView('home')} 
          />
          <NavItem 
            icon={<BookOpen size={16} />} 
            label="Current Notebook" 
            active={currentView === 'notebook'} 
            onClick={() => setCurrentView('notebook')} 
            badge={currentNotebook?.sourcesCount ? `${currentNotebook.sourcesCount} sources` : null}
          />
          <NavItem 
            icon={<Layers size={16} />} 
            label="Flashcards" 
            active={currentView === 'flashcards'} 
            onClick={() => setCurrentView('flashcards')} 
            badge="5 due"
          />
          <NavItem 
            icon={<CheckCircle2 size={16} />} 
            label="Quizzes & Practice" 
            active={currentView === 'quizzes'} 
            onClick={() => setCurrentView('quizzes')} 
          />
          <NavItem 
            icon={<TrendingUp size={16} />} 
            label="Learning Progress" 
            active={currentView === 'progress'} 
            onClick={() => setCurrentView('progress')} 
            badge="74%"
          />
        </div>

        {/* Section: Recent Notebooks */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 8px',
            fontSize: '0.72rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em'
          }}>
            <span>Recent Notebooks</span>
            <Folder size={12} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '4px' }}>
            {notebooks.map((nb) => {
              const isSelected = currentNotebook?.id === nb.id && currentView === 'notebook';
              return (
                <div
                  key={nb.id}
                  onClick={() => {
                    onSelectNotebook(nb);
                    setCurrentView('notebook');
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '9px',
                    padding: '7px 8px',
                    borderRadius: '7px',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    backgroundColor: isSelected ? 'var(--bg-surface-active)' : 'transparent',
                    color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                    fontWeight: isSelected ? 600 : 400,
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--bg-sidebar-hover)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <div style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: nb.color || 'var(--accent-primary)',
                    flexShrink: 0
                  }} />
                  <span style={{
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {nb.title}
                  </span>
                  {nb.pinned && <Pin size={11} color="var(--text-muted)" style={{ transform: 'rotate(45deg)' }} />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Section: Chat Memory & Past Sessions */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '4px 8px',
            fontSize: '0.72rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <MessageSquare size={12} color="var(--accent-primary)" />
              <span>Chat Memory ({chatSessions.length})</span>
            </div>
            {onNewSession && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onNewSession();
                }}
                className="btn btn-ghost btn-sm"
                style={{ padding: '1px 6px', fontSize: '0.68rem', height: '20px' }}
                title="Start a new chat session"
              >
                <Plus size={11} />
                <span>New</span>
              </button>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '4px' }}>
            {chatSessions.length === 0 ? (
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', padding: '6px 8px', fontStyle: 'italic' }}>
                No past sessions yet.
              </div>
            ) : (
              chatSessions.map((sess) => {
                const isSelected = currentSessionId === sess.session_id;
                return (
                  <div
                    key={sess.session_id}
                    onClick={() => onSelectSession && onSelectSession(sess.session_id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '6px 8px',
                      borderRadius: '7px',
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      backgroundColor: isSelected ? 'var(--bg-surface-active)' : 'transparent',
                      color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                      fontWeight: isSelected ? 600 : 400,
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--bg-sidebar-hover)';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <MessageSquare size={13} color={isSelected ? 'var(--accent-primary)' : 'var(--text-muted)'} style={{ flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '0.78rem'
                      }} title={sess.title}>
                        {sess.title}
                      </div>
                      <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>
                        {sess.last_active}
                      </div>
                    </div>

                    {onDeleteSession && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Delete chat memory for "${sess.title}"?`)) {
                            onDeleteSession(sess.session_id);
                          }
                        }}
                        className="btn-icon"
                        style={{ width: '22px', height: '22px', padding: 0, opacity: isSelected ? 1 : 0.6 }}
                        title="Delete this chat session"
                        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                      >
                        <Trash2 size={12} color="var(--status-danger-badge)" />
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Section: Learning Memory */}
        <div style={{
          padding: '10px 10px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
          backgroundColor: 'var(--bg-surface)',
          marginBottom: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <Brain size={14} color="var(--accent-primary)" />
            <span style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Learning Memory
            </span>
          </div>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4, margin: 0 }}>
            Tuned for: <strong style={{ color: 'var(--text-secondary)' }}>Geometric analogies & worked code</strong>
          </p>
          <button 
            onClick={() => setCurrentView('progress')}
            className="btn btn-ghost btn-sm"
            style={{ width: '100%', marginTop: '6px', fontSize: '0.72rem', padding: '3px 6px', justifyContent: 'center' }}
          >
            Review memory & state →
          </button>
        </div>
      </div>

      {/* Bottom User Profile & Theme Controls */}
      <div style={{
        padding: '12px 14px',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: 'var(--bg-surface)'
      }}>
        <div 
          onClick={onOpenSettings}
          style={{ display: 'flex', alignItems: 'center', gap: '9px', cursor: 'pointer', flex: 1 }}
        >
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            backgroundColor: 'var(--accent-primary-subtle)',
            color: 'var(--accent-primary-text)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: 700,
            border: '1px solid var(--accent-primary-border)'
          }}>
            AC
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              Alex Chen
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              CS Master's
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button 
            onClick={onToggleTheme} 
            className="btn-icon" 
            style={{ width: '28px', height: '28px' }}
            title={theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
          <button 
            onClick={onOpenSettings} 
            className="btn-icon" 
            style={{ width: '28px', height: '28px' }}
            title="Settings"
          >
            <Settings size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}

function NavItem({ icon, label, active, onClick, badge }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '9px',
        padding: '7px 10px',
        borderRadius: '7px',
        border: 'none',
        background: active ? 'var(--bg-surface)' : 'transparent',
        color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
        fontWeight: active ? 600 : 500,
        fontSize: '0.82rem',
        cursor: 'pointer',
        textAlign: 'left',
        width: '100%',
        boxShadow: active ? 'var(--shadow-xs)' : 'none',
        borderLeft: active ? '2px solid var(--accent-primary)' : '2px solid transparent',
        transition: 'all 0.15s ease'
      }}
      onMouseEnter={(e) => {
        if (!active) e.currentTarget.style.backgroundColor = 'var(--bg-sidebar-hover)';
      }}
      onMouseLeave={(e) => {
        if (!active) e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      <span style={{ color: active ? 'var(--accent-primary)' : 'var(--text-muted)', display: 'flex' }}>
        {icon}
      </span>
      <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {label}
      </span>
      {badge && (
        <span className="badge badge-neutral" style={{ fontSize: '0.68rem', padding: '1px 5px' }}>
          {badge}
        </span>
      )}
    </button>
  );
}
