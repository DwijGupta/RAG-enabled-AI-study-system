import React, { useState } from 'react';
import { 
  FileText, 
  Plus, 
  Search, 
  CheckSquare, 
  Square, 
  FileCheck2, 
  Film, 
  Presentation, 
  MoreVertical, 
  Check, 
  Trash2,
  ExternalLink,
  Image as ImageIcon,
  ChevronLeft
} from 'lucide-react';

export default function SourcesPanel({
  sources,
  onToggleSourceActive,
  onSelectAllSources,
  onClearAllSources,
  onOpenUpload,
  onRemoveSource,
  onSelectSourcePreview,
  width = 280,
  onCollapse
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeMenuId, setActiveMenuId] = useState(null);

  const filteredSources = sources.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeCount = sources.filter((s) => s.active).length;
  const allSelected = sources.length > 0 && activeCount === sources.length;

  const getSourceIcon = (type) => {
    switch (type) {
      case 'image':
        return <ImageIcon size={15} color="#10B981" />;
      case 'pdf':
        return <FileText size={15} color="#EF4444" />;
      case 'pptx':
        return <Presentation size={15} color="#F59E0B" />;
      case 'video':
        return <Film size={15} color="#8B5CF6" />;
      case 'md':
      default:
        return <FileCheck2 size={15} color="#3B82F6" />;
    }
  };

  return (
    <div style={{
      width: `${width}px`,
      minWidth: `${width}px`,
      backgroundColor: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-default)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Sources Header */}
      <div style={{
        padding: '14px 16px 10px 16px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Sources
            </h2>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {activeCount} of {sources.length} active in context
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button
              onClick={onOpenUpload}
              className="btn btn-primary btn-sm"
              style={{ padding: '5px 9px', fontSize: '0.75rem' }}
              title="Upload PDF, Image, Notes, PPTX, or Video"
            >
              <Plus size={13} />
              <span>Add</span>
            </button>
            {onCollapse && (
              <button
                onClick={onCollapse}
                className="btn-icon"
                style={{ width: '26px', height: '26px' }}
                title="Collapse sources panel"
              >
                <ChevronLeft size={15} />
              </button>
            )}
          </div>
        </div>

        {/* Search input */}
        <div style={{ position: 'relative' }}>
          <Search size={13} color="var(--text-muted)" style={{ position: 'absolute', left: '9px', top: '8px' }} />
          <input
            type="text"
            placeholder="Search sources..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field"
            style={{
              paddingLeft: '28px',
              paddingTop: '5px',
              paddingBottom: '5px',
              fontSize: '0.78rem'
            }}
          />
        </div>

        {/* Select All / Clear All controls */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.72rem',
          color: 'var(--text-muted)'
        }}>
          <button
            onClick={allSelected ? onClearAllSources : onSelectAllSources}
            className="btn btn-ghost btn-sm"
            style={{ padding: '2px 4px', fontSize: '0.72rem' }}
          >
            {allSelected ? 'Deselect all' : 'Select all'}
          </button>
          <span>Selected sources ground the AI</span>
        </div>
      </div>

      {/* Sources List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 10px' }}>
        {filteredSources.length === 0 ? (
          <div style={{
            padding: '24px 12px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.78rem'
          }}>
            No matching sources found.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {filteredSources.map((source) => (
              <div
                key={source.id}
                style={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                  padding: '8px 10px',
                  borderRadius: '8px',
                  backgroundColor: source.active ? 'var(--bg-subtle)' : 'transparent',
                  border: '1px solid',
                  borderColor: source.active ? 'var(--border-default)' : 'transparent',
                  transition: 'all 0.15s ease'
                }}
              >
                {/* Active Checkbox */}
                <button
                  onClick={() => onToggleSourceActive(source.id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    marginTop: '2px',
                    color: source.active ? 'var(--accent-primary)' : 'var(--text-subtle)'
                  }}
                  title={source.active ? 'Deactivate source' : 'Activate source'}
                >
                  {source.active ? <CheckSquare size={16} /> : <Square size={16} />}
                </button>

                {/* Source Icon & Details */}
                <div 
                  onClick={() => onSelectSourcePreview && onSelectSourcePreview(source)}
                  style={{ flex: 1, minWidth: 0, cursor: 'pointer' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    {getSourceIcon(source.type)}
                    <span style={{
                      fontSize: '0.8rem',
                      fontWeight: 500,
                      color: source.active ? 'var(--text-primary)' : 'var(--text-muted)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }} title={source.name}>
                      {source.name}
                    </span>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginTop: '3px',
                    fontSize: '0.68rem',
                    color: 'var(--text-muted)'
                  }}>
                    <span>{source.pages} {source.type === 'video' ? '' : 'pages'}</span>
                    <span>•</span>
                    <span>{source.size}</span>
                    <span>•</span>
                    <span className="badge badge-success" style={{ fontSize: '0.62rem', padding: '0 4px' }}>
                      Ready
                    </span>
                  </div>
                </div>

                {/* Context Menu Trigger */}
                <button
                  onClick={() => setActiveMenuId(activeMenuId === source.id ? null : source.id)}
                  className="btn-icon"
                  style={{ width: '22px', height: '22px', padding: 0 }}
                >
                  <MoreVertical size={13} />
                </button>

                {/* Dropdown Menu */}
                {activeMenuId === source.id && (
                  <div style={{
                    position: 'absolute',
                    top: '32px',
                    right: '10px',
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-default)',
                    borderRadius: '7px',
                    boxShadow: 'var(--shadow-md)',
                    zIndex: 20,
                    width: '130px',
                    padding: '4px'
                  }}>
                    <button
                      onClick={() => {
                        onSelectSourcePreview && onSelectSourcePreview(source);
                        setActiveMenuId(null);
                      }}
                      className="btn btn-ghost btn-sm"
                      style={{ width: '100%', justifyContent: 'flex-start', fontSize: '0.74rem' }}
                    >
                      <ExternalLink size={12} />
                      <span>Preview</span>
                    </button>
                    <button
                      onClick={() => {
                        onRemoveSource(source.id);
                        setActiveMenuId(null);
                      }}
                      className="btn btn-ghost btn-sm"
                      style={{ width: '100%', justifyContent: 'flex-start', fontSize: '0.74rem', color: 'var(--status-danger-badge)' }}
                    >
                      <Trash2 size={12} />
                      <span>Remove</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Dropzone Callout */}
      <div 
        onClick={onOpenUpload}
        style={{
          margin: '10px',
          padding: '10px',
          border: '1px dashed var(--border-strong)',
          borderRadius: '8px',
          backgroundColor: 'var(--bg-subtle)',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.15s ease'
        }}
        onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
        onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-strong)'}
      >
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          + Add more materials
        </div>
        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px' }}>
          PDF, DOCX, PPTX, MD, Video, Web
        </div>
      </div>
    </div>
  );
}
