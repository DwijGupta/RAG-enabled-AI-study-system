import React, { useState } from 'react';
import { 
  UploadCloud, 
  X, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  FileCheck2, 
  Film, 
  Presentation,
  Globe,
  Loader2,
  Image as ImageIcon
} from 'lucide-react';

export default function UploadModal({
  isOpen,
  onClose,
  onAddSource
}) {
  const [dragActive, setDragActive] = useState(false);
  const [activeTab, setActiveTab] = useState('file'); // 'file' | 'link'
  const [urlInput, setUrlInput] = useState('');
  const [uploadQueue, setUploadQueue] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  if (!isOpen) return null;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const processUpload = async (file) => {
    setIsProcessing(true);
    const tempId = `upload-${Date.now()}`;
    const ext = file.name.split('.').pop().toLowerCase();
    
    let type = 'pdf';
    let label = 'Processing document...';
    if (['png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif'].includes(ext)) {
      type = 'image';
      label = 'Multimodal image parsing & OCR diagram extraction...';
    } else if (['pptx', 'ppt'].includes(ext)) {
      type = 'pptx';
    } else if (['docx', 'doc'].includes(ext)) {
      type = 'docx';
    } else if (['md', 'txt'].includes(ext)) {
      type = 'md';
    } else if (['mp4', 'mov'].includes(ext)) {
      type = 'video';
    }

    setUploadQueue([{
      id: tempId,
      name: file.name,
      type: type,
      status: 'processing',
      progressText: label
    }]);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '));

      // Visual step feedback
      setTimeout(() => {
        setUploadQueue(prev => prev.map(item => ({
          ...item,
          progressText: type === 'image' 
            ? 'Transcribing visual math equations & extracting concept graph...'
            : 'Extracting knowledge graph & prerequisite DAG...'
        })));
      }, 700);

      const response = await fetch('/api/ingestion/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Upload failed (Status ${response.status})`);
      }

      const data = await response.json();
      let res = data.result || {};

      // If async background job was queued (202 Accepted)
      if (data.status === 'queued' && data.job_id) {
        setUploadQueue(prev => prev.map(item => ({
          ...item,
          progressText: 'Queued in background worker...'
        })));

        res = await new Promise((resolve, reject) => {
          const interval = setInterval(async () => {
            try {
              const pollRes = await fetch(`/api/ingestion/status/${data.job_id}`);
              if (!pollRes.ok) {
                clearInterval(interval);
                return reject(new Error('Failed to retrieve processing status'));
              }
              const job = await pollRes.json();
              setUploadQueue(prev => prev.map(item => ({
                ...item,
                progressText: job.stage || 'Processing document...'
              })));

              if (job.status === 'completed') {
                clearInterval(interval);
                resolve(job.result || {});
              } else if (job.status === 'failed') {
                clearInterval(interval);
                reject(new Error(job.error || 'Ingestion failed'));
              }
            } catch (e) {
              clearInterval(interval);
              reject(e);
            }
          }, 750);
        });
      }

      setUploadQueue(prev => prev.map(item => ({
        ...item,
        status: 'ready',
        progressText: `Embedded ${res.chunks || 1} chunks & ${res.concepts_extracted || 0} graph concepts into Qdrant & BM25`
      })));

      const newSource = {
        id: res.document_id || tempId,
        name: res.title || file.name,
        type: res.source_type || type,
        pages: res.pages || 1,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        status: 'ready',
        active: true,
        addedDate: 'Just now',
        chunks: res.chunks,
        concepts: res.concepts_extracted
      };

      onAddSource(newSource);
      setTimeout(() => {
        setIsProcessing(false);
        onClose();
        setUploadQueue([]);
      }, 1000);

    } catch (err) {
      console.error('Upload error:', err);
      setUploadQueue(prev => prev.map(item => ({
        ...item,
        status: 'error',
        progressText: `Failed: ${err.message}`
      })));
      setIsProcessing(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      processUpload(e.target.files[0]);
    }
  };

  const handleUrlSubmit = async () => {
    if (!urlInput.trim() || isProcessing) return;
    setIsProcessing(true);
    const tempId = `url-${Date.now()}`;
    setUploadQueue([{
      id: tempId,
      name: urlInput.trim(),
      type: 'md',
      status: 'processing',
      progressText: 'Extracting content and building embeddings in real-time...'
    }]);

    try {
      const formData = new FormData();
      formData.append('url', urlInput.trim());

      const response = await fetch('/api/ingestion/import-url', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'URL import failed');
      }

      const data = await response.json();
      let res = data.result || {};

      if (data.status === 'queued' && data.job_id) {
        setUploadQueue(prev => prev.map(item => ({
          ...item,
          progressText: 'Queued in background worker...'
        })));

        res = await new Promise((resolve, reject) => {
          const interval = setInterval(async () => {
            try {
              const pollRes = await fetch(`/api/ingestion/status/${data.job_id}`);
              if (!pollRes.ok) {
                clearInterval(interval);
                return reject(new Error('Failed to retrieve processing status'));
              }
              const job = await pollRes.json();
              setUploadQueue(prev => prev.map(item => ({
                ...item,
                progressText: job.stage || 'Fetching and indexing web content...'
              })));

              if (job.status === 'completed') {
                clearInterval(interval);
                resolve(job.result || {});
              } else if (job.status === 'failed') {
                clearInterval(interval);
                reject(new Error(job.error || 'URL import failed'));
              }
            } catch (e) {
              clearInterval(interval);
              reject(e);
            }
          }, 750);
        });
      }

      setUploadQueue(prev => prev.map(item => ({
        ...item,
        status: 'ready',
        progressText: `Successfully indexed ${res.chunks || 1} chunks into Qdrant & BM25`
      })));

      const newSource = {
        id: res.document_id || tempId,
        name: res.title || urlInput.trim(),
        type: res.source_type || 'md',
        pages: res.pages || 1,
        size: 'Web Article',
        status: 'ready',
        active: true,
        addedDate: 'Just now'
      };

      onAddSource(newSource);
      setTimeout(() => {
        setIsProcessing(false);
        onClose();
        setUploadQueue([]);
      }, 1000);

    } catch (err) {
      setUploadQueue(prev => prev.map(item => ({
        ...item,
        status: 'error',
        progressText: `Failed: ${err.message}`
      })));
      setIsProcessing(false);
    }
  };


  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '580px' }}>
        {/* Modal Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Add Study Materials to Notebook
            </h2>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Grounds your AI tutor with citation-backed explanations
            </div>
          </div>

          <button onClick={onClose} className="btn-icon">
            <X size={16} />
          </button>
        </div>

        {/* Tab Toggle */}
        <div style={{ padding: '12px 20px 0 20px', display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('file')}
            className={`btn btn-sm ${activeTab === 'file' ? 'btn-primary' : 'btn-ghost'}`}
          >
            <FileText size={14} />
            <span>Upload Documents</span>
          </button>
          <button
            onClick={() => setActiveTab('link')}
            className={`btn btn-sm ${activeTab === 'link' ? 'btn-primary' : 'btn-ghost'}`}
          >
            <Globe size={14} />
            <span>Web or Video Link</span>
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '20px' }}>
          {activeTab === 'file' ? (
            <div>
              {/* Drag & Drop Area */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                style={{
                  border: `2px dashed ${dragActive ? 'var(--accent-primary)' : 'var(--border-strong)'}`,
                  borderRadius: '10px',
                  backgroundColor: dragActive ? 'var(--accent-primary-subtle)' : 'var(--bg-subtle)',
                  padding: '36px 20px',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onClick={() => document.getElementById('studybuddy-file-input').click()}
              >
                <input
                  id="studybuddy-file-input"
                  type="file"
                  multiple
                  style={{ display: 'none' }}
                  onChange={handleFileSelect}
                  accept=".pdf,.png,.jpg,.jpeg,.webp,.bmp,.docx,.pptx,.txt,.md,.mp4"
                />

                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--bg-surface)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '12px',
                  boxShadow: 'var(--shadow-xs)'
                }}>
                  <UploadCloud size={24} color="var(--accent-primary)" />
                </div>

                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                  Drag and drop study files here, or <span style={{ color: 'var(--accent-primary)' }}>browse</span>
                </div>

                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                  Supported formats: <strong>Images (PNG, JPG, WEBP diagram snapshots)</strong>, PDF textbooks, DOCX notes, PPT slides, Markdown
                </div>
              </div>

              {/* Ingestion Info Tips */}
              <div style={{ marginTop: '16px' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  ⚡ Real-time Multimodal Pipeline:
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.74rem',
                  color: 'var(--text-secondary)'
                }}>
                  <ImageIcon size={14} color="var(--accent-primary)" />
                  <span>Images are automatically parsed with multimodal OCR, LaTeX equations, and diagram concept extraction in real time.</span>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'block', marginBottom: '6px' }}>
                  Web Documentation or YouTube Lecture URL
                </label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="url"
                    placeholder="https://arxiv.org/abs/... or YouTube link"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    className="input-field"
                    style={{ flex: 1 }}
                  />
                  <button
                    onClick={handleUrlSubmit}
                    disabled={!urlInput.trim() || isProcessing}
                    className="btn btn-primary btn-sm"
                  >
                    Import
                  </button>
                </div>
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                AI Study Buddy System extracts text transcripts and structured sections while stripping web ads and boilerplates.
              </div>
            </div>
          )}

          {/* Processing Queue Feedback */}
          {uploadQueue.length > 0 && (
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {uploadQueue.map((item, idx) => (
                <div key={idx} style={{
                  padding: '12px 14px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-default)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {item.status === 'processing' ? (
                      <Loader2 size={16} color="var(--accent-primary)" style={{ animation: 'spin 1s linear infinite' }} />
                    ) : (
                      <CheckCircle2 size={16} color="var(--status-success-badge)" />
                    )}
                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {item.name}
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {item.progressText}
                      </div>
                    </div>
                  </div>

                  <span className={`badge ${item.status === 'ready' ? 'badge-success' : 'badge-neutral'}`} style={{ fontSize: '0.7rem' }}>
                    {item.status === 'ready' ? 'Complete' : 'Processing'}
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
