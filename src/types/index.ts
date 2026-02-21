export type DawType = 'protools' | 'logic' | 'cubase' | 'ableton';
export type BounceFormat = 'wav' | 'aiff' | 'mp3' | 'flac';
export type SelectionStrategy = 'USE_SAVED_SELECTION' | 'SELECT_ALL' | 'TRIMMED_COPY';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';
export type JobStep = 'opening' | 'prepping' | 'bouncing' | 'routing' | 'done';
export type RunState = 'idle' | 'running' | 'paused' | 'complete';

export interface BounceJob {
  id: string;
  sessionPath: string;
  sessionName: string;
  dawType: DawType;
  status: JobStatus;
  step?: JobStep;
  stepProgress: number;
  outputs?: string[];
  error?: string;
}

export interface AppConfig {
  daw: DawType;
  formats: BounceFormat[];
  sampleRate: number;
  bitDepth: number;
  offline: boolean;
  selectionStrategy: SelectionStrategy;
  namingTemplate: string;
  copyDest: string;
  email: string;
  phone: string;
  stopOnError: boolean;
}

export interface BatchResult {
  total: number;
  succeeded: number;
  failed: number;
  outputs: string[];
  errors: string[];
  durationMs: number;
}

export const DAW_LABELS: Record<DawType, string> = {
  protools: 'Pro Tools',
  logic: 'Logic Pro X',
  cubase: 'Cubase',
  ableton: 'Ableton Live',
};

export const DAW_EXTENSIONS: Record<DawType, string[]> = {
  protools: ['ptx', 'pts'],
  logic: ['logicx'],
  cubase: ['cpr'],
  ableton: ['als'],
};

export const FORMAT_LABELS: Record<BounceFormat, string> = {
  wav: 'WAV',
  aiff: 'AIFF',
  mp3: 'MP3',
  flac: 'FLAC',
};

export const STEP_LABELS: Record<JobStep, string> = {
  opening: 'Opening Session',
  prepping: 'Preparing Bounce',
  bouncing: 'Bouncing Audio',
  routing: 'Routing Outputs',
  done: 'Complete',
};

export const JOB_STEPS: JobStep[] = ['opening', 'prepping', 'bouncing', 'routing', 'done'];
