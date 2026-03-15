import sys
import os
from PIL import Image
import io
import pyautogui

# Add current directory to path to import agent_s3
sys.path.append(os.getcwd())

from agent_s3 import Executor

def test_screenshot_resizing():
    print("Testing Executor.screenshot()...")
    executor = Executor(remote=False)
    
    # Get logical screen size
    screen_width, screen_height = pyautogui.size()
    print(f"Logical Screen Size: {screen_width}x{screen_height}")
    
    # Take screenshot using Executor
    screenshot_bytes = executor.screenshot()
    img = Image.open(io.BytesIO(screenshot_bytes))
    print(f"Executor Screenshot Size: {img.width}x{img.height}")
    
    if img.width == screen_width and img.height == screen_height:
        print("✅ SUCCESS: Screenshot matches logical screen size.")
    else:
        print("❌ FAILURE: Screenshot size mismatch.")
        print(f"Expected: {screen_width}x{screen_height}")
        print(f"Actual: {img.width}x{img.height}")

if __name__ == "__main__":
    test_screenshot_resizing()
