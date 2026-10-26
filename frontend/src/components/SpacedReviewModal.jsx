import React, { useState, useEffect } from 'react';
import { X, Layers, RotateCw, Check, Clock } from 'lucide-react';

export default function SpacedReviewModal({ isOpen, onClose, onCardsUpdated }) {
  const [cards, setCards] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchDueCards();
    }
  }, [isOpen]);

  const fetchDueCards = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/review/due?user_id=student_1');
      if (res.ok) {
        const data = await res.json();
        setCards(data.due_cards || []);
        setCurrentIndex(0);
        setShowAnswer(false);
      }
    } catch (err) {
      console.error('Failed to load due cards:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRate = async (rating) => {
    const currentCard = cards[currentIndex];
    if (!currentCard) return;

    try {
      await fetch('/api/review/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: currentCard.id, rating })
      });

      if (currentIndex + 1 < cards.length) {
        setCurrentIndex((prev) => prev + 1);
        setShowAnswer(false);
      } else {
        // All completed
        setCards([]);
        if (onCardsUpdated) onCardsUpdated();
      }
    } catch (err) {
      console.error('Rate error:', err);
    }
  };

  if (!isOpen) return null;

  const currentCard = cards[currentIndex];

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
      <div className="glass-panel" style={{ width: '100%', maxWidth: '550px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Layers size={20} color="#06B6D4" />
            <h3 style={{ fontSize: '1.05rem' }}>FSRS Spaced Repetition Practice</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {currentCard ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              <span>Card {currentIndex + 1} of {cards.length}</span>
              <span>Memory Stability: {currentCard.stability.toFixed(1)}d • Retrievability: {Math.round(currentCard.retrievability * 100)}%</span>
            </div>

            {/* Flashcard Body */}
            <div
              style={{
                minHeight: '200px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border-glass)',
                borderRadius: '16px',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                textAlign: 'center',
                gap: '16px',
                boxShadow: 'inset 0 0 20px rgba(0, 0, 0, 0.3)'
              }}
            >
              <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#FFF' }}>
                {currentCard.question}
              </div>

              {showAnswer ? (
                <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', color: '#A5B4FC', fontSize: '0.92rem', lineHeight: '1.6' }}>
                  {currentCard.answer}
                  {currentCard.explanation && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                      {currentCard.explanation}
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => setShowAnswer(true)}
                  className="btn-secondary"
                  style={{ alignSelf: 'center', marginTop: '10px' }}
                >
                  <RotateCw size={14} />
                  <span>Reveal Answer</span>
                </button>
              )}
            </div>

            {/* FSRS Rating Buttons */}
            {showAnswer && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginTop: '8px' }}>
                <button
                  onClick={() => handleRate(1)}
                  style={{ padding: '10px 4px', borderRadius: '8px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FB7185', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Again (12h)
                </button>
                <button
                  onClick={() => handleRate(2)}
                  style={{ padding: '10px 4px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#FBBF24', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Hard (1.5d)
                </button>
                <button
                  onClick={() => handleRate(3)}
                  style={{ padding: '10px 4px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#818CF8', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Good (3d)
                </button>
                <button
                  onClick={() => handleRate(4)}
                  style={{ padding: '10px 4px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#34D399', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Easy (7d)
                </button>
              </div>
            )}
          </div>
        ) : (
          <div style={{ padding: '30px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <Check size={36} color="#10B981" />
            <div style={{ fontSize: '1.05rem', fontWeight: 600 }}>All Caught Up!</div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              No cards are currently due for spaced review. New cards will appear as forgetting decay progresses.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
