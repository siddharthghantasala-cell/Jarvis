import pyautogui
import io
from dotenv import load_dotenv
load_dotenv()
from gui_agents.s3.agents.agent_s import AgentS3
from gui_agents.s3.agents.grounding import OSWorldACI
from gui_agents.s3.utils.local_env import LocalEnv  # Optional: for local coding environment



current_platform = "linux"  # "darwin", "windows"