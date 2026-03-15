"""
cquick.py - Quick click at specified coordinates
Usage: python cquick.py <x> <y>
"""
import sys
import time
from actions import ComputerActions

if len(sys.argv) != 3:
    print("Usage: python cquick.py <x> <y>")
    print("Example: python cquick.py 500 300")
    sys.exit(1)

try:
    x = int(sys.argv[1])
    y = int(sys.argv[2])
except ValueError:
    print("Error: Coordinates must be integers")
    print("Example: python cquick.py 500 300")
    sys.exit(1)

actions = ComputerActions()

print(f"Will click at ({x}, {y}) in 3 seconds...")
time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")

print(f"Moving to ({x}, {y})...")
actions.move_mouse(x, y, duration=0.5)

print("Clicking...")
actions.click()

print("✅ Done!")