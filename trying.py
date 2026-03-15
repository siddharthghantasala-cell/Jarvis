#!/usr/bin/env python3
"""
Simple Agent S demo - shows how the actions work
"""
import time
import pyautogui

# Give yourself time to position windows
print("Starting in 3 seconds... Make sure you have a text editor or browser open!")
time.sleep(3)

# Example 1: Open Spotlight (macOS) and search for something
print("Opening Spotlight...")
pyautogui.hotkey('command', 'space')
time.sleep(0.5)
pyautogui.typewrite('safari')
pyautogui.press('enter')
time.sleep(2)

# Example 2: Type some text
print("Typing text...")
pyautogui.write('Hello from Agent S!')
time.sleep(1)

# Example 3: Select all and delete
print("Selecting all text...")
pyautogui.hotkey('command', 'a')
time.sleep(0.5)
pyautogui.press('backspace')
time.sleep(1)

# Example 4: Type more text
print("Typing more text...")
text = "This is how Agent S controls your Mac!\nIt uses PyAutoGUI under the hood."
# For unicode, we'd use clipboard:
import pyperclip
pyperclip.copy(text)
pyautogui.hotkey('command', 'v')
time.sleep(1)

# Example 5: Move mouse to a specific position
print("Moving mouse to top-left...")
pyautogui.moveTo(100, 100, duration=1)
time.sleep(0.5)

# Example 6: Click at current position
print("Clicking...")
pyautogui.click()

print("\nDemo complete!")



#opening an app
# do research - wikipedia
#textoing someone
# drafting an email
#