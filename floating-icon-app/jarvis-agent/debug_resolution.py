import pyautogui
from PIL import Image

width, height = pyautogui.size()
print(f"Logical Screen Size (pyautogui.size()): {width}x{height}")

screenshot = pyautogui.screenshot()
img_width, img_height = screenshot.size
print(f"Screenshot Size: {img_width}x{img_height}")

if width != img_width or height != img_height:
    print("MISMATCH DETECTED: Retina/High-DPI display likely.")
    print(f"Scaling factor: {img_width/width}")
else:
    print("No mismatch detected.")
