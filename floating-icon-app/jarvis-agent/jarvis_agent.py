#!/usr/bin/env python3

import os, io, sys, time, json, base64, re, copy
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import pyautogui
import anthropic
from dotenv import load_dotenv
load_dotenv()


# ─── Grounding Model Abstraction ───

class GroundingModel(ABC):
    """Base class for grounding models. Swap implementations to switch between Claude, UI-TARS, etc."""

    @abstractmethod
    def analyze_screenshot(self, screenshot_b64: str, messages: list, system_prompt: str) -> str:
        """Given a screenshot and message history, return the model's text response."""
        pass

    @abstractmethod
    def describe_screen(self, screenshot_b64: str) -> str:
        """Given a screenshot, return a brief spoken description of what's on screen."""
        pass

    @abstractmethod
    def verify_completion(self, screenshot_b64: str, instruction: str) -> tuple[bool, str]:
        """Verify if a task was completed. Returns (verified: bool, explanation: str)."""
        pass


class ClaudeGroundingModel(GroundingModel):
    """Claude-based grounding model implementation."""

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def analyze_screenshot(self, screenshot_b64: str, messages: list, system_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    def describe_screen(self, screenshot_b64: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe what's on screen in 1-2 short sentences for a visually impaired user. Be concise and focus on the main content and active window."},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                ],
            }],
        )
        return response.content[0].text.strip()

    def verify_completion(self, screenshot_b64: str, instruction: str) -> tuple[bool, str]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f'The task was: "{instruction}"\n\nLook at the screenshot. Was this task completed successfully? Respond with ONLY "YES" or "NO" followed by a brief reason.'},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64}},
                ],
            }],
        )
        reply = response.content[0].text.strip()
        verified = reply.upper().startswith("YES")
        return verified, reply

# Lazy-loaded embedding model
_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        print("🧠 Loading semantic search model...")
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("🧠 Model loaded.")
    return _embed_model

CONFIG = {
    "model": os.getenv("AGENT_MODEL", "claude-sonnet-4-6"),
    "max_steps": int(os.getenv("MAX_STEPS", "10")),
    "step_delay": float(os.getenv("STEP_DELAY", "0.5")),
    "max_rate_limit_retries": 3,
    "keep_images": 2,
}

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experience_cache.json")

SYSTEM_PROMPT = """You are a Windows desktop automation agent. You control the computer using ONLY keyboard commands via pyautogui.

AVAILABLE FUNCTIONS (these are the ONLY functions you may use):
- pyautogui.hotkey("key1", "key2", ...) — press key combination (e.g. "win", "ctrl", "alt", "shift", "enter", "tab", "escape", "F1"-"F12", "up", "down", "left", "right", "backspace", "delete", "space")
- pyautogui.write("text", interval=0.02) — type text characters
- pyautogui.press("key") — press a single key
- time.sleep(seconds) — wait

FORBIDDEN: Do NOT use pyautogui.click(), moveTo(), scroll(), or any mouse-based functions.

WINDOWS KEYBOARD SHORTCUTS:
- Open app: Win → type name → Enter
- Switch apps: Alt+Tab
- Close window: Alt+F4
- Browser address bar: Ctrl+L
- New browser tab: Ctrl+T
- Close tab: Ctrl+W
- Search on page: Ctrl+F
- Copy/Paste: Ctrl+C / Ctrl+V
- Select all: Ctrl+A
- Undo: Ctrl+Z
- Save: Ctrl+S
- Run dialog: Win+R
- File Explorer: Win+E
- Desktop: Win+D
- Lock: Win+L
- Task Manager: Ctrl+Shift+Escape
- Settings: Win+I

RESPONSE FORMAT:
Return ONLY a Python code block with pyautogui/time commands to execute. Multiple commands per response is encouraged.
If the task is complete (you can see the result on screen), return exactly: DONE
If the task is impossible, return exactly: FAIL

Example response for "open notepad":
```python
pyautogui.hotkey("win")
time.sleep(0.5)
pyautogui.write("notepad", interval=0.02)
time.sleep(0.5)
pyautogui.press("enter")
```

Be efficient. Combine multiple actions in one response when possible. Always add short time.sleep() between actions that trigger UI changes."""


# ─── Semantic Similarity ───

def semantic_similarity(a, b):
    """Compute cosine similarity between two strings using sentence embeddings."""
    embeddings = get_embed_model().encode([a, b])
    cos_sim = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(cos_sim)


# ─── Experience Cache ───


def load_cache(compact=False):
    if not os.path.exists(CACHE_PATH):
        return []
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    return compact_cache(cache) if compact else cache


def compact_cache(cache):
    """Remove old-format entries superseded by richer ones, and near-dupes."""
    if not cache:
        return cache
    # Encode all instructions in one batch for efficiency
    instructions = [e["instruction"] for e in cache]
    embeddings = get_embed_model().encode(instructions)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = embeddings / norms
    sim_matrix = normalized @ normalized.T

    result = []
    for i, entry in enumerate(cache):
        dominated = False
        for j, other in enumerate(cache):
            if i == j:
                continue
            if sim_matrix[i][j] > 0.85:
                other_richer = bool(other.get("plan")) and not bool(entry.get("plan"))
                other_newer = other.get("timestamp", "") > entry.get("timestamp", "")
                if other_richer or (not bool(entry.get("plan")) and other_newer):
                    dominated = True
                    break
        if not dominated:
            result.append(entry)
    if len(result) < len(cache):
        print(f"🧹 Compacted cache: {len(cache)} → {len(result)} entries")
    return result


def save_to_cache(instruction, actions, plan=None, subtasks=None):
    cache = load_cache(compact=True)
    entry = {
        "instruction": instruction,
        "actions": actions,
        "timestamp": datetime.now().isoformat(),
    }
    if plan:
        entry["plan"] = plan
    if subtasks:
        entry["subtasks"] = subtasks

    # Replace similar existing entry instead of appending
    for i, existing in enumerate(cache):
        if semantic_similarity(instruction, existing["instruction"]) > 0.85:
            cache[i] = entry
            print(f"🔄 Replaced similar cache entry: \"{existing['instruction']}\"")
            break
    else:
        cache.append(entry)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved experience to cache ({len(cache)} total entries)")


def save_subtasks_to_cache(subtasks):
    """Save each subtask as its own independent cache entry for reuse."""
    cache = load_cache()
    existing_labels = [e["instruction"] for e in cache]
    added = 0
    for st in subtasks:
        label = st.get("label", "").strip()
        if not label:
            continue

        # Skip trivially small subtasks (fewer than 2 meaningful actions)
        actions = st.get("actions", [])
        meaningful = [a for a in actions if not a.strip().startswith("time.sleep")]
        if len(meaningful) < 2:
            continue

        # Fuzzy dedup against existing entries
        if any(semantic_similarity(label, ex) > 0.8 for ex in existing_labels):
            continue

        cache.append({
            "instruction": label,
            "actions": actions,
            "plan": f"Subtask: {label}",
            "timestamp": datetime.now().isoformat(),
        })
        existing_labels.append(label)
        added += 1
    if added:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {added} subtask(s) to cache")


def find_similar(instruction, cache, max_results=3, threshold=0.85):
    scored = []
    for entry in cache:
        score = semantic_similarity(instruction, entry["instruction"])
        if score >= threshold:
            scored.append((score, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:max_results]]


def build_experience_context(instruction, cache):
    similar = find_similar(instruction, cache)
    if not similar:
        return ""
    context = """PAST EXPERIENCES (loose hints only — do NOT copy these blindly):
The following are past tasks that were somewhat similar. They may help you understand general patterns (e.g. how to open an app), but your CURRENT task may differ in important ways. Always follow the CURRENT instruction exactly. Pay close attention to specific details like "new", "open", "close", "write", etc. that distinguish this task from past ones.

"""
    for entry in similar:
        context += f'Past task: "{entry["instruction"]}"\n'
        if entry.get("plan"):
            context += f'Approach used: {entry["plan"]}\n'
        if entry.get("subtasks"):
            context += "Steps used:\n"
            for st in entry["subtasks"]:
                label = st.get("label", "step")
                actions_preview = st["actions"][0][:120] + "..." if st.get("actions") else ""
                context += f'  - {label}: {actions_preview}\n'
        else:
            actions_str = "\n".join(entry["actions"])
            context += f'Actions used:\n{actions_str}\n'
        context += "\n"
    print(f"📚 Found {len(similar)} relevant past experience(s)")
    return context


# ─── Screenshot ───

def take_screenshot():
    screenshot = pyautogui.screenshot()
    buffered = io.BytesIO()
    screenshot.save(buffered, format="PNG")
    return base64.standard_b64encode(buffered.getvalue()).decode("utf-8")


# ─── Code Extraction ───

def extract_code(response_text):
    match = re.search(r"```python\n(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = response_text.strip()
    if text in ("DONE", "FAIL"):
        return text
    if text.endswith("DONE") or "\nDONE" in text:
        return "DONE"
    if text.endswith("FAIL") or "\nFAIL" in text:
        return "FAIL"
    if "pyautogui." in text or "time.sleep" in text:
        return text
    return None


# ─── History Compression ───

def compress_messages(messages, keep_images=2):
    """Keep only the last N screenshots in message history to reduce token usage."""
    # Find indices of user messages that contain images
    image_indices = []
    for i, m in enumerate(messages):
        if m["role"] == "user" and isinstance(m["content"], list):
            if any(c.get("type") == "image" for c in m["content"]):
                image_indices.append(i)

    # Remove images from all but the last `keep_images` messages
    for idx in image_indices[:-keep_images]:
        messages[idx]["content"] = [
            c for c in messages[idx]["content"] if c.get("type") != "image"
        ]
    return messages


# ─── Post-Task Analysis ───

def generate_plan_and_subtasks(client, instruction, executed_actions):
    """Ask Claude to summarize the approach and break actions into labeled subtasks."""
    actions_text = "\n---\n".join(executed_actions)
    try:
        response = client.messages.create(
            model=CONFIG["model"],
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""A desktop automation task was completed successfully.

Task: "{instruction}"
Actions executed (in order):
{actions_text}

Respond in JSON with:
1. "plan": A one-sentence summary of the approach taken
2. "subtasks": An array of objects, each with:
   - "label": short descriptive name (e.g. "open Chrome", "navigate to URL", "fill in form")
   - "actions": array of the action strings that belong to this subtask

Group the actions into logical subtasks. Every action must appear in exactly one subtask.
Return ONLY valid JSON, no markdown fences."""
            }],
        )
        result = json.loads(response.content[0].text)
        return result.get("plan"), result.get("subtasks", [])
    except Exception as e:
        print(f"⚠️ Could not generate plan/subtasks: {e}")
        return None, []


# ─── Task Verification ───

def verify_task(grounding: GroundingModel, instruction):
    """Take a final screenshot and ask the grounding model if the task was actually completed."""
    screenshot_b64 = take_screenshot()
    try:
        verified, reply = grounding.verify_completion(screenshot_b64, instruction)
        print(f"🔍 Verification: {reply}")
        return verified
    except Exception as e:
        print(f"⚠️ Verification failed, assuming success: {e}")
        return True


# ─── Main Agent Loop ───

def run_task(client, grounding: GroundingModel, instruction, cache):
    print(f"\n🤖 Task: {instruction}\n")

    experience = build_experience_context(instruction, cache)
    messages = []
    executed_actions = []

    step = 0
    rate_limit_retries = 0

    while step < CONFIG["max_steps"]:
        print(f"Step {step + 1}/{CONFIG['max_steps']}")

        screenshot_b64 = take_screenshot()

        # Narrate the screen for accessibility
        try:
            description = grounding.describe_screen(screenshot_b64)
            print(f"NARRATION:{description}")
        except Exception as e:
            print(f"⚠️ Screen narration failed: {e}")

        user_content = []
        if step == 0:
            task_text = f"{experience}Task: {instruction}" if experience else f"Task: {instruction}"
            user_content.append({"type": "text", "text": task_text})
        else:
            user_content.append({"type": "text", "text": "Screenshot after the previous action. Continue with the task or respond DONE if complete."})

        user_content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
        })

        messages.append({"role": "user", "content": user_content})

        # Compress history: keep only last N screenshots
        compressed = compress_messages(copy.deepcopy(messages), keep_images=CONFIG["keep_images"])

        try:
            reply = grounding.analyze_screenshot(screenshot_b64, compressed, SYSTEM_PROMPT)
            messages.append({"role": "assistant", "content": reply})
            rate_limit_retries = 0  # reset on success

            code = extract_code(reply)
            if not code:
                print(f"⚠️ Could not parse response: {reply[:200]}")
                step += 1
                time.sleep(CONFIG["step_delay"])
                continue

            if code == "DONE":
                print("✅ Agent reports complete, verifying...")
                time.sleep(2)
                verified = verify_task(grounding, instruction)
                if verified and executed_actions:
                    plan, subtasks = generate_plan_and_subtasks(client, instruction, executed_actions)
                    save_to_cache(instruction, executed_actions, plan=plan, subtasks=subtasks)
                    if subtasks:
                        save_subtasks_to_cache(subtasks)
                    print("✅ Verified and cached!")
                elif not verified:
                    print("⚠️ Verification failed — not caching this attempt")
                return True

            if code == "FAIL":
                print("❌ Agent reported task is impossible")
                return False

            print(f"🔧 {code}")
            exec(code, {"pyautogui": pyautogui, "time": time})
            executed_actions.append(code)

        except anthropic.RateLimitError as e:
            rate_limit_retries += 1
            if rate_limit_retries > CONFIG["max_rate_limit_retries"]:
                print(f"❌ Rate limited {rate_limit_retries} times, giving up on this step")
                rate_limit_retries = 0
                step += 1
                continue
            retry_after = 60
            if hasattr(e, 'response') and e.response is not None:
                retry_after = int(e.response.headers.get("retry-after", 60))
            print(f"⏳ Rate limited (attempt {rate_limit_retries}/{CONFIG['max_rate_limit_retries']}), waiting {retry_after}s...")
            # Remove the user message we just added since we'll retry this step
            messages.pop()
            time.sleep(retry_after)
            continue  # retry same step, don't increment

        except Exception as e:
            print(f"❌ Error: {e}")

        step += 1
        time.sleep(CONFIG["step_delay"])

    print("⏱️ Max steps reached")
    return False


def main():
    client = anthropic.Anthropic()
    grounding = ClaudeGroundingModel(client, CONFIG["model"])

    cache = load_cache()
    print(f"📚 Experience cache: {len(cache)} entries loaded")

    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
        sys.exit(0 if run_task(client, grounding, instruction, cache) else 1)

    print("🎮 Interactive Mode (type 'exit' to quit)\n")
    while True:
        task = input("Task: ").strip()
        if task == "exit":
            break
        if task:
            run_task(client, grounding, task, cache)
            cache = load_cache()


if __name__ == "__main__":
    main()
