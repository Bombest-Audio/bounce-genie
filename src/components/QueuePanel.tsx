import { useCallback, useRef, useState } from 'react';
import type { BounceJob, RunState, DawType } from '../types';
import { DAW_LABELS } from '../types';

interface Props {
  jobs: BounceJob[];
  runState: RunState;
  onAddJobs: (paths: string[]) => void;
  onRemoveJob: (id: string) => void;
  onClearAll: () => void;
}

const STATUS_ICONS: Record<BounceJob['status'], React.ReactNode> = {
  pending: (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
      <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1.5" fill="none"/>
    </svg>
  ),
  running: (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor" className="spin">
      <path d="M5 1A4 4 0 0 1 9 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
    </svg>
  ),
  completed: (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <path d="M2 5L4 7L8 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  failed: (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <path d="M3 3L7 7M7 3L3 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
};

const DAW_ICONS: Record<DawType, string> = {
  protools: '🎚️',
  logic: '🍎',
  cubase: '🎹',
  ableton: '🎛️',
};

const EXT_TO_DAW: Record<string, DawType> = {
  ptx: 'protools', pts: 'protools',
  logicx: 'logic',
  cpr: 'cubase',
  als: 'ableton',
};

function detectDaw(path: string): DawType {
  const ext = path.split('.').pop()?.toLowerCase() ?? '';
  return EXT_TO_DAW[ext] ?? 'protools';
}

export function QueuePanel({ jobs, runState, onAddJobs, onRemoveJob, onClearAll }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isRunning = runState === 'running' || runState === 'paused';

  const handleFilePick = useCallback(async () => {
    // Try Tauri dialog first, fall back to browser file input
    try {
      const { open } = await import('@tauri-apps/plugin-dialog');
      const selected = await open({
        multiple: true,
        filters: [{ name: 'DAW Sessions', extensions: ['ptx', 'pts', 'logicx', 'als', 'cpr', 'rpp'] }],
      });
      if (selected) {
        const paths = Array.isArray(selected) ? selected : [selected];
        onAddJobs(paths.map(p => typeof p === 'string' ? p : (p as { path: string }).path));
      }
    } catch {
      fileInputRef.current?.click();
    }
  }, [onAddJobs]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    onAddJobs(files.map(f => f.name));
    e.target.value = '';
  }, [onAddJobs]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    const paths = files.map(f => f.name || (f as File & { path?: string }).path || f.name);
    if (paths.length) onAddJobs(paths);
  }, [onAddJobs]);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);

  const addDemoJobs = () => {
    onAddJobs([
      '/Sessions/Track_01_Intro.ptx',
      '/Sessions/Track_02_Verse.ptx',
      '/Sessions/Track_03_Chorus.als',
      '/Sessions/Track_04_Bridge.logicx',
      '/Sessions/Track_05_Outro.ptx',
    ]);
  };

  return (
    <div className="queue-panel panel">
      <div className="panel-header">
        <span className="panel-title">Session Queue</span>
        <div className="queue-actions">
          {jobs.length > 0 && (
            <button
              className="btn btn-ghost"
              style={{ fontSize: 11, padding: '0 8px', height: 26 }}
              onClick={onClearAll}
              disabled={isRunning}
              title="Clear all"
            >
              Clear
            </button>
          )}
          <button
            className="btn btn-secondary"
            style={{ fontSize: 11, padding: '0 10px', height: 26 }}
            onClick={handleFilePick}
            disabled={isRunning}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 2V10M2 6H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            Add Files
          </button>
        </div>
      </div>

      <div className="panel-scroll">
        <div
          className={`queue-drop-zone ${dragOver ? 'drag-over' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={isRunning ? undefined : handleFilePick}
        >
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" style={{ display: 'block', margin: '0 auto 8px', color: dragOver ? 'var(--purple)' : 'var(--text-muted)', transition: 'color 0.2s' }}>
            <path d="M14 4L14 18M14 4L10 8M14 4L18 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M4 20V22C4 23.1 4.9 24 6 24H22C23.1 24 24 23.1 24 22V20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          <div className="drop-zone-text">
            {dragOver ? 'Drop to add sessions' : 'Drop sessions here'}
          </div>
          <div className="drop-zone-hint">PTX · LOGICX · ALS · CPR</div>
        </div>

        {jobs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <button
              className="btn btn-ghost"
              style={{ fontSize: 11, color: 'var(--purple-light)', textDecoration: 'underline', textDecorationStyle: 'dashed', textUnderlineOffset: 3 }}
              onClick={addDemoJobs}
            >
              Load demo sessions
            </button>
          </div>
        ) : (
          <div className="job-list">
            {jobs.map((job) => {
              const daw = job.dawType ?? detectDaw(job.sessionPath);
              const overallStep = job.step ? ['opening', 'prepping', 'bouncing', 'routing', 'done'].indexOf(job.step) : -1;
              const stepPct = overallStep >= 0 ? ((overallStep / 4) * 100) + (job.stepProgress / 4) : 0;
              return (
                <div key={job.id} className={`job-item ${job.status}`}>
                  <div className={`job-status-icon ${job.status}`}>
                    {STATUS_ICONS[job.status]}
                  </div>
                  <div className="job-info">
                    <div className="job-name" title={job.sessionPath}>{job.sessionName}</div>
                    <div className="job-meta">
                      <span className="daw-badge">{DAW_ICONS[daw]} {DAW_LABELS[daw]}</span>
                      {job.status === 'running' && job.step && (
                        <span className="job-step-label" style={{ marginLeft: 6 }}>
                          {job.step === 'opening' ? 'Opening…' :
                           job.step === 'prepping' ? 'Prepping…' :
                           job.step === 'bouncing' ? 'Bouncing…' :
                           job.step === 'routing' ? 'Routing…' : 'Done'}
                        </span>
                      )}
                      {job.status === 'failed' && job.error && (
                        <span style={{ color: 'var(--red)', marginLeft: 6 }}>Error</span>
                      )}
                    </div>
                    {job.status === 'running' && (
                      <div className="job-progress-bar">
                        <div className="job-progress-fill" style={{ width: `${stepPct}%` }} />
                      </div>
                    )}
                    {job.status === 'completed' && (
                      <div className="job-progress-bar">
                        <div className="job-progress-fill" style={{ width: '100%', background: 'var(--green)' }} />
                      </div>
                    )}
                  </div>
                  <button
                    className="job-remove-btn"
                    onClick={() => onRemoveJob(job.id)}
                    disabled={job.status === 'running'}
                    title="Remove"
                  >
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M2 2L8 8M8 2L2 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".ptx,.pts,.logicx,.als,.cpr,.rpp"
        style={{ display: 'none' }}
        onChange={handleFileInputChange}
      />
    </div>
  );
}
