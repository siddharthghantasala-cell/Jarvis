# Jarvis — Voice-Controlled Desktop Agent

A desktop assistant you talk to. Say "Jarvis", give a command, and it automates your computer using keyboard-only control — no mouse, no clicking. Designed with accessibility in mind, Jarvis narrates what's on screen via text-to-speech so visually impaired users can follow along.

Built with Electron + React for the UI, Picovoice for wake word / speech-to-text / TTS, and Claude for the automation brain.

## How it works

```
"Jarvis" (wake word) → Record speech → Transcribe → Voice confirmation → Agent executes → Screen narration → Completion sound
```

1. A floating icon sits on your desktop (always on top, transparent, draggable)
2. Say **"Jarvis"** — the icon glows while you speak
3. When you stop talking, it transcribes your speech and plays a voice confirmation ("On it!", "Got it!", etc.)
4. The agent takes screenshots, narrates what's on screen via TTS, decides what keyboard shortcuts to press, and executes step by step
5. After completing, it verifies the result with a final screenshot check and says **"All done!"**
6. Successful task sequences are cached for faster execution next time
7. Say **"Jarvis"** again while the agent is running to stop it

## Stack

| Component | Technology |
|---|---|
| Desktop app | Electron 30 + React 18 + TypeScript |
| Wake word | Picovoice Porcupine v4 (runs locally, "Jarvis" keyword) |
| Speech-to-text | Picovoice Leopard |
| Voice feedback | Picovoice Orca TTS (confirmations, screen narration, completion) |
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

# Pre-download the semantic search model (one-time, ~90MB)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

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

Also create `.env` in `floating-icon-app/`:

```
VITE_PICOVOICE_ACCESS_KEY=...
```

### Porcupine wake word model

You need a custom `.ppn` keyword file trained for your Picovoice access key:

1. Go to [Picovoice Console](https://console.picovoice.ai/)
2. Train a "Jarvis" wake word for **Web (WASM)** platform, **Porcupine v4**
3. Place the exported `.ppn` file in `floating-icon-app/public/Jarvis_en_wasm_v4_0_0/`

The `.ppn` file is tied to the access key that created it — if you change access keys, you must re-train and re-export.

### Run

```bash
cd floating-icon-app
npm run dev
```

## Project structure

```
├── floating-icon-app/
│   ├── electron/
│   │   ├── main.ts              # Electron main process, IPC handlers, agent lifecycle
│   │   ├── recorder.ts          # Audio recording with SoX + silence detection
│   │   ├── transcriber.ts       # Picovoice Leopard speech-to-text
│   │   ├── tts-confirmation.ts  # Picovoice Orca TTS (confirmations, narration, completion)
│   │   └── preload.ts           # IPC bridge to renderer
│   ├── src/
│   │   ├── App.tsx              # Main app — wake word, recording, agent lifecycle
│   │   └── components/
│   │       ├── SiriAnimation.tsx    # Floating icon with blob animation
│   │       └── SiriAnimation.css    # Idle + listening glow states
│   └── agent-s2-example/
│       ├── agent_s3.py              # Automation agent (grounding model + PyAutoGUI)
│       └── experience_cache.json    # Learned task sequences
├── requirements.txt
└── .env
```

## The agent

`agent_s3.py` is the brain. It:

- Takes screenshots and sends them to the grounding model with a keyboard-only action constraint
- Narrates what's on screen at each step via `NARRATION:` lines (spoken aloud by Electron via Orca TTS)
- Executes pyautogui commands (hotkey, write, press — no mouse)
- Compresses conversation history (keeps last 2 screenshots) to manage token usage
- Retries on 429 errors with exponential backoff (up to 3 retries per step)
- After completion, verifies the task via a final screenshot check
- Caches successful task sequences with semantic search (sentence-transformers) for future reuse
- Breaks tasks into reusable subtasks (e.g., "open Chrome" gets cached independently)
- Deduplicates cache entries using cosine similarity (threshold 0.85)

### Grounding model architecture

The agent uses a `GroundingModel` abstraction that makes it easy to swap the vision model:

```python
class GroundingModel(ABC):
    def analyze_screenshot(self, screenshot_b64, messages, system_prompt) -> str: ...
    def describe_screen(self, screenshot_b64) -> str: ...
    def verify_completion(self, screenshot_b64, instruction) -> tuple[bool, str]: ...
```

Currently `ClaudeGroundingModel` is the only implementation. To switch to another model (e.g., UI-TARS), create a new class implementing `GroundingModel` and change one line in `main()`.

### Accessibility features

- **Screen narration**: At each step, the grounding model describes what's on screen in 1-2 sentences. The description is spoken aloud via Orca TTS, enabling visually impaired users to follow the agent's actions.
- **Voice confirmation**: A random affirmative phrase is spoken when a command is received.
- **Completion notification**: "All done!" is spoken when the agent finishes a task.

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
- "Open YouTube and find machining videos"
- "Write the alphabet in reverse order in a new notepad"

## Known limitations

- Navigation on web pages relies on Tab key, which can be imprecise with varying page layouts
- Orca TTS cannot synthesize special characters (e.g., `*`, `**`) — screen narrations should avoid markdown formatting
- The semantic search model (~90MB) loads on first use, adding a few seconds to the first task

## License

MIT
