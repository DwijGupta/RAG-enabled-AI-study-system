import React, { useState, useEffect } from 'react';
import { X, Sparkles, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

export default function PracticeModal({ isOpen, onClose, conceptName, onStateUpdated }) {
  const [question, setQuestion] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [usedHint, setUsedHint] = useState(false);
  const [hintIndex, setHintIndex] = useState(-1);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && conceptName) {
      fetchQuestion(conceptName);
    } else if (isOpen) {
      fetchQuestion("Backpropagation & Chain Rule");
    }
  }, [isOpen, conceptName]);

  const fetchQuestion = async (targetConcept) => {
    setLoading(true);
    setQuestion(null);
    setSelectedOption(null);
    setEvaluation(null);
    setUsedHint(false);
    setHintIndex(-1);

    try {
      const res = await fetch('/api/assessment/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concept_name: targetConcept, difficulty: 0.5 })
      });
      if (res.ok) {
        const q = await res.json();
        setQuestion(q);
      }
    } catch (err) {
      console.error('Failed to generate question:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!question || selectedOption === null || submitting) return;

    setSubmitting(true);
    const chosenText = question.options[selectedOption];
    const correctText = question.options[question.correct_option_index];

    try {
      const res = await fetch('/api/assessment/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'student_1',
          concept_name: question.concept_name,
          question_text: question.question_text,
          student_answer: chosenText,
          correct_answer: correctText,
          used_hint: usedHint
        })
      });

      if (res.ok) {
        const result = await res.json();
        setEvaluation(result.evaluation);
        if (onStateUpdated) onStateUpdated();
      }
    } catch (err) {
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', position: 'relative' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={20} color="#F59E0B" />
            <h3 style={{ fontSize: '1.05rem' }}>Diagnostic Practice Problem</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {loading && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#A5B4FC' }}>
            <div className="animate-pulse-glow">Generating diagnostic question via Qwen 2.5...</div>
          </div>
        )}

        {question && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ fontSize: '0.8rem', color: '#818CF8', fontWeight: 600 }}>
              Testing Concept: {question.concept_name}
            </div>

            <div style={{ fontSize: '0.95rem', fontWeight: 600, lineHeight: '1.5', color: '#FFF' }}>
              {question.question_text}
            </div>

            {/* Options */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {question.options.map((opt, idx) => {
                const isSelected = selectedOption === idx;
                return (
                  <button
                    key={idx}
                    disabled={!!evaluation}
                    onClick={() => setSelectedOption(idx)}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      background: isSelected ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                      border: isSelected ? '1px solid #6366F1' : '1px solid var(--border-glass)',
                      color: 'var(--text-main)',
                      fontSize: '0.88rem',
                      textAlign: 'left',
                      cursor: evaluation ? 'default' : 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px'
                    }}
                  >
                    <span style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: isSelected ? '#6366F1' : 'rgba(255, 255, 255, 0.1)',
                      color: '#FFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700
                    }}>
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span style={{ flex: 1 }}>{opt}</span>
                  </button>
                );
              })}
            </div>

            {/* Hints Section */}
            {question.hints && question.hints.length > 0 && !evaluation && (
              <div style={{ marginTop: '8px' }}>
                {hintIndex >= 0 ? (
                  <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.12)', border: '1px solid rgba(6, 182, 212, 0.3)', color: '#22D3EE', fontSize: '0.82rem' }}>
                    💡 Hint: {question.hints[hintIndex]}
                  </div>
                ) : (
                  <button
                    onClick={() => { setUsedHint(true); setHintIndex(0); }}
                    style={{ background: 'none', border: 'none', color: '#06B6D4', fontSize: '0.78rem', cursor: 'pointer', textDecoration: 'underline' }}
                  >
                    Need a hint? (-10% mastery penalty)
                  </button>
                )}
              </div>
            )}

            {/* Evaluation Result */}
            {evaluation && (
              <div style={{
                padding: '16px',
                borderRadius: '12px',
                background: evaluation.is_correct ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)',
                border: evaluation.is_correct ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(244, 63, 94, 0.3)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: evaluation.is_correct ? '#10B981' : '#F43F5E', fontWeight: 700 }}>
                  {evaluation.is_correct ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                  <span>{evaluation.is_correct ? 'Correct! Concept Reinforced' : 'Incorrect • Misconception Diagnosed'}</span>
                </div>
                <p style={{ fontSize: '0.85rem', lineHeight: '1.5', color: 'var(--text-main)' }}>
                  {evaluation.feedback}
                </p>
                {evaluation.identified_misconception && (
                  <div style={{ fontSize: '0.78rem', color: '#C084FC', fontWeight: 600 }}>
                    Detected Trap: {evaluation.identified_misconception}
                  </div>
                )}
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  BKT Posterior mastery updated in Knowledge Graph.
                </div>
              </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              {!evaluation ? (
                <button
                  disabled={selectedOption === null || submitting}
                  onClick={handleSubmit}
                  className="btn-primary"
                  style={{ opacity: selectedOption === null || submitting ? 0.5 : 1 }}
                >
                  <span>Submit Answer</span>
                  <ArrowRight size={16} />
                </button>
              ) : (
                <button
                  onClick={() => fetchQuestion(question.concept_name)}
                  className="btn-primary"
                >
                  <span>Next Practice Question</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
