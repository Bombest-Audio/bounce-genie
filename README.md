# Bounce Butler Feature-Parity Clone (Clean Room)

## TL;DR
Goal: build a **feature-parity, clean-room implementation** inspired by Bounce Butler: batch export/bounce automation for DAWs (Pro Tools, Logic Pro X, Cubase, Ableton Live) with naming/routing and “text/email me when it’s done” notifications.

**Important:** Don’t reuse Bounce Butler’s code/assets/name. This is specs, not rip-offs.

## What we’re replicating (core behavior)
- Select multiple session/project files and batch-bounce them, one by one, while you step away:contentReference[oaicite:0]{index=0}.
- Notification when finished (email first, SMS optional), because it’s meant to let you not babysit bounces:contentReference[oaicite:1]{index=1}.
- Naming: output filenames default to the session name (configurable template).
- Destinations:
  - the DAW’s bounce folder / previously-used bounce folder,
  - optional “copy finished bounces to a custom folder” workflow (Dropbox, etc.):contentReference[oaicite:2]{index=2}.
- Bounce options:
  - multiple formats (e.g., “Add MP3” produces two files per song in Pro Tools):contentReference[oaicite:3]{index=3},
  - last-used bounce settings respected (offline/online, formats) + roadmap for explicit control:contentReference[oaicite:4]{index=4}.
- “Virtual intern” design: automation drives the mouse/keyboard; user input pauses until resumed:contentReference[oaicite:5]{index=5}.
- Mac-first MVP; Windows later.

## High-level architecture
### Main components
1. **Job Queue**
   - Holds `BounceJob(session_path, naming_template, copy_dest, notification_target, options)`.
2. **DAW Adapter Layer**
   - `IDawAdapter` interface:
     - `open_session(path)`
     - `prep_bounce(selection_strategy, options)`
     - `execute_bounce(options)`
     - `detect_outputs(job)` → list of files
   - Concrete adapters:
     - `ProToolsAdapter`
     - `LogicAdapter`
     - `CubaseAdapter`
     - `AbletonAdapter`
3. **Automation Engine (macOS-first)**
   - Drives UI: menus, dialogs, shortcuts, etc.
   - Needs accessibility permissions + guardrails (timeouts, “can’t find window,” etc.).
4. **Bounce Output Detector**
   - Watches DAW bounce folder(s).
   - Detects completion per job (some yield multiple files).
5. **Naming & Routing**
   - Template engine to build final filenames/paths.
   - Copy/move finished files to optional custom folder.
6. **Notifications**
   - Email (SMTP) baseline.
   - SMS via Twilio (optional).
   - Batch summary: count, outputs, errors.

## Selection strategy (important edge-case)
From the original behavior:
- Pro Tools: bounce selected/saved range; if none, select-all:contentReference[oaicite:6]{index=6}.
- Logic/Cubase/Ableton: best to save a session copy trimmed to bounce length:contentReference[oaicite:7]{index=7}.

Define `SelectionStrategy`:
- `USE_SAVED_SELECTION` (default per DAW)
- `SELECT_ALL` (fallback)
- `TRIMMED_COPY` (explicit workflow)

## Project structure (suggested)
