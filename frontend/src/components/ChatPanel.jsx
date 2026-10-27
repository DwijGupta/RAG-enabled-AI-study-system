import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Paperclip, 
  Sparkles, 
  RotateCcw, 
  Copy, 
  ThumbsUp, 
  ThumbsDown, 
  Check, 
  Search, 
  PlusCircle, 
  MoreHorizontal,
  Lightbulb,
  CheckCircle,
  HelpCircle,
  Share2,
  Trash2,
  PanelLeft,
  PanelRight
} from 'lucide-react';
import { citationsDatabase, tutorModes } from '../data/mockData.js';

export default function ChatPanel({
  notebookTitle = 'Active Study Session',
  messages,
  onSendMessage,
  onSelectCitation,
  activeCitationId,
  tutorMode,
  setTutorMode,
  activeSourcesCount,
  onOpenUpload,
  isGenerating,
  onClearChat,
  onDeleteMessage,
  isSourcesOpen,
  onToggleSources,
  isEvidenceOpen,
  onToggleEvidence
}) {
  const [inputValue, setInputValue] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const [userRatings, setUserRatings] = useState({});
  const [quizAnswers, setQuizAnswers] = useState({});
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isGenerating]);

  const handleSend = () => {
    if (!inputValue.trim() || isGenerating) return;
    onSendMessage(inputValue.trim());
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRate = (id, rating) => {
    setUserRatings((prev) => ({ ...prev, [id]: rating }));
  };

  const handleQuizSelect = (msgId, optIndex) => {
    setQuizAnswers((prev) => ({ ...prev, [msgId]: optIndex }));
  };

  const renderFormattedContent = (content, citations = []) => {
    // Replace citation tags like [cit-1], [Doc 1], [REF-1], [REF-1: p. 4] with interactive citation chips
    const parts = content.split(/(\[(?:cit-\d+|Doc \d+(?::[^\]]+)?|REF-\d+(?::[^\]]+)?)\])/gi);

    return parts.map((part, index) => {
      const citMatch = part.match(/\[(cit-\d+|Doc \d+(?::[^\]]+)?|REF-\d+(?::[^\]]+)?)\]/i);
      if (citMatch) {
        const fullTag = citMatch[1];
        const numMatch = fullTag.match(/\d+/);
        const idx = numMatch ? parseInt(numMatch[0], 10) : 1;

        // Resolve matching citation from message's citations array or mock database
        let citData = null;
        if (citations && citations.length >= idx) {
          citData = citations[idx - 1];
        } else if (citationsDatabase[`cit-${idx}`]) {
          citData = citationsDatabase[`cit-${idx}`];
        } else if (citations && citations.length > 0) {
          citData = citations[0];
        }

        const label = citData?.cite_id || citData?.shortLabel || `[Doc ${idx}]`;
        const docName = citData?.doc_title || citData?.sourceName || 'Source';
        const pageNum = citData?.page_number || citData?.pageNumber || 1;
        const isActive = activeCitationId === citData || activeCitationId === `cit-${idx}`;

        return (
          <button
            key={index}
            onClick={() => onSelectCitation(citData || `cit-${idx}`)}
            className={`citation-chip ${isActive ? 'active' : ''}`}
            title={`Click to inspect source excerpt: ${docName} (Page ${pageNum})`}
          >
            <span>{label}</span>
            <span style={{ opacity: 0.85, fontSize: '0.68rem' }}>
              {docName.length > 16 ? docName.substring(0, 16) + '...' : docName}, p.{pageNum}
            </span>
          </button>
        );
      }

      // Check if it's a section header or bullet point
      const lines = part.split('\n');
      return (
        <span key={index}>
          {lines.map((line, lIdx) => {
            if (line.startsWith('### ')) {
              return (
                <h3 key={lIdx} style={{ fontSize: '0.98rem', fontWeight: 600, marginTop: '14px', marginBottom: '6px', color: 'var(--text-primary)' }}>
                  {line.replace('### ', '')}
                </h3>
              );
            }
            if (line.startsWith('---')) {
              return <hr key={lIdx} style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '14px 0' }} />;
            }
            if (line.startsWith('$$') && line.endsWith('$$')) {
              return (
                <div key={lIdx} style={{
                  padding: '8px 14px',
                  margin: '8px 0',
                  borderRadius: '6px',
                  backgroundColor: 'var(--code-bg)',
                  border: '1px solid var(--code-border)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.86rem',
                  color: 'var(--code-text)',
                  overflowX: 'auto'
                }}>
                  {line.replace(/\$\$/g, '')}
                </div>
              );
            }
            return (
              <React.Fragment key={lIdx}>
                {line}
                {lIdx < lines.length - 1 && <br />}
              </React.Fragment>
            );
          })}
        </span>
      );
    });
  };

  const suggestedPrompts = [
    'Explain the core concepts step by step',
    'Summarize key formulas and definitions',
    'Test my understanding with an exam-style question',
    'Give me a concrete real-world example'
  ];

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: 'var(--bg-app)',
      position: 'relative',
      minWidth: 0
    }}>
      {/* Chat Workspace Subheader */}
      <div style={{
        height: '46px',
        padding: '0 20px',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {notebookTitle}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>•</span>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Session grounded in {activeSourcesCount} sources
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {!isSourcesOpen && onToggleSources && (
            <button 
              onClick={onToggleSources}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.74rem', padding: '4px 8px' }}
              title="Expand Sources panel"
            >
              <PanelLeft size={13} color="var(--accent-primary)" />
              <span>Sources</span>
            </button>
          )}

          {!isEvidenceOpen && onToggleEvidence && (
            <button 
              onClick={onToggleEvidence}
              className="btn btn-secondary btn-sm"
              style={{ fontSize: '0.74rem', padding: '4px 8px' }}
              title="Expand Evidence panel"
            >
              <PanelRight size={13} color="var(--accent-primary)" />
              <span>Evidence</span>
            </button>
          )}

          <button 
            onClick={() => onSendMessage('Test my understanding with a conceptual question')}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: '0.74rem', padding: '4px 8px' }}
          >
            <Lightbulb size={13} color="var(--accent-primary)" />
            <span>Quiz me</span>
          </button>
          <button 
            onClick={() => onSendMessage('Explain this in simpler terms with another real-world analogy')}
            className="btn btn-ghost btn-sm"
            style={{ fontSize: '0.74rem', padding: '4px 8px' }}
          >
            <span>Simplify</span>
          </button>

          {onClearChat && (
            <button 
              onClick={() => {
                if (window.confirm("Clear this conversation's memory and start fresh?")) {
                  onClearChat();
                }
              }}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: '0.74rem', padding: '4px 8px', color: 'var(--status-danger-badge)' }}
              title="Clear chat memory"
            >
              <Trash2 size={13} />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 20px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <div style={{ width: '100%', maxWidth: '780px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';

            if (isUser) {
              return (
                <div key={msg.id} style={{
                  display: 'flex',
                  justifyContent: 'flex-end',
                  width: '100%'
                }}>
                  <div style={{
                    maxWidth: '85%',
                    backgroundColor: 'var(--accent-primary-subtle)',
                    border: '1px solid var(--accent-primary-border)',
                    borderRadius: '12px 12px 2px 12px',
                    padding: '12px 16px',
                    color: 'var(--text-primary)',
                    fontSize: '0.88rem',
                    lineHeight: 1.5,
                    boxShadow: 'var(--shadow-xs)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px', gap: '12px' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--accent-primary-text)' }}>
                        You (Student)
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                          {msg.timestamp}
                        </span>
                        {onDeleteMessage && (
                          <button
                            onClick={() => onDeleteMessage(msg.id, msg.trace_id)}
                            className="btn-icon"
                            style={{ width: '18px', height: '18px', padding: 0, opacity: 0.7 }}
                            title="Delete message"
                          >
                            <Trash2 size={11} color="var(--status-danger-badge)" />
                          </button>
                        )}
                      </div>
                    </div>
                    {msg.content}
                  </div>
                </div>
              );
            }

            // Tutor Response Card
            return (
              <div key={msg.id} style={{
                display: 'flex',
                flexDirection: 'column',
                width: '100%',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: '12px',
                padding: '18px 20px',
                boxShadow: 'var(--shadow-xs)'
              }}>
                {/* Tutor Header */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: '12px',
                  borderBottom: '1px solid var(--border-subtle)',
                  marginBottom: '14px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '6px',
                      backgroundColor: 'var(--accent-primary)',
                      color: '#FFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Sparkles size={13} />
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                      AI Study Buddy System Tutor
                    </span>
                    <span className="badge badge-info" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>
                      {msg.mode || tutorMode} mode
                    </span>
                  </div>

                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    {msg.timestamp}
                  </span>
                </div>

                {/* Formatted Content */}
                <div style={{
                  color: 'var(--text-primary)',
                  fontSize: '0.88rem',
                  lineHeight: 1.65,
                  letterSpacing: '-0.005em'
                }}>
                  {renderFormattedContent(msg.content, msg.citations)}
                </div>

                {/* Embedded Quick Check / Quiz Question if present */}
                {msg.quizQuestion && (
                  <div style={{
                    marginTop: '16px',
                    padding: '14px 16px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-subtle)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                      <HelpCircle size={15} color="var(--accent-primary)" />
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {msg.quizQuestion.question}
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '10px' }}>
                      {msg.quizQuestion.options.map((opt, optIdx) => {
                        const isSelected = quizAnswers[msg.id] === optIdx;
                        const isAnswered = quizAnswers[msg.id] !== undefined;
                        const isCorrect = optIdx === msg.quizQuestion.correctIndex;

                        let btnBg = 'var(--bg-surface)';
                        let btnBorder = 'var(--border-default)';
                        let btnColor = 'var(--text-secondary)';

                        if (isAnswered) {
                          if (isCorrect) {
                            btnBg = 'var(--status-success-bg)';
                            btnBorder = 'var(--status-success-border)';
                            btnColor = 'var(--status-success-text)';
                          } else if (isSelected) {
                            btnBg = 'var(--status-danger-bg)';
                            btnBorder = 'var(--status-danger-border)';
                            btnColor = 'var(--status-danger-text)';
                          }
                        }

                        return (
                          <button
                            key={optIdx}
                            onClick={() => !isAnswered && handleQuizSelect(msg.id, optIdx)}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '8px 12px',
                              borderRadius: '6px',
                              border: `1px solid ${btnBorder}`,
                              backgroundColor: btnBg,
                              color: btnColor,
                              fontSize: '0.8rem',
                              textAlign: 'left',
                              cursor: isAnswered ? 'default' : 'pointer',
                              transition: 'all 0.15s ease'
                            }}
                          >
                            <span>{opt}</span>
                            {isAnswered && isCorrect && <CheckCircle size={14} color="var(--status-success-badge)" />}
                          </button>
                        );
                      })}
                    </div>

                    {quizAnswers[msg.id] !== undefined && (
                      <div style={{
                        marginTop: '10px',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        fontSize: '0.74rem',
                        backgroundColor: quizAnswers[msg.id] === msg.quizQuestion.correctIndex ? 'var(--status-success-bg)' : 'var(--status-warning-bg)',
                        color: quizAnswers[msg.id] === msg.quizQuestion.correctIndex ? 'var(--status-success-text)' : 'var(--status-warning-text)',
                        border: '1px solid',
                        borderColor: quizAnswers[msg.id] === msg.quizQuestion.correctIndex ? 'var(--status-success-border)' : 'var(--status-warning-border)'
                      }}>
                        <strong>{quizAnswers[msg.id] === msg.quizQuestion.correctIndex ? 'Correct!' : 'Keep in mind:'}</strong>{' '}
                        {msg.quizQuestion.explanation}
                      </div>
                    )}
                  </div>
                )}

                {/* Footer Actions: Copy, Thumbs, Quick Prompts */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: '12px',
                  marginTop: '16px',
                  borderTop: '1px solid var(--border-subtle)',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button
                      onClick={() => handleCopy(msg.id, msg.content)}
                      className="btn-icon"
                      style={{ width: '26px', height: '26px' }}
                      title="Copy response"
                    >
                      {copiedId === msg.id ? <Check size={13} color="var(--status-success-badge)" /> : <Copy size={13} />}
                    </button>
                    <button
                      onClick={() => handleRate(msg.id, 'up')}
                      className="btn-icon"
                      style={{ width: '26px', height: '26px', color: userRatings[msg.id] === 'up' ? 'var(--accent-primary)' : 'inherit' }}
                      title="Helpful"
                    >
                      <ThumbsUp size={13} />
                    </button>
                    <button
                      onClick={() => handleRate(msg.id, 'down')}
                      className="btn-icon"
                      style={{ width: '26px', height: '26px', color: userRatings[msg.id] === 'down' ? 'var(--status-danger-badge)' : 'inherit' }}
                      title="Not helpful"
                    >
                      <ThumbsDown size={13} />
                    </button>
                    {onDeleteMessage && (
                      <button
                        onClick={() => onDeleteMessage(msg.id, msg.trace_id)}
                        className="btn-icon"
                        style={{ width: '26px', height: '26px', color: 'var(--status-danger-badge)' }}
                        title="Delete message"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <button 
                      onClick={() => onSendMessage('Explain this in simpler terms with another analogy')}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                    >
                      Explain more simply
                    </button>
                    <button 
                      onClick={() => onSendMessage('Show me another worked example')}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                    >
                      Another example
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Streaming / Generating State */}
          {isGenerating && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '12px 18px',
              borderRadius: '10px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              boxShadow: 'var(--shadow-xs)',
              width: '100%'
            }}>
              <span className="pulse-dot" />
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Synthesizing explanation from <strong>{activeSourcesCount} active sources</strong> & verifying grounded citations...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Suggested Prompts Pills */}
      <div style={{
        padding: '0 20px 8px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        flexWrap: 'wrap',
        maxWidth: '820px',
        margin: '0 auto',
        width: '100%'
      }}>
        {suggestedPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => onSendMessage(prompt)}
            className="btn btn-secondary btn-sm"
            style={{
              fontSize: '0.74rem',
              padding: '4px 10px',
              borderRadius: '9999px',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              color: 'var(--text-secondary)'
            }}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Fixed Composer Bottom Dock */}
      <div style={{
        padding: '12px 20px 16px 20px',
        backgroundColor: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-default)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        flexShrink: 0
      }}>
        <div style={{
          width: '100%',
          maxWidth: '780px',
          border: '1px solid var(--border-default)',
          borderRadius: '10px',
          backgroundColor: 'var(--bg-app)',
          boxShadow: 'var(--shadow-sm)',
          overflow: 'hidden',
          transition: 'border-color 0.15s ease'
        }}>
          {/* Multiline Input Textarea */}
          <textarea
            ref={textareaRef}
            rows={2}
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
            }}
            onKeyDown={handleKeyDown}
            placeholder={`Ask AI Study Buddy System anything about your active materials... (Enter to send, Shift+Enter for newline)`}
            style={{
              width: '100%',
              padding: '12px 14px',
              border: 'none',
              backgroundColor: 'transparent',
              color: 'var(--text-primary)',
              fontFamily: 'inherit',
              fontSize: '0.88rem',
              lineHeight: 1.5,
              resize: 'none',
              outline: 'none'
            }}
          />

          {/* Composer Controls Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 12px 8px 12px',
            backgroundColor: 'var(--bg-app)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={onOpenUpload}
                className="btn-icon"
                style={{ width: '28px', height: '28px' }}
                title="Attach or upload new source material"
              >
                <Paperclip size={15} />
              </button>

              <div style={{
                fontSize: '0.72rem',
                color: 'var(--text-muted)',
                backgroundColor: 'var(--bg-surface)',
                padding: '2px 8px',
                borderRadius: '5px',
                border: '1px solid var(--border-subtle)'
              }}>
                {activeSourcesCount} sources active
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>
                Press ↵ to send
              </span>
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isGenerating}
                className="btn btn-primary btn-sm"
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  opacity: !inputValue.trim() || isGenerating ? 0.5 : 1,
                  cursor: !inputValue.trim() || isGenerating ? 'not-allowed' : 'pointer'
                }}
              >
                <Send size={13} />
                <span>Send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
