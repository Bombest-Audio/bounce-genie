import { useState, useCallback, useRef, useEffect } from 'react';
import './App.css';
import { Header } from './components/Header';
import { QueuePanel } from './components/QueuePanel';
import { ControlCenter } from './components/ControlCenter';
import { ConfigPanel } from './components/ConfigPanel';
import { StatusBar } from './components/StatusBar';
import type { BounceJob, AppConfig, RunState, BatchResult, DawType } from './types';
import { JOB_STEPS } from './types';

function genId() { return Math.random().toString(36).slice(2, 10); }

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

const DEFAULT_CONFIG: AppConfig = {
  daw: 'protools',
  formats: ['wav'],
  sampleRate: 44100,
  bitDepth: 24,
  offline: true,
  selectionStrategy: 'USE_SAVED_SELECTION',
  namingTemplate: '${session_name}',
  copyDest: '',
  email: '',
  phone: '',
  stopOnError: true,
};

export default function App() {
  const [jobs, setJobs] = useState<BounceJob[]>([]);
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG);
  const [runState, setRunState] = useState<RunState>('idle');
  const [currentJobIndex, setCurrentJobIndex] = useState(-1);
  const [result, setResult] = useState<BatchResult | null>(null);
  const [logMessages, setLogMessages] = useState<string[]>([]);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pausedRef = useRef(false);
  const stoppedRef = useRef(false);
  const jobsRef = useRef(jobs);
  jobsRef.current = jobs;

  const addLog = useCallback((msg: string) => {
    setLogMessages(prev => [...prev.slice(-150), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const addJobs = useCallback((paths: string[]) => {
    setJobs(prev => {
      const existing = new Set(prev.map(j => j.sessionPath));
      const fresh = paths
        .filter(p => !existing.has(p))
        .map(p => ({
          id: genId(),
          sessionPath: p,
          sessionName: p.split(/[\\/]/).pop()?.replace(/\.[^.]+$/, '') ?? p,
          dawType: detectDaw(p),
          status: 'pending' as const,
          stepProgress: 0,
        }));
      return [...prev, ...fresh];
    });
    setResult(null);
  }, []);

  const removeJob = useCallback((id: string) => {
    setJobs(prev => prev.filter(j => j.id !== id));
  }, []);

  const clearJobs = useCallback(() => {
    setJobs([]);
    setResult(null);
    setRunState('idle');
    setCurrentJobIndex(-1);
    setLogMessages([]);
    pausedRef.current = false;
    stoppedRef.current = false;
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, []);

  const startBatch = useCallback(() => {
    const current = jobsRef.current;
    if (current.length === 0) return;
    // Reset
    setJobs(prev => prev.map(j => ({ ...j, status: 'pending', step: undefined, stepProgress: 0, error: undefined, outputs: undefined })));
    setResult(null);
    setLogMessages([]);
    pausedRef.current = false;
    stoppedRef.current = false;
    setRunState('running');
    setCurrentJobIndex(0);
    addLog(`🚀 Starting batch: ${current.length} session${current.length !== 1 ? 's' : ''}`);
  }, [addLog]);

  const pauseBatch = useCallback(() => {
    setRunState(prev => {
      if (prev === 'running') {
        pausedRef.current = true;
        addLog('⏸ Batch paused');
        return 'paused';
      } else if (prev === 'paused') {
        pausedRef.current = false;
        addLog('▶️ Batch resumed');
        return 'running';
      }
      return prev;
    });
  }, [addLog]);

  const stopBatch = useCallback(() => {
    stoppedRef.current = true;
    pausedRef.current = false;
    if (intervalRef.current) clearInterval(intervalRef.current);
    setJobs(prev => prev.map(j =>
      j.status === 'running' ? { ...j, status: 'pending', step: undefined, stepProgress: 0 } : j
    ));
    setCurrentJobIndex(-1);
    setRunState('idle');
    addLog('⏹ Batch stopped by user');
  }, [addLog]);

  // Simulation engine
  useEffect(() => {
    if (runState !== 'running' || currentJobIndex < 0) return;

    const currentJobs = jobsRef.current;
    if (currentJobIndex >= currentJobs.length) {
      // All done
      const succ = currentJobs.filter(j => j.status === 'completed').length;
      const fail = currentJobs.filter(j => j.status === 'failed').length;
      setResult({ total: currentJobs.length, succeeded: succ, failed: fail, outputs: [], errors: [], durationMs: 0 });
      setRunState('complete');
      setCurrentJobIndex(-1);
      addLog(`🎉 Batch complete: ${succ} succeeded, ${fail} failed`);
      return;
    }

    const job = currentJobs[currentJobIndex];
    if (!job || job.status === 'completed' || job.status === 'failed') {
      setCurrentJobIndex(i => i + 1);
      return;
    }

    addLog(`⚙️ Processing: ${job.sessionName}`);

    // Mark as running
    setJobs(prev => prev.map(j =>
      j.id === job.id ? { ...j, status: 'running', step: JOB_STEPS[0], stepProgress: 0 } : j
    ));

    let stepIdx = 0;
    let stepProgress = 0;

    const tick = () => {
      if (pausedRef.current || stoppedRef.current) return;

      stepProgress += 4 + Math.random() * 6;

      if (stepProgress >= 100) {
        stepProgress = 0;
        stepIdx++;

        if (stepIdx >= JOB_STEPS.length - 1) {
          // Simulate occasional failure for demo realism
          const shouldFail = Math.random() < 0.08;
          if (intervalRef.current) clearInterval(intervalRef.current);

          setJobs(prev => prev.map(j =>
            j.id === job.id
              ? {
                  ...j,
                  status: shouldFail ? 'failed' : 'completed',
                  step: 'done',
                  stepProgress: 100,
                  outputs: shouldFail ? [] : [`/Bounces/${j.sessionName}.wav`],
                  error: shouldFail ? 'DAW session could not be opened' : undefined,
                }
              : j
          ));

          if (shouldFail) addLog(`❌ Failed: ${job.sessionName}`);
          else addLog(`✅ Completed: ${job.sessionName}`);

          setTimeout(() => {
            if (!stoppedRef.current) setCurrentJobIndex(i => i + 1);
          }, 600);
          return;
        }
      }

      setJobs(prev => prev.map(j =>
        j.id === job.id
          ? { ...j, status: 'running', step: JOB_STEPS[Math.min(stepIdx, JOB_STEPS.length - 2)], stepProgress }
          : j
      ));
    };

    intervalRef.current = setInterval(tick, 80);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [runState, currentJobIndex, addLog]);

  // Complete check when all jobs done
  useEffect(() => {
    if (runState !== 'running') return;
    const current = jobsRef.current;
    const allDone = current.length > 0 && current.every(j => j.status === 'completed' || j.status === 'failed');
    if (allDone && currentJobIndex === -1) {
      const succ = current.filter(j => j.status === 'completed').length;
      const fail = current.filter(j => j.status === 'failed').length;
      setResult({ total: current.length, succeeded: succ, failed: fail, outputs: [], errors: [], durationMs: 0 });
      setRunState('complete');
    }
  }, [jobs, runState, currentJobIndex]);

  const completedCount = jobs.filter(j => j.status === 'completed').length;
  const failedCount = jobs.filter(j => j.status === 'failed').length;

  return (
    <div className="app">
      <Header />
      <main className="app-main">
        <QueuePanel
          jobs={jobs}
          runState={runState}
          onAddJobs={addJobs}
          onRemoveJob={removeJob}
          onClearAll={clearJobs}
        />
        <ControlCenter
          jobs={jobs}
          runState={runState}
          currentJobIndex={currentJobIndex}
          result={result}
          logMessages={logMessages}
          completedCount={completedCount}
          failedCount={failedCount}
          onStart={startBatch}
          onPause={pauseBatch}
          onStop={stopBatch}
          onClear={clearJobs}
        />
        <ConfigPanel config={config} onChange={setConfig} runState={runState} />
      </main>
      <StatusBar
        runState={runState}
        jobCount={jobs.length}
        completedCount={completedCount}
        failedCount={failedCount}
      />
    </div>
  );
}
