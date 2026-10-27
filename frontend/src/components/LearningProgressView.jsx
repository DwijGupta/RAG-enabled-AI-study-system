import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  Plus, 
  Sparkles,
  PauseCircle,
  PlayCircle,
  RotateCcw,
  BookOpen
} from 'lucide-react';

export default function LearningProgressView({
  onPracticeConcept,
  onGoToChat
}) {
  const [profileData, setProfileData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [preferences, setPreferences] = useState(() => {
    try {
      const saved = localStorage.getItem('studybuddy_preferences');
      return saved ? JSON.parse(saved) : [
        'Prefers concise intuitive intuition before formal mathematics',
        'Prefers concrete code examples and step-by-step derivations'
      ];
    } catch (_) {
      return ['Prefers concise intuitive intuition before formal mathematics'];
    }
  });
  const [newPrefInput, setNewPrefInput] = useState('');
  const [isPersonalizationPaused, setIsPersonalizationPaused] = useState(false);

  const fetchProfile = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/learner/profile?user_id=student_1');
      if (res.ok) {
        const data = await res.json();
        setProfileData(data);
      }
    } catch (err) {
      console.warn('Could not load learner profile from API:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleAddPreference = () => {
    if (!newPrefInput.trim()) return;
    const updated = [...preferences, newPrefInput.trim()];
    setPreferences(updated);
    try {
      localStorage.setItem('studybuddy_preferences', JSON.stringify(updated));
    } catch (_) {}
    setNewPrefInput('');
  };

  const handleRemovePreference = (index) => {
    const updated = preferences.filter((_, i) => i !== index);
    setPreferences(updated);
    try {
      localStorage.setItem('studybuddy_preferences', JSON.stringify(updated));
    } catch (_) {}
  };

  const concepts = profileData?.concepts || [];
  const recentTraces = profileData?.recent_traces || [];
  const totalTracked = profileData?.total_concepts_tracked || concepts.length;
  const masteredCount = profileData?.mastered_count || 0;
  const inZpdCount = profileData?.in_zpd_count || 0;
  const needsWorkCount = profileData?.needs_work_count || 0;

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      backgroundColor: 'var(--bg-app)',
      padding: '32px 36px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }}>
      <div style={{ width: '100%', maxWidth: '880px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Brain size={20} color="var(--accent-primary)" />
              <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Learning Profile & Mastery
              </h1>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>
              Real-time cognitive model tracking conceptual understanding across your active study sessions.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => fetchProfile()}
              className="btn btn-secondary btn-sm"
              title="Refresh profile data"
            >
              <RotateCcw size={13} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => setIsPersonalizationPaused(!isPersonalizationPaused)}
              className="btn btn-secondary btn-sm"
            >
              {isPersonalizationPaused ? (
                <>
                  <PlayCircle size={13} color="var(--status-success-badge)" />
                  <span>Resume Tutor Memory</span>
                </>
              ) : (
                <>
                  <PauseCircle size={13} color="var(--accent-primary)" />
                  <span>Pause Tutor Memory</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Minimal Clean Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '12px'
        }}>
          <div className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Mastered Concepts
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--status-success-badge)', marginTop: '2px' }}>
              {masteredCount}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Demonstrated solid comprehension
            </div>
          </div>

          <div className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              In Active Practice
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-primary)', marginTop: '2px' }}>
              {inZpdCount}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Zone of Proximal Development
            </div>
          </div>

          <div className="card" style={{ padding: '14px 18px' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              Needs Review
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--status-warning-badge)', marginTop: '2px' }}>
              {needsWorkCount}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Targeted for upcoming review
            </div>
          </div>
        </div>

        {/* Tracked Concepts */}
        <div className="card" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div>
              <h2 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Tracked Knowledge Concepts
              </h2>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Concepts identified and evaluated from course materials and practice interactions
              </div>
            </div>
          </div>

          {concepts.length === 0 ? (
            <div style={{
              padding: '32px 16px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '10px'
            }}>
              <BookOpen size={28} color="var(--text-muted)" style={{ opacity: 0.6 }} />
              <div style={{ fontSize: '0.86rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                No concept practice data recorded yet
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: '400px', margin: 0 }}>
                As you chat with the tutor, upload documents, and answer follow-up questions, your concept mastery will automatically appear here.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {concepts.map((c, idx) => {
                const masteryVal = typeof c.p_mastery === 'number' ? Math.round(c.p_mastery * 100) : 50;
                let statusLabel = 'Developing';
                let statusClass = 'badge-warning';
                if (masteryVal >= 75) {
                  statusLabel = 'Mastered';
                  statusClass = 'badge-success';
                } else if (masteryVal < 45) {
                  statusLabel = 'Needs Practice';
                  statusClass = 'badge-neutral';
                }

                return (
                  <div key={idx} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-subtle)',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                        {c.concept_name || c.name}
                      </span>
                      <span className={`badge ${statusClass}`} style={{ fontSize: '0.68rem', padding: '1px 6px' }}>
                        {statusLabel}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        {c.attempts ? `${c.correct || 0}/${c.attempts} correct` : 'Practiced'}
                      </span>
                      {onPracticeConcept && (
                        <button
                          onClick={() => onPracticeConcept(c.concept_name || c.name)}
                          className="btn btn-ghost btn-sm"
                          style={{ fontSize: '0.72rem', padding: '2px 8px' }}
                        >
                          Practice
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Learning Preferences */}
        <div className="card" style={{ padding: '20px 22px' }}>
          <div style={{ marginBottom: '14px' }}>
            <h2 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Learner Preferences & Directives
            </h2>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
              Custom instructions guiding how the AI tutor formats explanations, analogies, and pacing
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
            {preferences.map((pref, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '9px 12px',
                borderRadius: '7px',
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.82rem',
                color: 'var(--text-secondary)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={13} color="var(--accent-primary)" />
                  <span>{pref}</span>
                </div>
                <button
                  onClick={() => handleRemovePreference(idx)}
                  className="btn-icon"
                  style={{ width: '22px', height: '22px', color: 'var(--text-muted)' }}
                  title="Remove instruction"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="Add preference (e.g., 'Explain step-by-step with code first')..."
              value={newPrefInput}
              onChange={(e) => setNewPrefInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddPreference()}
              className="input-field"
              style={{ fontSize: '0.8rem', padding: '7px 12px' }}
            />
            <button
              onClick={handleAddPreference}
              className="btn btn-secondary btn-sm"
              style={{ whiteSpace: 'nowrap' }}
            >
              <Plus size={13} />
              <span>Add</span>
            </button>
          </div>
        </div>

        {/* Recent Session Trace Log if any */}
        {recentTraces.length > 0 && (
          <div className="card" style={{ padding: '20px 22px' }}>
            <div style={{ marginBottom: '12px' }}>
              <h2 style={{ fontSize: '0.98rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Recent Interaction History
              </h2>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                Verified question traces and pedagogical actions
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentTraces.map((t) => (
                <div key={t.id} style={{
                  padding: '9px 12px',
                  borderRadius: '7px',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '0.8rem'
                }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', maxWidth: '75%' }}>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      "{t.query}"
                    </div>
                    {t.diagnosed_weakness && (
                      <div style={{ fontSize: '0.7rem', color: 'var(--status-warning-badge)' }}>
                        Targeted: {t.diagnosed_weakness}
                      </div>
                    )}
                  </div>
                  <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>
                    {t.planner_action || 'Grounded Response'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
