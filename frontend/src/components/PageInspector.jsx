import React, { useState, useEffect } from 'react';
import { BookOpen, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, FileText, Image as ImageIcon } from 'lucide-react';

export default function PageInspector({ activeCitation }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [pages, setPages] = useState([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    if (activeCitation) {
      if (activeCitation.doc_id && activeCitation.doc_id !== selectedDocId) {
        setSelectedDocId(activeCitation.doc_id);
        fetchPages(activeCitation.doc_id, activeCitation.page_number - 1);
      } else if (activeCitation.page_number) {
        setCurrentPageIndex(Math.max(0, activeCitation.page_number - 1));
      }
    }
  }, [activeCitation]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/ingestion/documents');
      if (res.ok) {
        const docs = await res.json();
        setDocuments(docs);
        if (docs.length > 0 && !selectedDocId) {
          setSelectedDocId(docs[0].id);
          fetchPages(docs[0].id, 0);
        }
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const fetchPages = async (docId, targetPage = 0) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/ingestion/document/${docId}/pages`);
      if (res.ok) {
        const data = await res.json();
        setPages(data);
        setCurrentPageIndex(Math.min(targetPage, Math.max(0, data.length - 1)));
      }
    } catch (err) {
      console.error('Failed to load pages:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentPage = pages[currentPageIndex];

  return (
    <div className="glass-panel" style={{ height: 'calc(100vh - 110px)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Inspector Header */}
      <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BookOpen size={18} color="#6366F1" />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Visual Page Inspector</span>
          {documents.length > 0 && (
            <select
              value={selectedDocId}
              onChange={(e) => {
                setSelectedDocId(e.target.value);
                fetchPages(e.target.value, 0);
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-glass)',
                borderRadius: '6px',
                color: 'var(--text-main)',
                fontSize: '0.78rem',
                padding: '4px 8px',
                outline: 'none'
              }}
            >
              {documents.map((d) => (
                <option key={d.id} value={d.id} style={{ background: '#111827' }}>
                  {d.title} ({d.total_pages}p)
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Page Nav & Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            disabled={currentPageIndex <= 0}
            onClick={() => setCurrentPageIndex((prev) => Math.max(0, prev - 1))}
            className="btn-secondary"
            style={{ padding: '4px 8px' }}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {pages.length > 0 ? `Page ${currentPageIndex + 1} / ${pages.length}` : 'No pages'}
          </span>
          <button
            disabled={currentPageIndex >= pages.length - 1}
            onClick={() => setCurrentPageIndex((prev) => Math.min(pages.length - 1, prev + 1))}
            className="btn-secondary"
            style={{ padding: '4px 8px' }}
          >
            <ChevronRight size={16} />
          </button>

          <div style={{ width: '1px', height: '18px', background: 'var(--border-glass)', margin: '0 4px' }} />

          <button onClick={() => setZoomLevel((z) => Math.min(2.0, z + 0.15))} className="btn-secondary" style={{ padding: '4px 8px' }}>
            <ZoomIn size={16} />
          </button>
          <button onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.15))} className="btn-secondary" style={{ padding: '4px 8px' }}>
            <ZoomOut size={16} />
          </button>
        </div>
      </div>

      {/* Page Content Viewer */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px', display: 'flex', justifyContent: 'center', background: 'rgba(0, 0, 0, 0.2)' }}>
        {currentPage ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', width: '100%', maxWidth: `${650 * zoomLevel}px` }}>
            {currentPage.image_path ? (
              <img
                src={currentPage.image_path}
                alt={`Page ${currentPage.page_number}`}
                style={{
                  width: '100%',
                  borderRadius: '8px',
                  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.7)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}
              />
            ) : (
              /* Fallback rendered text page if no image available */
              <div
                style={{
                  width: '100%',
                  minHeight: '400px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-glass)',
                  borderRadius: '12px',
                  padding: '24px',
                  fontSize: '0.85rem',
                  lineHeight: '1.7',
                  color: 'var(--text-main)',
                  whiteSpace: 'pre-wrap'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: '#818CF8' }}>
                  <FileText size={18} />
                  <span style={{ fontWeight: 600 }}>Extracted Text • Page {currentPage.page_number}</span>
                </div>
                {currentPage.text_snippet || "No textual content available on this page."}
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: '10px' }}>
            <ImageIcon size={36} color="rgba(255,255,255,0.2)" />
            <p style={{ fontSize: '0.85rem' }}>No document pages loaded. Ingest a PDF to inspect pages side-by-side.</p>
          </div>
        )}
      </div>
    </div>
  );
}
