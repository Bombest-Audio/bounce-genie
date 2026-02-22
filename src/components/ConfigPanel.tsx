import { useCallback } from 'react';
import type { AppConfig, RunState, DawType, BounceFormat, SelectionStrategy } from '../types';
import { DAW_LABELS, FORMAT_LABELS } from '../types';

interface Props {
  config: AppConfig;
  onChange: (cfg: AppConfig) => void;
  runState: RunState;
}

const DAW_OPTIONS: { value: DawType; icon: string }[] = [
  { value: 'protools', icon: '🎚️' },
  { value: 'logic',    icon: '🍎' },
  { value: 'cubase',   icon: '��' },
  { value: 'ableton',  icon: '🎛️' },
];

const FORMAT_OPTIONS: BounceFormat[] = ['wav', 'aiff', 'mp3', 'flac'];

const SAMPLE_RATES = [44100, 48000, 88200, 96000, 192000];
const BIT_DEPTHS = [16, 24, 32];

const SELECTION_STRATEGIES: { value: SelectionStrategy; label: string; desc: string }[] = [
  { value: 'USE_SAVED_SELECTION', label: 'Use Saved', desc: 'Respects saved range in session' },
  { value: 'SELECT_ALL', label: 'Select All', desc: 'Bounce entire timeline' },
  { value: 'TRIMMED_COPY', label: 'Trimmed Copy', desc: 'Export a trimmed session copy' },
];

const TEMPLATE_TOKENS = [
  '${session_name}',
  '${index}',
  '${index1}',
  '${date}',
  '${time}',
  '${format}',
];

export function ConfigPanel({ config, onChange, runState }: Props) {
  const disabled = runState === 'running' || runState === 'paused';

  const set = useCallback(<K extends keyof AppConfig>(key: K, value: AppConfig[K]) => {
    onChange({ ...config, [key]: value });
  }, [config, onChange]);

  const toggleFormat = useCallback((fmt: BounceFormat) => {
    const fmts = config.formats.includes(fmt)
      ? config.formats.filter(f => f !== fmt)
      : [...config.formats, fmt];
    set('formats', fmts.length ? fmts : [fmt]);
  }, [config.formats, set]);

  const appendToken = (token: string) => {
    set('namingTemplate', config.namingTemplate + token);
  };

  const pickDirectory = useCallback(async () => {
    try {
      const { open } = await import('@tauri-apps/plugin-dialog');
      const selected = await open({ directory: true });
      if (selected && typeof selected === 'string') set('copyDest', selected);
      else if (selected && typeof selected === 'object' && 'path' in selected) set('copyDest', (selected as {path:string}).path);
    } catch {
      const path = prompt('Enter output directory path:');
      if (path) set('copyDest', path);
    }
  }, [set]);

  return (
    <div className="config-panel panel">
      <div className="panel-header">
        <span className="panel-title">Configuration</span>
      </div>
      <div className="panel-scroll">

        {/* DAW */}
        <div className="config-section">
          <span className="config-section-label">DAW</span>
          <div className="radio-group">
            {DAW_OPTIONS.map(({ value, icon }) => (
              <div
                key={value}
                className={`radio-item ${config.daw === value ? 'selected' : ''}`}
                onClick={() => !disabled && set('daw', value)}
                style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
              >
                <div className="radio-dot">
                  <div className="radio-dot-inner" />
                </div>
                <span className="daw-icon">{icon}</span>
                <span className="radio-label">{DAW_LABELS[value]}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Output Formats */}
        <div className="config-section">
          <span className="config-section-label">Output Formats</span>
          <div className="checkbox-group">
            {FORMAT_OPTIONS.map(fmt => (
              <div
                key={fmt}
                className={`checkbox-item ${config.formats.includes(fmt) ? 'checked' : ''}`}
                onClick={() => !disabled && toggleFormat(fmt)}
                style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
              >
                <div className="checkbox-box">
                  {config.formats.includes(fmt) && (
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1.5 4L4 6.5L8.5 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>
                <span className="checkbox-label">{FORMAT_LABELS[fmt]}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Audio Settings */}
        <div className="config-section">
          <span className="config-section-label">Audio Settings</span>

          <div className="field-row">
            <span className="field-label">Sample Rate</span>
            <select
              className="field-select"
              value={config.sampleRate}
              onChange={e => set('sampleRate', Number(e.target.value))}
              disabled={disabled}
            >
              {SAMPLE_RATES.map(r => (
                <option key={r} value={r}>{r.toLocaleString()} Hz</option>
              ))}
            </select>
          </div>

          <div className="field-row">
            <span className="field-label">Bit Depth</span>
            <select
              className="field-select"
              value={config.bitDepth}
              onChange={e => set('bitDepth', Number(e.target.value))}
              disabled={disabled}
            >
              {BIT_DEPTHS.map(d => (
                <option key={d} value={d}>{d}-bit</option>
              ))}
            </select>
          </div>

          <div className="toggle-row">
            <span className="toggle-label">Offline Bounce (faster)</span>
            <div
              className={`toggle ${config.offline ? 'on' : ''}`}
              onClick={() => !disabled && set('offline', !config.offline)}
              style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
            >
              <div className="toggle-knob"/>
            </div>
          </div>
        </div>

        {/* Naming Template */}
        <div className="config-section">
          <span className="config-section-label">Naming Template</span>
          <input
            className="field-input-full"
            value={config.namingTemplate}
            onChange={e => set('namingTemplate', e.target.value)}
            placeholder="${session_name}"
            disabled={disabled}
          />
          <div className="token-chips">
            {TEMPLATE_TOKENS.map(t => (
              <span
                key={t}
                className="token-chip"
                onClick={() => !disabled && appendToken(t)}
                title={`Insert ${t}`}
              >
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Output Destination */}
        <div className="config-section">
          <span className="config-section-label">Output Destination</span>
          <div className="dest-row">
            <input
              className="field-input-full"
              value={config.copyDest}
              onChange={e => set('copyDest', e.target.value)}
              placeholder="Use DAW bounce folder"
              disabled={disabled}
            />
            <button
              className="btn btn-secondary"
              style={{ height: 30, padding: '0 10px', fontSize: 11, flexShrink: 0 }}
              onClick={pickDirectory}
              disabled={disabled}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 4V9C2 9.55 2.45 10 3 10H9C9.55 10 10 9.55 10 9V5C10 4.45 9.55 4 9 4H6L5 2H3C2.45 2 2 2.45 2 3V4Z" stroke="currentColor" strokeWidth="1" fill="none"/>
              </svg>
              Browse
            </button>
          </div>
        </div>

        {/* Notifications */}
        <div className="config-section">
          <span className="config-section-label">Notifications</span>
          <div className="field-row">
            <span className="field-label">Email</span>
            <input
              className="field-input"
              type="email"
              value={config.email}
              onChange={e => set('email', e.target.value)}
              placeholder="me@example.com"
              disabled={disabled}
            />
          </div>
          <div className="field-row">
            <span className="field-label">SMS</span>
            <input
              className="field-input"
              type="tel"
              value={config.phone}
              onChange={e => set('phone', e.target.value)}
              placeholder="+1 555 000 0000"
              disabled={disabled}
            />
          </div>
        </div>

        {/* Advanced */}
        <div className="config-section">
          <span className="config-section-label">Advanced</span>

          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Selection Strategy</span>
          <div className="radio-group" style={{ marginBottom: 10 }}>
            {SELECTION_STRATEGIES.map(({ value, label, desc }) => (
              <div
                key={value}
                className={`radio-item ${config.selectionStrategy === value ? 'selected' : ''}`}
                onClick={() => !disabled && set('selectionStrategy', value)}
                style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
              >
                <div className="radio-dot">
                  <div className="radio-dot-inner" />
                </div>
                <div>
                  <div className="radio-label">{label}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="toggle-row">
            <span className="toggle-label">Stop batch on error</span>
            <div
              className={`toggle ${config.stopOnError ? 'on' : ''}`}
              onClick={() => !disabled && set('stopOnError', !config.stopOnError)}
              style={{ opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}
            >
              <div className="toggle-knob"/>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
