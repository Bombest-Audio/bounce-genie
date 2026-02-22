
import { getCurrentWindow } from '@tauri-apps/api/window';

async function minimize() {
  try { await getCurrentWindow().minimize(); } catch {}
}
async function maximize() {
  try {
    const win = getCurrentWindow();
    if (await win.isMaximized()) await win.unmaximize();
    else await win.maximize();
  } catch {}
}
async function closeWindow() {
  try { await getCurrentWindow().close(); } catch {}
}

export function Header() {
  return (
    <header className="app-header">
      <div className="app-header-left">
        <div className="app-icon">
          <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
            <ellipse cx="16" cy="22" rx="10" ry="4" fill="url(#lamp-base)"/>
            <path d="M10 22C10 22 8 14 10 10C12 6 14 4 16 4C18 4 20 6 22 10C24 14 22 22 22 22" fill="url(#lamp-body)"/>
            <ellipse cx="16" cy="22" rx="10" ry="3.5" fill="none" stroke="url(#lamp-stroke)" strokeWidth="1"/>
            <path d="M14 4C14 4 13 2 16 1C19 2 18 4 18 4" fill="url(#spout)" opacity="0.9"/>
            <circle cx="23" cy="6" r="5" fill="url(#flame-bg)" opacity="0.3"/>
            <path d="M23 3C23 3 20 5 21 7C22 9 25 8 25 6C25 4 23 3 23 3Z" fill="url(#flame)"/>
            <defs>
              <linearGradient id="lamp-base" x1="6" y1="22" x2="26" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#7C3AED"/>
                <stop offset="1" stopColor="#0891B2"/>
              </linearGradient>
              <linearGradient id="lamp-body" x1="10" y1="4" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#9B73F8"/>
                <stop offset="1" stopColor="#22D3EE" stopOpacity="0.8"/>
              </linearGradient>
              <linearGradient id="lamp-stroke" x1="6" y1="22" x2="26" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#C4B5FD" stopOpacity="0.6"/>
                <stop offset="1" stopColor="#67E8F9" stopOpacity="0.6"/>
              </linearGradient>
              <linearGradient id="spout" x1="14" y1="1" x2="18" y2="4" gradientUnits="userSpaceOnUse">
                <stop stopColor="#9B73F8"/>
                <stop offset="1" stopColor="#22D3EE"/>
              </linearGradient>
              <radialGradient id="flame-bg" cx="0.5" cy="0.5" r="0.5">
                <stop stopColor="#FCD34D"/>
              </radialGradient>
              <linearGradient id="flame" x1="21" y1="3" x2="25" y2="9" gradientUnits="userSpaceOnUse">
                <stop stopColor="#FDE68A"/>
                <stop offset="1" stopColor="#F59E0B"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div className="app-title">
          <span className="app-name">Bounce Genie</span>
          <span className="app-subtitle">Batch DAW Automation</span>
        </div>
      </div>
      <div className="app-header-right">
        <span className="app-version">v0.1.0</span>
        <div className="window-controls">
          <button className="wc-btn wc-minimize" onClick={minimize} title="Minimize">
            <svg width="10" height="1" viewBox="0 0 10 1"><rect width="10" height="1" rx="0.5" fill="currentColor"/></svg>
          </button>
          <button className="wc-btn wc-maximize" onClick={maximize} title="Maximize">
            <svg width="10" height="10" viewBox="0 0 10 10"><rect x="0.5" y="0.5" width="9" height="9" rx="2" stroke="currentColor" strokeWidth="1" fill="none"/></svg>
          </button>
          <button className="wc-btn wc-close" onClick={closeWindow} title="Close">
            <svg width="10" height="10" viewBox="0 0 10 10"><path d="M1 1L9 9M9 1L1 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </button>
        </div>
      </div>
    </header>
  );
}
