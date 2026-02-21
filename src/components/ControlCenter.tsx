import { useEffect, useRef } from 'react';
import type { BounceJob, RunState, BatchResult } from '../types';
import { JOB_STEPS, STEP_LABELS, DAW_LABELS } from '../types';

interface Props {
  jobs: BounceJob[];
  runState: RunState;
  currentJobIndex: number;
  result: BatchResult | null;
  logMessages: string[];
  completedCount: number;
  failedCount: number;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
}

const WAVE_BARS = Array.from({ length: 32 }, (_, i) => i);

function GenielampSVG() {
  return (
    <svg className="genie-lamp" viewBox="0 0 160 160" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Glow rings */}
      <circle cx="80" cy="100" r="50" stroke="url(#glow-ring1)" strokeWidth="1" strokeDasharray="4 6" opacity="0.3"/>
      <circle cx="80" cy="100" r="62" stroke="url(#glow-ring2)" strokeWidth="1" strokeDasharray="3 8" opacity="0.15"/>

      {/* Lamp base shadow */}
      <ellipse cx="80" cy="128" rx="36" ry="8" fill="url(#shadow)" opacity="0.4"/>

      {/* Lamp body */}
      <path d="M45 110 C38 90 42 65 52 52 C60 42 68 36 80 36 C92 36 100 42 108 52 C118 65 122 90 115 110 Z"
        fill="url(#lamp-body)" />
      <path d="M45 110 C38 90 42 65 52 52 C60 42 68 36 80 36 C92 36 100 42 108 52 C118 65 122 90 115 110 Z"
        stroke="url(#lamp-stroke)" strokeWidth="1.5" fill="none"/>

      {/* Lamp rim */}
      <ellipse cx="80" cy="110" rx="35" ry="9" fill="url(#lamp-rim)"/>
      <ellipse cx="80" cy="110" rx="35" ry="9" stroke="url(#rim-stroke)" strokeWidth="1" fill="none"/>

      {/* Lamp base */}
      <rect x="60" y="118" width="40" height="12" rx="4" fill="url(#lamp-base)"/>
      <rect x="55" y="128" width="50" height="6" rx="3" fill="url(#lamp-foot)"/>

      {/* Spout */}
      <path d="M45 102 C32 98 22 94 18 86 C14 78 18 70 28 68 C36 67 40 72 38 80 C37 85 40 88 45 90"
        stroke="url(#spout-stroke)" strokeWidth="6" strokeLinecap="round" fill="none"/>
      <path d="M45 102 C32 98 22 94 18 86 C14 78 18 70 28 68 C36 67 40 72 38 80 C37 85 40 88 45 90"
        stroke="url(#spout-inner)" strokeWidth="3" strokeLinecap="round" fill="none"/>

      {/* Handle */}
      <path d="M115 102 C128 98 134 88 130 78 C127 70 120 67 113 70"
        stroke="url(#handle-stroke)" strokeWidth="5" strokeLinecap="round" fill="none"/>

      {/* Magic sparkle / flame */}
      <g transform="translate(15, 48)">
        <circle cx="0" cy="0" r="14" fill="url(#flame-glow)" opacity="0.5"/>
        <path d="M0 -10 C0 -10 -5 -4 -3 0 C-2 3 2 3 3 0 C5 -4 0 -10 0 -10Z"
          fill="url(#flame-color)" opacity="0.9"/>
        <path d="M0 -6 C0 -6 -2 -3 -1 0 C-0.5 1.5 0.5 1.5 1 0 C2 -3 0 -6 0 -6Z"
          fill="white" opacity="0.7"/>
      </g>

      {/* Stars/sparkles */}
      <g opacity="0.7">
        <path d="M128 30 L129.5 27 L131 30 L128 30Z" fill="var(--cyan)" transform="rotate(15 129.5 28.5)"/>
        <path d="M120 20 L121 18 L122 20 L120 20Z" fill="var(--purple-light)" transform="rotate(-10 121 19)"/>
        <path d="M140 48 L141.5 45 L143 48 L140 48Z" fill="var(--amber)" transform="rotate(5 141.5 46.5)"/>
        <circle cx="135" cy="62" r="2" fill="var(--cyan)" opacity="0.6"/>
        <circle cx="110" cy="15" r="1.5" fill="var(--purple-light)" opacity="0.5"/>
      </g>

      {/* Smoke/magic wisps */}
      <path d="M80 36 C76 28 80 18 76 10" stroke="url(#wisp1)" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.5"/>
      <path d="M80 36 C84 26 82 16 86 8" stroke="url(#wisp2)" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.35"/>

      <defs>
        <linearGradient id="lamp-body" x1="45" y1="36" x2="115" y2="120" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C3AED"/>
          <stop offset="0.5" stopColor="#9B73F8"/>
          <stop offset="1" stopColor="#0891B2"/>
        </linearGradient>
        <linearGradient id="lamp-stroke" x1="45" y1="36" x2="115" y2="110" gradientUnits="userSpaceOnUse">
          <stop stopColor="#C4B5FD" stopOpacity="0.8"/>
          <stop offset="1" stopColor="#67E8F9" stopOpacity="0.6"/>
        </linearGradient>
        <linearGradient id="lamp-rim" x1="45" y1="110" x2="115" y2="110" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6D28D9"/>
          <stop offset="1" stopColor="#0E7490"/>
        </linearGradient>
        <linearGradient id="rim-stroke" x1="45" y1="110" x2="115" y2="110" gradientUnits="userSpaceOnUse">
          <stop stopColor="#A78BFA" stopOpacity="0.8"/>
          <stop offset="1" stopColor="#22D3EE" stopOpacity="0.6"/>
        </linearGradient>
        <linearGradient id="lamp-base" x1="60" y1="118" x2="100" y2="130" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5B21B6"/>
          <stop offset="1" stopColor="#164E63"/>
        </linearGradient>
        <linearGradient id="lamp-foot" x1="55" y1="128" x2="105" y2="134" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4C1D95"/>
          <stop offset="1" stopColor="#0C4A6E"/>
        </linearGradient>
        <linearGradient id="spout-stroke" x1="18" y1="68" x2="45" y2="110" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C3AED"/>
          <stop offset="1" stopColor="#9B73F8"/>
        </linearGradient>
        <linearGradient id="spout-inner" x1="18" y1="68" x2="45" y2="110" gradientUnits="userSpaceOnUse">
          <stop stopColor="#C4B5FD" stopOpacity="0.5"/>
          <stop offset="1" stopColor="#A78BFA" stopOpacity="0.3"/>
        </linearGradient>
        <linearGradient id="handle-stroke" x1="113" y1="70" x2="130" y2="102" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0891B2"/>
          <stop offset="1" stopColor="#22D3EE"/>
        </linearGradient>
        <radialGradient id="flame-glow" cx="0.5" cy="0.5" r="0.5">
          <stop stopColor="#FCD34D" stopOpacity="0.8"/>
          <stop offset="1" stopColor="#FCD34D" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="flame-color" x1="0" y1="-10" x2="0" y2="3" gradientUnits="userSpaceOnUse">
          <stop stopColor="#FEF3C7"/>
          <stop offset="0.5" stopColor="#F59E0B"/>
          <stop offset="1" stopColor="#DC2626"/>
        </linearGradient>
        <radialGradient id="shadow" cx="0.5" cy="0.5" r="0.5">
          <stop stopColor="#000000" stopOpacity="0.5"/>
          <stop offset="1" stopColor="#000000" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id="glow-ring1" x1="30" y1="50" x2="130" y2="150" gradientUnits="userSpaceOnUse">
          <stop stopColor="#9B73F8"/>
          <stop offset="1" stopColor="#22D3EE"/>
        </linearGradient>
        <linearGradient id="glow-ring2" x1="18" y1="38" x2="142" y2="162" gradientUnits="userSpaceOnUse">
          <stop stopColor="#9B73F8" stopOpacity="0.5"/>
          <stop offset="1" stopColor="#22D3EE" stopOpacity="0.5"/>
        </linearGradient>
        <linearGradient id="wisp1" x1="76" y1="36" x2="80" y2="10" gradientUnits="userSpaceOnUse">
          <stop stopColor="#9B73F8"/>
          <stop offset="1" stopColor="#9B73F8" stopOpacity="0"/>
        </linearGradient>
        <linearGradient id="wisp2" x1="82" y1="36" x2="86" y2="8" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22D3EE"/>
          <stop offset="1" stopColor="#22D3EE" stopOpacity="0"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

function Waveform({ paused }: { paused: boolean }) {
  return (
    <div className={`waveform ${paused ? 'paused' : ''}`}>
      {WAVE_BARS.map(i => {
        const maxH = 12 + Math.sin(i * 0.7) * 18 + Math.cos(i * 1.3) * 12 + Math.random() * 8;
        const duration = 0.4 + (i % 7) * 0.08;
        const delay = (i % 11) * 0.04;
        return (
          <div
            key={i}
            className="wave-bar"
            style={{
              '--max-height': `${Math.max(8, maxH)}px`,
              '--duration': `${duration}s`,
              '--delay': `${delay}s`,
            } as React.CSSProperties}
          />
        );
      })}
    </div>
  );
}

export function ControlCenter({ jobs, runState, currentJobIndex, result, logMessages, completedCount, failedCount, onStart, onPause, onStop }: Props) {
  const logRef = useRef<HTMLDivElement>(null);
  const currentJob = currentJobIndex >= 0 ? jobs[currentJobIndex] : null;
  const total = jobs.length;

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logMessages]);

  const overallPct = total > 0 ? ((completedCount + failedCount) / total) * 100 : 0;

  const currentStepIdx = currentJob?.step ? JOB_STEPS.indexOf(currentJob.step) : -1;

  return (
    <div className="control-center">
      <div className="panel-header">
        <span className="panel-title">Control Center</span>
        {(runState === 'running' || runState === 'paused') && (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {completedCount + failedCount} / {total} jobs
          </span>
        )}
      </div>

      <div className="control-center-body">
        {/* ── IDLE ── */}
        {runState === 'idle' && (
          <div className="idle-view">
            <div className="genie-container">
              <div className="genie-glow"/>
              <GenielampSVG />
            </div>

            <div className="idle-text">
              {jobs.length === 0 ? (
                <>
                  <div className="idle-title">Ready to Grant Wishes</div>
                  <div className="idle-desc">
                    Add your DAW session files to the queue, configure your settings, then let Bounce Genie handle the rest.
                  </div>
                </>
              ) : (
                <>
                  <div className="idle-title">{jobs.length} Session{jobs.length !== 1 ? 's' : ''} Ready</div>
                  <div className="idle-desc">
                    Hit Start to begin bouncing all sessions in sequence.
                  </div>
                </>
              )}
            </div>

            <button
              className="btn btn-primary btn-lg"
              onClick={onStart}
              disabled={jobs.length === 0}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4 3L13 8L4 13V3Z"/>
              </svg>
              Start Batch
            </button>

            {logMessages.length > 0 && (
              <div ref={logRef} className="log-viewer">
                {logMessages.map((msg, i) => (
                  <div key={i} className={`log-entry ${msg.includes('✅') ? 'success' : msg.includes('❌') ? 'error' : ''}`}>
                    {msg}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── RUNNING / PAUSED ── */}
        {(runState === 'running' || runState === 'paused') && (
          <div className="running-view">
            <Waveform paused={runState === 'paused'} />

            {currentJob && (
              <div className="current-job-card">
                <div className="current-job-header">
                  <div>
                    <div className="current-job-name">{currentJob.sessionName}</div>
                    <div className="current-job-path">{currentJob.sessionPath}</div>
                  </div>
                  <div className="current-job-daw">
                    {DAW_LABELS[currentJob.dawType ?? 'protools']}
                  </div>
                </div>

                {/* Step tracker */}
                <div className="step-track">
                  {JOB_STEPS.filter(s => s !== 'done').map((step, idx) => {
                    const isDone = currentStepIdx > idx;
                    const isActive = currentStepIdx === idx;
                    return (
                      <div key={step} className={`step-item ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
                        <div className={`step-dot ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
                          {isDone && (
                            <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
                              <path d="M1.5 4L3 5.5L6.5 2" stroke="var(--green)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                          )}
                          {isActive && (
                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--cyan)', animation: 'statusPulse 1s infinite' }}/>
                          )}
                        </div>
                        <span className="step-label">{STEP_LABELS[step].replace(' ', '\n')}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Current step progress */}
                <div className="progress-bar" style={{ marginTop: 4 }}>
                  <div
                    className="progress-fill"
                    style={{ width: `${(currentStepIdx / 4) * 100 + (currentJob.stepProgress / 4)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Overall progress */}
            <div className="overall-progress">
              <div className="progress-header">
                <span className="progress-label">Overall Progress</span>
                <span className="progress-count">
                  {completedCount + failedCount} / {total}
                  {failedCount > 0 && <span style={{ color: 'var(--red)', marginLeft: 6 }}>({failedCount} failed)</span>}
                </span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${overallPct}%` }} />
              </div>
            </div>

            {/* Controls */}
            <div className="batch-controls">
              <button className="btn btn-secondary" onClick={onPause}>
                {runState === 'paused' ? (
                  <>
                    <svg width="13" height="13" viewBox="0 0 13 13" fill="currentColor">
                      <path d="M3 2L11 6.5L3 11V2Z"/>
                    </svg>
                    Resume
                  </>
                ) : (
                  <>
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                      <rect x="2" y="2" width="3" height="8" rx="1"/>
                      <rect x="7" y="2" width="3" height="8" rx="1"/>
                    </svg>
                    Pause
                  </>
                )}
              </button>
              <button className="btn btn-danger" onClick={onStop}>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                  <rect x="2" y="2" width="8" height="8" rx="1.5"/>
                </svg>
                Stop
              </button>
            </div>

            {/* Mini log */}
            <div ref={logRef} className="log-viewer">
              {logMessages.length === 0 ? (
                <div className="log-entry">Initializing batch run…</div>
              ) : logMessages.slice(-20).map((msg, i) => (
                <div key={i} className={`log-entry ${msg.includes('✅') ? 'success' : msg.includes('❌') ? 'error' : ''}`}>
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── COMPLETE ── */}
        {runState === 'complete' && result && (
          <div className="complete-view">
            <div className={`result-icon ${failedCount > 0 ? 'has-errors' : ''}`}>
              {failedCount === 0 ? (
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <path d="M8 18L15 25L28 11" stroke="var(--green)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              ) : (
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <path d="M18 10V20M18 26V27" stroke="var(--amber)" strokeWidth="2.5" strokeLinecap="round"/>
                </svg>
              )}
            </div>

            <div className="result-title">
              {failedCount === 0 ? '🎉 Batch Complete!' : `Batch Finished with ${failedCount} Error${failedCount !== 1 ? 's' : ''}`}
            </div>

            <div className="result-stats">
              <div className="result-stat">
                <span className="result-stat-value total">{result.total}</span>
                <span className="result-stat-label">Total Sessions</span>
              </div>
              <div className="result-stat">
                <span className="result-stat-value success">{completedCount}</span>
                <span className="result-stat-label">Succeeded</span>
              </div>
              <div className="result-stat">
                <span className="result-stat-value fail">{failedCount}</span>
                <span className="result-stat-label">Failed</span>
              </div>
            </div>

            <div ref={logRef} className="log-viewer" style={{ height: 88 }}>
              {logMessages.map((msg, i) => (
                <div key={i} className={`log-entry ${msg.includes('✅') ? 'success' : msg.includes('❌') ? 'error' : ''}`}>
                  {msg}
                </div>
              ))}
            </div>

            <div className="batch-controls">
              <button className="btn btn-primary" onClick={() => onStart()}>
                <svg width="13" height="13" viewBox="0 0 13 13" fill="currentColor">
                  <path d="M2 2L11 6.5L2 11V2Z"/>
                </svg>
                Run Again
              </button>
              <button className="btn btn-secondary" onClick={() => window.location.reload()}>
                New Batch
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
