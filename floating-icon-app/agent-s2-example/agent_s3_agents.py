#!/usr/bin/env python3

import os, io, sys, time
from dotenv import load_dotenv
from PIL import Image
load_dotenv()
# from gui_agents.s2.agents.agent_s import AgentS2
from gui_agents.s3.agents.agent_s import AgentS3
# from gui_agents.s2.agents.grounding import OSWorldACI
from gui_agents.s3.agents.grounding import OSWorldACI
from gui_agents.s3.utils.local_env import LocalEnv
from orgo import Computer
import pyautogui

CONFIG = {
    "model": os.getenv("AGENT_MODEL", "gpt-4o"),
    "model_type": os.getenv("AGENT_MODEL_TYPE", "openai"),
    "grounding_model": os.getenv("GROUNDING_MODEL", "claude-3-7-sonnet-20250219"),
    "grounding_type": os.getenv("GROUNDING_MODEL_TYPE", "anthropic"),
    "search_engine": os.getenv("SEARCH_ENGINE", "none"),
    "embedding_type": os.getenv("EMBEDDING_TYPE", "openai"),
    "max_steps": int(os.getenv("MAX_STEPS", "20")),
    "step_delay": float(os.getenv("STEP_DELAY", "0.5")),
    "remote": os.getenv("USE_CLOUD_ENVIRONMENT", "false").lower() == "true"
}


class Executor:
    def __init__(self, remote=False):
        self.remote = remote
        if remote:
            self.computer = Computer()
            self.platform = "linux"
        else:
            self.pyautogui = pyautogui
            self.platform = {"win32": "windows", "darwin": "darwin"}.get(sys.platform, "linux")
    
    def screenshot(self):
        img = self.computer.screenshot() if self.remote else self.pyautogui.screenshot()
        
        if not self.remote:
            screen_width, screen_height = self.pyautogui.size()
            if img.size != (screen_width, screen_height):
                # print(f"ℹ️  Resizing screenshot from {img.size} to {(screen_width, screen_height)}")
                img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()
    
    def exec(self, code):
        if self.remote:
            result = self.computer.exec(code)
            if not result.get('success', True):
                raise Exception(result.get('error', 'Execution failed'))
            if output := result.get('output', '').strip():
                print(f"📤 {output}")
        else:
            exec(code, {"pyautogui": self.pyautogui, "time": time})


def create_agent(executor):
    params = {"engine_type": CONFIG["model_type"], "model": CONFIG["model"]}
    
    # Get screen size dynamically
    screen_width, screen_height = pyautogui.size()
    
    grounding = {
        "engine_type": CONFIG["grounding_type"], 
        "model": CONFIG["grounding_model"],
        **({"grounding_width": screen_width, "grounding_height": screen_height} if CONFIG["grounding_type"] == "anthropic" else {})
    }
    
    return AgentS3(
        worker_engine_params=params,
        grounding_agent=OSWorldACI(
            platform=executor.platform,
            engine_params_for_generation=params,
            engine_params_for_grounding=grounding,
            env=LocalEnv
        ),
        platform=executor.platform,

        # action_space="pyautogui",
        # observation_type="screenshot",
        # search_engine=CONFIG["search_engine"] if CONFIG["search_engine"] != "none" else None,
        # embedding_engine_type=CONFIG["embedding_type"],
    )


def run_task(agent, executor, instruction):
    print(f"\n🤖 Task: {instruction}\n")
    done_count = 0
    
    for step in range(CONFIG["max_steps"]):
        print(f"Step {step + 1}/{CONFIG['max_steps']}")
        
        try:
            info, action = agent.predict(instruction=instruction, observation={"screenshot": executor.screenshot()})
            if info: print(f"💭 {info}")
            
            if not action or not action[0] or action[0].strip().upper() == "DONE":
                done_count += 1
                if done_count >= 2:
                    print("✅ Complete!")
                    return True
                continue
            
            done_count = 0
            print(f"🔧 {action[0]}")
            executor.exec(action[0])
            
        except Exception as e:
            print(f"❌ Error: {e}")
            done_count = 0
        
        time.sleep(CONFIG["step_delay"])
    
    print("⏱️ Max steps reached")
    return False


def main():
    try:
        executor = Executor(CONFIG["remote"])
        agent = create_agent(executor)
        
        if len(sys.argv) > 1:
            sys.exit(0 if run_task(agent, executor, " ".join(sys.argv[1:])) else 1)
        
        print("🎮 Interactive Mode (type 'exit' to quit)\n")
        while (task := input("Task: ").strip()) != "exit":
            if task: run_task(agent, executor, task)
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()