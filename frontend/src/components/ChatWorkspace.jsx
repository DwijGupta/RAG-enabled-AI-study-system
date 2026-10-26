import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, BookOpen, AlertTriangle, CheckCircle, ArrowRight, CornerDownLeft } from 'lucide-react';

export default function ChatWorkspace({ onSelectCitation, onPracticeConcept }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello Alex! I am your AI Study Buddy. I monitor your conceptual understanding using Bayesian Knowledge Tracing, diagnose prerequisite bottlenecks, and guide you through your optimal Zone of Proximal Development (ZPD).\n\nWhat topic or problem would you like to explore today?",
      planner_action: 'EXPLAIN',
      citations: [],
      faithfulness_score: 1.0,
      diagnosed_weakness: null
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText = null) => {
    const q = queryText || inputQuery;
    if (!q.trim() || loading) return;

    const userMessage = { role: 'user', content: q };
    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'student_1',
          session_id: 'session_demo_1',
          query: q
        })
      });

      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        planner_action: data.planner_action,
        rationale: data.rationale,
        citations: data.citations || [],
        faithfulness_score: data.faithfulness_score,
        diagnosed_weakness: data.diagnosed_weakness
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "I encountered a problem connecting to the local tutoring pipeline. Please verify Ollama is active on port 11434.",
          planner_action: 'EXPLAIN',
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getActionBadgeClass = (action) => {
    switch (action?.toUpperCase()) {
      case 'SOCRATIC': return 'badge-socratic';
      case 'HINT': return 'badge-hint';
      case 'REMEDIATE': return 'badge-remediate';
      case 'QUIZ': return 'badge-quiz';
      default: return 'badge-explain';
    }
  };

  return (
    <div className="glass-panel" style={{ height: 'calc(100vh - 110px)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Chat Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10B981', boxShadow: '0 0 10px #10B981' }} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Socratic Tutoring Stream</span>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Adaptive Scaffolding Enabled</span>
      </div>

      {/* Message List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              gap: '14px',
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: msg.role === 'user' ? '80%' : '90%'
            }}
          >
            {msg.role === 'assistant' && (
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
              }}>
                <Bot size={20} color="#FFF" />
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* Tutor Policy Indicator */}
              {msg.role === 'assistant' && msg.planner_action && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge ${getActionBadgeClass(msg.planner_action)}`}>
                    {msg.planner_action}
                  </span>
                  {msg.diagnosed_weakness && (
                    <span style={{
                      fontSize: '0.75rem',
                      color: '#FB7185',
                      background: 'rgba(244, 63, 94, 0.12)',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid rgba(244, 63, 94, 0.3)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      <AlertTriangle size={12} />
                      Prerequisite Gap: {msg.diagnosed_weakness}
                    </span>
                  )}
                  {msg.faithfulness_score !== undefined && (
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle size={12} color="#10B981" />
                      Faithfulness: {Math.round(msg.faithfulness_score * 100)}%
                    </span>
                  )}
                </div>
              )}

              {/* Message Bubble */}
              <div
                style={{
                  padding: '16px 18px',
                  borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  background: msg.role === 'user'
                    ? 'linear-gradient(135deg, #4F46E5 0%, #6366F1 100%)'
                    : 'rgba(255, 255, 255, 0.04)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  lineHeight: '1.6',
                  whiteSpace: 'pre-wrap'
                }}
              >
                {msg.content}
              </div>

              {/* Interactive Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>Sources:</span>
                  {msg.citations.map((c, cIdx) => (
                    <button
                      key={cIdx}
                      onClick={() => onSelectCitation(c)}
                      style={{
                        background: 'rgba(99, 102, 241, 0.12)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        borderRadius: '6px',
                        padding: '4px 8px',
                        color: '#A5B4FC',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(99, 102, 241, 0.25)'; }}
                      onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(99, 102, 241, 0.12)'; }}
                    >
                      <BookOpen size={12} />
                      <span>{c.cite_id}: Page {c.page_number}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <User size={20} color="#FFF" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={20} color="#818CF8" />
            </div>
            <div style={{ padding: '12px 18px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="animate-pulse-glow" style={{ fontSize: '0.85rem', color: '#A5B4FC' }}>
                Analyzing intent & traversing prerequisite graph...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div style={{ padding: '8px 20px', display: 'flex', gap: '8px', overflowX: 'auto', borderTop: '1px solid rgba(255, 255, 255, 0.04)' }}>
        {[
          "Why do we need activation functions?",
          "How does backpropagation use the chain rule?",
          "Give me a Socratic hint on attention matrices",
          "Test my understanding of dot products"
        ].map((prompt, pIdx) => (
          <button
            key={pIdx}
            onClick={() => handleSend(prompt)}
            style={{
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '9999px',
              padding: '4px 12px',
              color: 'var(--text-muted)',
              fontSize: '0.75rem',
              whiteSpace: 'nowrap',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => { e.currentTarget.style.color = '#FFF'; e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)'; }}
            onMouseOut={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'; }}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-glass)' }}>
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          style={{ display: 'flex', gap: '10px', alignItems: 'center' }}
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask a question or explain your reasoning..."
            style={{
              flex: 1,
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-glass)',
              borderRadius: '12px',
              padding: '12px 16px',
              color: 'var(--text-main)',
              fontSize: '0.9rem',
              outline: 'none',
              fontFamily: 'var(--font-sans)'
            }}
            onFocus={(e) => { e.target.style.borderColor = 'var(--primary)'; }}
            onBlur={(e) => { e.target.style.borderColor = 'var(--border-glass)'; }}
          />
          <button
            type="submit"
            disabled={loading || !inputQuery.trim()}
            className="btn-primary"
            style={{ padding: '12px 20px', borderRadius: '12px', opacity: (loading || !inputQuery.trim()) ? 0.5 : 1 }}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
