import pyautogui
import time

print("Move your mouse to the desired position...")
print("The coordinates will be captured in 3 seconds...")

# Countdown
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# Get mouse position
x, y = pyautogui.position()
print(f"\nMouse Coordinates: X={x}, Y={y}")