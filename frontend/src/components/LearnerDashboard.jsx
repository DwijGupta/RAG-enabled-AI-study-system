import React, { useState, useEffect } from 'react';
import { Target, Zap, Activity, CheckCircle2, AlertOctagon, TrendingUp, RefreshCw } from 'lucide-react';

export default function LearnerDashboard({ reloadTrigger }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/learner/profile?user_id=student_1');
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [reloadTrigger]);

  if (!profile) {
    return (
      <div className="glass-panel" style={{ height: 'calc(100vh - 110px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading learner state...</span>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ height: 'calc(100vh - 110px)', overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Overview Cards */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem' }} className="gradient-text">Cognitive Learner Overlay</h2>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Bayesian Knowledge Tracing (BKT) • Long-Term Cognitive Modeling
          </p>
        </div>
        <button onClick={fetchProfile} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
          <RefreshCw size={14} />
          <span>Refresh State</span>
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
        <div className="glass-panel glass-panel-interactive" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#10B981', marginBottom: '8px' }}>
            <CheckCircle2 size={16} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>MASTERED</span>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{profile.mastered_count}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Concepts &gt; 75% Mastery</div>
        </div>

        <div className="glass-panel glass-panel-interactive" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#F59E0B', marginBottom: '8px' }}>
            <Target size={16} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>IN ZPD</span>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{profile.in_zpd_count}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Optimal Challenge Zone</div>
        </div>

        <div className="glass-panel glass-panel-interactive" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#F43F5E', marginBottom: '8px' }}>
            <AlertOctagon size={16} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>PREREQUISITE GAPS</span>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{profile.needs_work_count}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Needs Diagnostic Practice</div>
        </div>

        <div className="glass-panel glass-panel-interactive" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6366F1', marginBottom: '8px' }}>
            <TrendingUp size={16} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>OVERALL PROFICIENCY</span>
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800 }}>{Math.round(profile.overall_mastery * 100)}%</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Curriculum Coverage</div>
        </div>
      </div>

      {/* Concept Breakdown Table */}
      <div className="glass-panel" style={{ padding: '18px' }}>
        <h3 style={{ fontSize: '0.9rem', marginBottom: '14px', color: '#A5B4FC' }}>Tracked Concepts & BKT Posterior</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {profile.concepts.map((c, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: c.p_mastery >= 0.75 ? '#10B981' : c.p_mastery >= 0.45 ? '#F59E0B' : '#EF4444'
                }} />
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{c.concept_name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                    Attempts: {c.attempts} • Correct: {c.correct}
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '180px' }}>
                <div style={{ flex: 1, height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '9999px', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.round(c.p_mastery * 100)}%`,
                    background: c.p_mastery >= 0.75 ? '#10B981' : c.p_mastery >= 0.45 ? '#F59E0B' : '#EF4444',
                    borderRadius: '9999px'
                  }} />
                </div>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, minWidth: '35px', textAlign: 'right' }}>
                  {Math.round(c.p_mastery * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Episodic Traces */}
      <div className="glass-panel" style={{ padding: '18px' }}>
        <h3 style={{ fontSize: '0.9rem', marginBottom: '14px', color: '#A5B4FC' }}>Recent Episodic Traces & Diagnoses</h3>
        {profile.recent_traces.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {profile.recent_traces.map((t, idx) => (
              <div key={idx} style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>"{t.query}"</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Strategy: <span style={{ color: '#818CF8' }}>{t.planner_action}</span>
                    {t.diagnosed_weakness && ` • Remediated: ${t.diagnosed_weakness}`}
                  </div>
                </div>
                <span style={{ fontSize: '0.72rem', color: '#10B981', fontWeight: 600 }}>
                  Faithful {Math.round(t.faithfulness * 100)}%
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No interaction traces logged yet.</p>
        )}
      </div>
    </div>
  );
}
