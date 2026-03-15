import sys
import os
from PIL import Image
import io
import pyautogui
import time

# Mock Computer class since we don't have orgo
class Computer:
    def screenshot(self):
        pass
    def exec(self, code):
        pass

# Copied from agent_s3.py and modified to remove external dependencies
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
        # Mocking the screenshot for remote, but we are testing local
        img = self.computer.screenshot() if self.remote else self.pyautogui.screenshot()
        
        if not self.remote:
            screen_width, screen_height = self.pyautogui.size()
            # Logic to test:
            if img.size != (screen_width, screen_height):
                print(f"ℹ️  Resizing screenshot from {img.size} to {(screen_width, screen_height)}")
                img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()
    
    def exec(self, code):
        pass

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
