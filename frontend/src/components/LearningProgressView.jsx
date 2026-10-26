import React, { useState } from 'react';
import { 
  TrendingUp, 
  Brain, 
  CheckCircle2, 
  AlertTriangle, 
  Settings2, 
  Clock, 
  Trash2, 
  Plus, 
  Sparkles,
  ShieldCheck,
  PauseCircle,
  RotateCcw
} from 'lucide-react';
import { mockLearnerProfile } from '../data/mockData.js';

export default function LearningProgressView({
  profile = mockLearnerProfile,
  onPracticeConcept
}) {
  const [preferences, setPreferences] = useState(profile.rememberedPreferences);
  const [newPrefInput, setNewPrefInput] = useState('');
  const [isPersonalizationPaused, setIsPersonalizationPaused] = useState(false);

  const handleAddPreference = () => {
    if (!newPrefInput.trim()) return;
    setPreferences([...preferences, newPrefInput.trim()]);
    setNewPrefInput('');
  };

  const handleRemovePreference = (index) => {
    setPreferences(preferences.filter((_, i) => i !== index));
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Mastered':
        return <span className="badge badge-success">Mastered</span>;
      case 'Strong':
        return <span className="badge badge-info">Strong</span>;
      case 'Developing':
        return <span className="badge badge-warning">Developing</span>;
      case 'Needs practice':
      default:
        return <span className="badge badge-neutral" style={{ color: 'var(--status-danger-badge)' }}>Needs practice</span>;
    }
  };

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      backgroundColor: 'var(--bg-app)',
      padding: '36px 40px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }}>
      <div style={{ width: '100%', maxWidth: '960px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Brain size={20} color="var(--accent-primary)" />
              <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Learning Memory & Cognitive Progress
              </h1>
            </div>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Transparent student model estimating your conceptual mastery, learning preferences, and review schedule.
            </p>
          </div>

          <button
            onClick={() => setIsPersonalizationPaused(!isPersonalizationPaused)}
            className="btn btn-secondary btn-sm"
          >
            <PauseCircle size={14} />
            <span>{isPersonalizationPaused ? 'Resume personalization' : 'Pause personalization'}</span>
          </button>
        </div>

        {/* Top Summary Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px'
        }}>
          <div className="card" style={{ padding: '18px 20px' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Estimated Subject Mastery
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--accent-primary)', marginTop: '4px' }}>
              {profile.overallMastery}%
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Based on practice sessions and diagnostic quizzes
            </div>
          </div>

          <div className="card" style={{ padding: '18px 20px' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Current Focus Area
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '8px' }}>
              Gradient Descent & Backpropagation
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--status-warning-badge)', marginTop: '4px' }}>
              Zone of Proximal Development
            </div>
          </div>

          <div className="card" style={{ padding: '18px 20px' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Flashcard Memory Retention
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--status-success-badge)', marginTop: '4px' }}>
              89.4%
            </div>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              FSRS Spaced Repetition decay rate
            </div>
          </div>
        </div>

        {/* Concept Mastery Breakdown */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Topic-Level Estimated Mastery
              </h2>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Estimates derived from Bayesian Knowledge Tracing (BKT)
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {profile.concepts.map((concept, idx) => (
              <div key={idx} style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                padding: '12px 14px',
                borderRadius: '8px',
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.86rem', color: 'var(--text-primary)' }}>
                      {concept.name}
                    </span>
                    {getStatusBadge(concept.status)}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                      Reviewed {concept.lastReviewed}
                    </span>
                    <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {concept.mastery}%
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div style={{
                  width: '100%',
                  height: '6px',
                  borderRadius: '3px',
                  backgroundColor: 'var(--border-subtle)',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${concept.mastery}%`,
                    height: '100%',
                    backgroundColor: concept.mastery >= 80 ? 'var(--status-success-badge)' : concept.mastery >= 60 ? 'var(--accent-primary)' : 'var(--status-warning-badge)',
                    borderRadius: '3px'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Remembered Learning Preferences */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Remembered Learning Preferences
              </h2>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                You have full control to edit or delete any fact AI Study Buddy System has remembered about your style.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
            {preferences.map((pref, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '8px',
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.84rem',
                color: 'var(--text-secondary)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={14} color="var(--accent-primary)" />
                  <span>{pref}</span>
                </div>
                <button
                  onClick={() => handleRemovePreference(idx)}
                  className="btn-icon"
                  style={{ width: '24px', height: '24px', color: 'var(--text-muted)' }}
                  title="Remove memory item"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>

          {/* Add custom preference */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="Add a new instruction (e.g., 'Explain with Python code before mathematical proofs')..."
              value={newPrefInput}
              onChange={(e) => setNewPrefInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddPreference()}
              className="input-field"
              style={{ fontSize: '0.82rem' }}
            />
            <button
              onClick={handleAddPreference}
              className="btn btn-secondary btn-sm"
              style={{ whiteSpace: 'nowrap' }}
            >
              <Plus size={14} />
              <span>Add Memory</span>
            </button>
          </div>
        </div>

        {/* Saved Diagnostic Misconceptions */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <AlertTriangle size={18} color="var(--status-warning-badge)" />
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Diagnosed Conceptual Misconceptions
              </h2>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Targeted areas identified during recent problem solving where tutor interventions are active.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {profile.struggledMisconceptions.map((item, idx) => (
              <div key={idx} style={{
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: 'var(--status-warning-bg)',
                border: '1px solid var(--status-warning-border)'
              }}>
                <div style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--status-warning-text)', marginBottom: '3px' }}>
                  {item.topic}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--status-warning-text)', opacity: 0.9 }}>
                  {item.detail}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
