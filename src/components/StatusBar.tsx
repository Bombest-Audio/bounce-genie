
import type { RunState } from '../types';

interface Props {
  runState: RunState;
  jobCount: number;
  completedCount: number;
  failedCount: number;
}

const STATE_LABELS: Record<RunState, string> = {
  idle: 'Ready',
  running: 'Running',
  paused: 'Paused',
  complete: 'Complete',
};

export function StatusBar({ runState, jobCount, completedCount, failedCount }: Props) {
  return (
    <div className="status-bar">
      <div className={`status-dot ${runState}`} />
      <span className="status-text">{STATE_LABELS[runState]}</span>
      <div className="status-sep" />
      <span className="status-text">{jobCount} session{jobCount !== 1 ? 's' : ''} queued</span>
      {(completedCount > 0 || failedCount > 0) && (
        <>
          <div className="status-sep" />
          <span className="status-text" style={{ color: 'var(--green)' }}>{completedCount} done</span>
          {failedCount > 0 && (
            <>
              <div className="status-sep" />
              <span className="status-text" style={{ color: 'var(--red)' }}>{failedCount} failed</span>
            </>
          )}
        </>
      )}
      <div className="status-right">
        <span className="status-text" style={{ fontSize: 10 }}>Bounce Genie v0.1.0</span>
      </div>
    </div>
  );
}
