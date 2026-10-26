import React, { useState } from 'react';
import { 
  BookOpen, 
  Layers, 
  CheckCircle2, 
  FileText, 
  RotateCw, 
  ChevronLeft, 
  ChevronRight, 
  Shuffle, 
  Check, 
  AlertCircle, 
  Award,
  Sparkles,
  Download,
  Copy
} from 'lucide-react';
import { mockStudyGuide, mockFlashcards, mockQuizQuestions } from '../data/mockData.js';

export default function StudyToolsView({
  initialTab = 'study-guide',
  onClose,
  notebookTitle = 'Machine Learning Fundamentals'
}) {
  const [activeTab, setActiveTab] = useState(initialTab);

  // Flashcards State
  const [cards, setCards] = useState(mockFlashcards);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [cardStats, setCardStats] = useState({ known: 0, review: 0 });

  // Quiz State
  const [quizQuestions, setQuizQuestions] = useState(mockQuizQuestions);
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizFinished, setQuizFinished] = useState(false);
  const [quizScore, setQuizScore] = useState(0);

  // Flashcard Handlers
  const handleNextCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex((prev) => (prev + 1) % cards.length);
  };

  const handlePrevCard = () => {
    setIsFlipped(false);
    setCurrentCardIndex((prev) => (prev - 1 + cards.length) % cards.length);
  };

  const handleShuffle = () => {
    setIsFlipped(false);
    const shuffled = [...cards].sort(() => Math.random() - 0.5);
    setCards(shuffled);
    setCurrentCardIndex(0);
  };

  const handleCardFeedback = (status) => {
    setCardStats((prev) => ({
      ...prev,
      [status === 'known' ? 'known' : 'review']: prev[status === 'known' ? 'known' : 'review'] + 1
    }));
    handleNextCard();
  };

  // Quiz Handlers
  const handleSelectAnswer = (qIndex, optIndex) => {
    if (selectedAnswers[qIndex] !== undefined) return;
    const newAnswers = { ...selectedAnswers, [qIndex]: optIndex };
    setSelectedAnswers(newAnswers);

    if (optIndex === quizQuestions[qIndex].correctIndex) {
      setQuizScore((prev) => prev + 1);
    }
  };

  const handleNextQuizQuestion = () => {
    if (currentQuizIndex < quizQuestions.length - 1) {
      setCurrentQuizIndex((prev) => prev + 1);
    } else {
      setQuizFinished(true);
    }
  };

  const handleRestartQuiz = () => {
    setSelectedAnswers({});
    setCurrentQuizIndex(0);
    setQuizScore(0);
    setQuizFinished(false);
  };

  const currentCard = cards[currentCardIndex];
  const currentQuiz = quizQuestions[currentQuizIndex];

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      backgroundColor: 'var(--bg-app)',
      padding: '24px 32px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }}>
      <div style={{ width: '100%', maxWidth: '940px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Top Header & Tab Navigation */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-default)',
          paddingBottom: '16px'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              {notebookTitle}
            </div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Interactive Study Tools
            </h1>
          </div>

          {/* Tab Selector */}
          <div style={{
            display: 'flex',
            gap: '4px',
            backgroundColor: 'var(--bg-surface)',
            padding: '4px',
            borderRadius: '9px',
            border: '1px solid var(--border-default)'
          }}>
            <button
              onClick={() => setActiveTab('study-guide')}
              className={`btn btn-sm ${activeTab === 'study-guide' ? 'btn-primary' : 'btn-ghost'}`}
            >
              <BookOpen size={14} />
              <span>Study Guide</span>
            </button>
            <button
              onClick={() => setActiveTab('flashcards')}
              className={`btn btn-sm ${activeTab === 'flashcards' ? 'btn-primary' : 'btn-ghost'}`}
            >
              <Layers size={14} />
              <span>Flashcards</span>
            </button>
            <button
              onClick={() => setActiveTab('quiz')}
              className={`btn btn-sm ${activeTab === 'quiz' ? 'btn-primary' : 'btn-ghost'}`}
            >
              <CheckCircle2 size={14} />
              <span>Practice Quiz</span>
            </button>
          </div>
        </div>

        {/* TAB 1: STUDY GUIDE */}
        {activeTab === 'study-guide' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-default)',
              borderRadius: '12px',
              padding: '28px',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {mockStudyGuide.title}
                  </h2>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Auto-generated from 4 verified sources • {mockStudyGuide.lastUpdated}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-secondary btn-sm">
                    <Copy size={13} />
                    <span>Copy</span>
                  </button>
                  <button className="btn btn-secondary btn-sm">
                    <Download size={13} />
                    <span>Export PDF</span>
                  </button>
                </div>
              </div>

              {/* Sections */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* 1. Overview */}
                <div>
                  <h3 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                    {mockStudyGuide.sections[0].title}
                  </h3>
                  <p style={{ fontSize: '0.86rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                    {mockStudyGuide.sections[0].content}
                  </p>
                </div>

                {/* 2. Key Concepts */}
                <div>
                  <h3 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {mockStudyGuide.sections[1].title}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {mockStudyGuide.sections[1].items?.map((item, idx) => (
                      <div key={idx} style={{
                        padding: '10px 14px',
                        borderRadius: '8px',
                        backgroundColor: 'var(--bg-subtle)',
                        border: '1px solid var(--border-subtle)'
                      }}>
                        <strong style={{ color: 'var(--text-primary)', fontSize: '0.84rem' }}>{item.term}:</strong>{' '}
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{item.desc}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Equations */}
                <div>
                  <h3 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {mockStudyGuide.sections[2].title}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {mockStudyGuide.sections[2].equations?.map((eq, idx) => (
                      <div key={idx} style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        backgroundColor: 'var(--code-bg)',
                        border: '1px solid var(--code-border)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px'
                      }}>
                        <span style={{ fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                          {eq.name}
                        </span>
                        <code style={{ fontSize: '0.88rem', color: 'var(--code-text)', fontWeight: 500 }}>
                          {eq.eq}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 4. Common Misconceptions */}
                <div>
                  <h3 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {mockStudyGuide.sections[3].title}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {mockStudyGuide.sections[3].misconceptions?.map((misc, idx) => (
                      <div key={idx} style={{
                        padding: '12px 14px',
                        borderRadius: '8px',
                        backgroundColor: 'var(--status-warning-bg)',
                        border: '1px solid var(--status-warning-border)'
                      }}>
                        <div style={{ color: 'var(--status-warning-text)', fontWeight: 600, fontSize: '0.82rem', marginBottom: '3px' }}>
                          {misc.pitfall}
                        </div>
                        <div style={{ color: 'var(--status-warning-text)', opacity: 0.9, fontSize: '0.8rem' }}>
                          {misc.reality}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 5. Revision Checklist */}
                <div>
                  <h3 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {mockStudyGuide.sections[4].title}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {mockStudyGuide.sections[4].checklist?.map((item, idx) => (
                      <label key={idx} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        fontSize: '0.82rem',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer'
                      }}>
                        <input type="checkbox" style={{ accentColor: 'var(--accent-primary)' }} />
                        <span>{item}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: FLASHCARDS */}
        {activeTab === 'flashcards' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
            {/* Top Toolbar */}
            <div style={{ width: '100%', maxWidth: '640px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Card <strong>{currentCardIndex + 1}</strong> of <strong>{cards.length}</strong>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button onClick={handleShuffle} className="btn btn-secondary btn-sm" title="Shuffle flashcards">
                  <Shuffle size={13} />
                  <span>Shuffle</span>
                </button>
              </div>
            </div>

            {/* 3D Flip Card Container */}
            <div 
              className="flashcard-perspective" 
              style={{ width: '100%', maxWidth: '640px' }}
              onClick={() => setIsFlipped(!isFlipped)}
            >
              <div className={`flashcard-inner ${isFlipped ? 'flipped' : ''}`}>
                {/* Front Face */}
                <div className="flashcard-face flashcard-front">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="badge badge-neutral">{currentCard.subject}</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Click card or press Space to flip</span>
                  </div>

                  <div style={{
                    fontSize: '1.25rem',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    textAlign: 'center',
                    lineHeight: 1.5,
                    padding: '20px 0'
                  }}>
                    {currentCard.front}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <span className="badge badge-info" style={{ fontSize: '0.72rem' }}>
                      Prompt
                    </span>
                  </div>
                </div>

                {/* Back Face */}
                <div className="flashcard-face flashcard-back">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="badge badge-success">Verified Solution</span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Click to flip back</span>
                  </div>

                  <div style={{
                    fontSize: '0.95rem',
                    lineHeight: 1.6,
                    color: 'var(--text-primary)',
                    padding: '16px 0',
                    whiteSpace: 'pre-line'
                  }}>
                    {currentCard.back}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Grounded in Chapter 6</span>
                    <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>FSRS Retention: 89%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Feedback Buttons: Need Review / Got it */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '12px' }}>
              <button
                onClick={handlePrevCard}
                className="btn btn-secondary"
                title="Previous card"
              >
                <ChevronLeft size={16} />
              </button>

              <button
                onClick={() => handleCardFeedback('review')}
                className="btn btn-secondary"
                style={{ minWidth: '130px', borderColor: 'var(--status-danger-border)', color: 'var(--status-danger-badge)' }}
              >
                <AlertCircle size={15} />
                <span>Needs review</span>
              </button>

              <button
                onClick={() => handleCardFeedback('known')}
                className="btn btn-primary"
                style={{ minWidth: '130px', backgroundColor: 'var(--status-success-badge)', borderColor: 'var(--status-success-badge)' }}
              >
                <Check size={15} />
                <span>Got it (Known)</span>
              </button>

              <button
                onClick={handleNextCard}
                className="btn btn-secondary"
                title="Next card"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* TAB 3: PRACTICE QUIZ */}
        {activeTab === 'quiz' && (
          <div style={{ width: '100%', maxWidth: '720px', margin: '0 auto' }}>
            {!quizFinished ? (
              <div style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: '12px',
                padding: '28px',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex',
                flexDirection: 'column',
                gap: '20px'
              }}>
                {/* Quiz Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="badge badge-info">
                    Question {currentQuizIndex + 1} of {quizQuestions.length}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Score: <strong>{quizScore}</strong> / {quizQuestions.length}
                  </span>
                </div>

                {/* Question */}
                <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                  {currentQuiz.question}
                </h2>

                {/* Options */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {currentQuiz.options.map((opt, optIdx) => {
                    const isSelected = selectedAnswers[currentQuizIndex] === optIdx;
                    const isAnswered = selectedAnswers[currentQuizIndex] !== undefined;
                    const isCorrect = optIdx === currentQuiz.correctIndex;

                    let bg = 'var(--bg-surface)';
                    let border = 'var(--border-default)';
                    let color = 'var(--text-secondary)';

                    if (isAnswered) {
                      if (isCorrect) {
                        bg = 'var(--status-success-bg)';
                        border = 'var(--status-success-border)';
                        color = 'var(--status-success-text)';
                      } else if (isSelected) {
                        bg = 'var(--status-danger-bg)';
                        border = 'var(--status-danger-border)';
                        color = 'var(--status-danger-text)';
                      }
                    }

                    return (
                      <button
                        key={optIdx}
                        onClick={() => handleSelectAnswer(currentQuizIndex, optIdx)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '12px 16px',
                          borderRadius: '8px',
                          border: `1px solid ${border}`,
                          backgroundColor: bg,
                          color: color,
                          fontSize: '0.86rem',
                          textAlign: 'left',
                          cursor: isAnswered ? 'default' : 'pointer',
                          transition: 'all 0.15s ease'
                        }}
                      >
                        <span>{opt}</span>
                        {isAnswered && isCorrect && <CheckCircle2 size={16} color="var(--status-success-badge)" />}
                      </button>
                    );
                  })}
                </div>

                {/* Feedback Explanation */}
                {selectedAnswers[currentQuizIndex] !== undefined && (
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    backgroundColor: selectedAnswers[currentQuizIndex] === currentQuiz.correctIndex ? 'var(--status-success-bg)' : 'var(--status-warning-bg)',
                    border: '1px solid',
                    borderColor: selectedAnswers[currentQuizIndex] === currentQuiz.correctIndex ? 'var(--status-success-border)' : 'var(--status-warning-border)',
                    fontSize: '0.8rem',
                    color: selectedAnswers[currentQuizIndex] === currentQuiz.correctIndex ? 'var(--status-success-text)' : 'var(--status-warning-text)'
                  }}>
                    <strong>Explanation:</strong> {currentQuiz.explanation}
                  </div>
                )}

                {/* Next Button */}
                {selectedAnswers[currentQuizIndex] !== undefined && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                    <button
                      onClick={handleNextQuizQuestion}
                      className="btn btn-primary"
                    >
                      <span>{currentQuizIndex < quizQuestions.length - 1 ? 'Next Question' : 'View Results'}</span>
                      <ChevronRight size={15} />
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Quiz Finished Summary */
              <div style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: '12px',
                padding: '36px',
                boxShadow: 'var(--shadow-sm)',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px'
              }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--status-success-bg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Award size={28} color="var(--status-success-badge)" />
                </div>

                <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Quiz Session Completed!
                </h2>

                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', maxWidth: '420px' }}>
                  You scored <strong>{quizScore} out of {quizQuestions.length}</strong>. Your estimated concept mastery for <em>Optimization & Loss Surfaces</em> has been updated to <strong>86%</strong>.
                </p>

                <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                  <button onClick={handleRestartQuiz} className="btn btn-secondary">
                    <RotateCw size={14} />
                    <span>Retake quiz</span>
                  </button>
                  <button onClick={() => setActiveTab('study-guide')} className="btn btn-primary">
                    <span>Back to Study Guide</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
