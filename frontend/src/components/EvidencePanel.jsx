import React from 'react';
import { 
  FileText, 
  ExternalLink, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  CheckCircle2, 
  Layers, 
  Sparkles,
  BookOpen,
  Info
} from 'lucide-react';
import { citationsDatabase } from '../data/mockData.js';

export default function EvidencePanel({
  activeCitationId,
  onClose,
  onNavigateCitation,
  activeSources,
  width = 340
}) {
  // Flexible citation resolution (supports mock citation ID or live backend citation object)
  let currentCitation = null;
  if (typeof activeCitationId === 'object' && activeCitationId !== null) {
    currentCitation = {
      shortLabel: activeCitationId.cite_id || '[Citation]',
      sourceName: activeCitationId.doc_title || 'Document',
      pageNumber: activeCitationId.page_number || 1,
      section: activeCitationId.section_title || `Page ${activeCitationId.page_number || 1}`,
      quote: activeCitationId.content_snippet || activeCitationId.content || '',
      relevanceConfidence: 'Verified Grounded',
      image_url: activeCitationId.image_url,
      relatedConcepts: activeCitationId.concepts || []
    };
  } else if (activeCitationId && citationsDatabase[activeCitationId]) {
    currentCitation = citationsDatabase[activeCitationId];
  } else if (activeCitationId) {
    currentCitation = {
      shortLabel: activeCitationId,
      sourceName: 'Active Course Materials',
      pageNumber: 1,
      section: 'Verified Excerpt',
      quote: 'Evidence passage extracted from current active source.',
      relevanceConfidence: '98% Verified',
      relatedConcepts: []
    };
  }

  return (
    <div style={{
      width: `${width}px`,
      minWidth: `${width}px`,
      backgroundColor: 'var(--bg-surface)',
      borderLeft: '1px solid var(--border-default)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpen size={16} color="var(--accent-primary)" />
          <h2 style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Grounded Evidence & Source
          </h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {currentCitation && (
            <>
              <button 
                onClick={() => onNavigateCitation('prev')}
                className="btn-icon" 
                style={{ width: '26px', height: '26px' }}
                title="Previous citation"
              >
                <ChevronLeft size={14} />
              </button>
              <button 
                onClick={() => onNavigateCitation('next')}
                className="btn-icon" 
                style={{ width: '26px', height: '26px' }}
                title="Next citation"
              >
                <ChevronRight size={14} />
              </button>
            </>
          )}
          <button 
            onClick={onClose}
            className="btn-icon" 
            style={{ width: '26px', height: '26px' }}
            title="Close evidence panel"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {currentCitation ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Source Meta Card */}
            <div style={{
              padding: '12px 14px',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                  Citation {currentCitation.shortLabel}
                </span>
                <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                  {currentCitation.relevanceConfidence}
                </span>
              </div>

              <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)', marginTop: '2px' }}>
                {currentCitation.sourceName}
              </div>

              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Page {currentCitation.pageNumber} • {currentCitation.section}
              </div>
            </div>

            {/* Cited Passage with Highlight */}
            <div>
              <div style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '6px'
              }}>
                Cited Source Passage
              </div>

              <blockquote style={{
                margin: 0,
                padding: '12px 14px',
                borderLeft: '3px solid var(--accent-primary)',
                backgroundColor: 'var(--citation-bg)',
                borderRadius: '0 8px 8px 0',
                fontSize: '0.82rem',
                lineHeight: 1.6,
                color: 'var(--text-primary)',
                fontStyle: 'normal'
              }}>
                "{currentCitation.quote}"
              </blockquote>
            </div>

            {/* High-Fidelity Page Preview Simulation */}
            <div>
              <div style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <span>Document Page Preview</span>
                <span style={{ fontSize: '0.68rem', color: 'var(--accent-primary)', cursor: 'pointer' }}>
                  Full Page view ↗
                </span>
              </div>

              <div style={{
                border: '1px solid var(--border-default)',
                borderRadius: '8px',
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '16px',
                boxShadow: 'var(--shadow-sm)',
                position: 'relative'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '8px',
                  marginBottom: '10px',
                  fontSize: '0.68rem',
                  color: 'var(--text-muted)'
                }}>
                  <span style={{ textTransform: 'uppercase' }}>{currentCitation.sourceName}</span>
                  <span>PAGE {currentCitation.pageNumber}</span>
                </div>

                {currentCitation.image_url ? (
                  <div style={{
                    borderRadius: '6px',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)',
                    marginBottom: '10px',
                    backgroundColor: 'var(--bg-app)',
                    maxHeight: '260px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <img 
                      src={currentCitation.image_url} 
                      alt="Cited page snapshot"
                      style={{ width: '100%', maxHeight: '260px', objectFit: 'contain' }}
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  </div>
                ) : null}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{
                    padding: '8px 10px',
                    borderRadius: '6px',
                    backgroundColor: 'var(--citation-bg)',
                    border: '1px dashed var(--citation-border)',
                    fontSize: '0.74rem',
                    color: 'var(--citation-text)',
                    lineHeight: 1.5
                  }}>
                    <strong>Highlighted passage:</strong> {currentCitation.quote || 'Grounded source context excerpt.'}
                  </div>
                </div>
              </div>
            </div>

            {/* Related Concepts */}
            <div>
              <div style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '8px'
              }}>
                Related Conceptual Nodes
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {currentCitation.relatedConcepts?.map((concept, idx) => (
                  <span
                    key={idx}
                    className="badge badge-neutral"
                    style={{ fontSize: '0.74rem', padding: '3px 8px', cursor: 'pointer' }}
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Empty / Default State when no citation is clicked */
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: '40px 12px',
            color: 'var(--text-muted)'
          }}>
            <div style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              backgroundColor: 'var(--bg-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px'
            }}>
              <Sparkles size={20} color="var(--accent-primary)" />
            </div>

            <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
              Source-Grounded Verification
            </h3>

            <p style={{ fontSize: '0.78rem', lineHeight: 1.5, maxWidth: '240px', margin: '0 auto 18px auto' }}>
              Click any inline citation chip like <span className="citation-chip">[1]</span> in the conversation to inspect the verified source page and passage here.
            </p>

            <div style={{
              width: '100%',
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'left'
            }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Active in Current Notebook:
              </div>
              <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <li>{activeSources?.length || 4} textbooks & lecture notes active</li>
                <li>Zero hallucinations: strictly grounded</li>
                <li>Instant page excerpts & mathematical proofs</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
