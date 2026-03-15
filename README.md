# Jarvis — Voice-Controlled Desktop Agent

A desktop assistant you talk to. Say "Jarvis", give a command, and it automates your computer using keyboard-only control — no mouse, no clicking.

Built with Electron + React for the UI, Picovoice for wake word and speech-to-text, and Claude for the automation brain.

## How it works

```
"Jarvis" (wake word) → Record speech → Transcribe → Agent executes keyboard commands → Verify result
```

1. A floating icon sits on your desktop (always on top, transparent, draggable)
2. Say **"Jarvis"** — the icon glows while you speak
3. When you stop talking, it transcribes your speech and hands it to the automation agent
4. The agent takes screenshots, decides what keyboard shortcuts to press, and executes step by step
5. After completing, it verifies the result with a final screenshot check
6. Successful task sequences are cached for faster execution next time
7. Say **"Jarvis"** again while the agent is running to stop it

## Stack

| Component | Technology |
|---|---|
| Desktop app | Electron 30 + React 18 + TypeScript |
| Wake word | Picovoice Porcupine (runs locally, "Jarvis" keyword) |
| Speech-to-text | Picovoice Leopard |
| Voice confirmation | Picovoice Orca TTS |
| Automation agent | Python + Claude Sonnet + PyAutoGUI (keyboard only) |
| Experience cache | Semantic search with sentence-transformers (all-MiniLM-L6-v2) |

## Setup

### Prerequisites

- Node.js 18+
- Python 3.10+
- [SoX](https://sourceforge.net/projects/sox/) installed (audio recording)
  - Windows: install to `C:\Program Files (x86)\sox-14-4-2\`
- API keys:
  - `ANTHROPIC_API_KEY` — [Anthropic](https://console.anthropic.com/)
  - `VITE_PICOVOICE_ACCESS_KEY` — [Picovoice Console](https://console.picovoice.ai/)

### Install

```bash
# Clone
git clone https://github.com/yourusername/jarvis.git
cd jarvis

# Python dependencies
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt

# Electron app
cd floating-icon-app
npm install
```

### Configure

Create `.env` in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
VITE_PICOVOICE_ACCESS_KEY=...
```

### Run

```bash
cd floating-icon-app
npm run dev
```

## Project structure

```
├── floating-icon-app/
│   ├── electron/
│   │   ├── main.ts          # Electron main process, IPC handlers
│   │   ├── recorder.ts      # Audio recording with SoX + silence detection
│   │   ├── transcriber.ts   # Picovoice Leopard speech-to-text
│   │   ├── tts-confirmation.ts  # Picovoice Orca voice feedback
│   │   └── preload.ts       # IPC bridge to renderer
│   ├── src/
│   │   ├── App.tsx           # Main app — wake word, recording, agent lifecycle
│   │   └── components/
│   │       ├── SiriAnimation.tsx   # Floating icon with blob animation
│   │       └── SiriAnimation.css   # Idle + listening glow states
│   └── agent-s2-example/
│       ├── agent_s3.py       # Automation agent (Claude + PyAutoGUI)
│       └── experience_cache.json   # Learned task sequences
├── requirements.txt
└── .env
```

## The agent

`agent_s3.py` is the brain. It:

- Takes screenshots and sends them to Claude with a keyboard-only action constraint
- Executes pyautogui commands (hotkey, write, press — no mouse)
- Compresses conversation history (keeps last 2 screenshots) to avoid rate limits
- Retries on 429 errors with exponential backoff (up to 3 retries per step)
- After completion, verifies the task actually worked via a final screenshot check
- Caches successful task sequences with semantic search (sentence-transformers) for future reuse
- Breaks tasks into reusable subtasks (e.g., "open Chrome" gets cached independently)
- Deduplicates cache entries using cosine similarity (threshold 0.85)

### Agent config (environment variables)

| Variable | Default | Description |
|---|---|---|
| `AGENT_MODEL` | `claude-sonnet-4-6` | Claude model to use |
| `MAX_STEPS` | `10` | Maximum actions per task |
| `STEP_DELAY` | `0.5` | Seconds between steps |

## Example commands

- "Open notepad and type hello world"
- "Search for cute cat videos online"
- "Open command prompt"
- "Go to Google Calendar and create an event"

## License

MIT
