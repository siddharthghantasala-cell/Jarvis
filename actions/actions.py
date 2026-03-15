"""
actions.py - Basic building block actions for computer control

These are atomic, composable actions that can be stacked to accomplish complex tasks.
Each action is simple, predictable, and does ONE thing well.
"""

import pyautogui
import time
import subprocess
import platform
from typing import List, Dict, Any


class ComputerActions:
    """
    Simple, composable actions for computer control.
    Each method is a building block that can be chained together.
    """
    
    def __init__(self, platform_name: str = None):
        self.platform = platform_name or platform.system().lower()
        # darwin = macOS, linux = Linux, windows = Windows
        
    # ==================== KEYBOARD ACTIONS ====================
    
    def type_text(self, text: str, interval: float = 0.0) -> Dict:
        """
        Type text character by character.
        
        Args:
            text: The text to type
            interval: Delay between keystrokes (seconds)
        
        Example:
            type_text("hello world")
        """
        pyautogui.write(text, interval=interval)
        return {"status": "success", "action": "type_text", "text": text}
    
    def press_key(self, key: str) -> Dict:
        """
        Press a single key.
        
        Args:
            key: Key name (e.g., 'enter', 'space', 'tab', 'escape', 'backspace')
        
        Example:
            press_key('enter')
        """
        pyautogui.press(key)
        return {"status": "success", "action": "press_key", "key": key}
    
    def hotkey(self, keys: List[str]) -> Dict:
        """
        Press a combination of keys simultaneously.
        Uses keyDown/keyUp for better reliability on macOS.
        
        Args:
            keys: List of keys to press together
        
        Example:
            hotkey(['command', 'c'])  # Copy on Mac
            hotkey(['ctrl', 'v'])      # Paste on Windows/Linux
        """
        # Press all keys down
        for key in keys:
            pyautogui.keyDown(key)
            time.sleep(0.05)
        
        # Release all keys in reverse order
        for key in reversed(keys):
            pyautogui.keyUp(key)
            time.sleep(0.05)
        
        return {"status": "success", "action": "hotkey", "keys": keys}
    
    # ==================== MOUSE ACTIONS ====================
    
    def move_mouse(self, x: int, y: int, duration: float = 0) -> Dict:
        """
        Move mouse to absolute coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Time to take moving (seconds)
        
        Example:
            move_mouse(100, 200)
        """
        pyautogui.moveTo(x, y, duration=duration)
        return {"status": "success", "action": "move_mouse", "x": x, "y": y}
    
    def click(self, x: int = None, y: int = None, button: str = 'left', clicks: int = 1) -> Dict:
        """
        Click the mouse.
        
        Args:
            x: X coordinate (if None, clicks at current position)
            y: Y coordinate (if None, clicks at current position)
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks (2 for double-click)
        
        Example:
            click(100, 200)
            click(button='right')  # Right-click at current position
            click(100, 200, clicks=2)  # Double-click
        """
        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)
        else:
            pyautogui.click(clicks=clicks, button=button)
        
        return {"status": "success", "action": "click", "x": x, "y": y, "button": button}
    
    def drag(self, from_x: int, from_y: int, to_x: int, to_y: int, duration: float = 0.5, button: str = 'left') -> Dict:
        """
        Drag from one point to another.
        
        Args:
            from_x: Starting X coordinate
            from_y: Starting Y coordinate
            to_x: Ending X coordinate
            to_y: Ending Y coordinate
            duration: Time to take dragging
            button: Mouse button to use
        
        Example:
            drag(100, 100, 200, 200)  # Drag from (100,100) to (200,200)
        """
        pyautogui.moveTo(from_x, from_y)
        pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
        return {"status": "success", "action": "drag", "from": (from_x, from_y), "to": (to_x, to_y)}
    
    def scroll(self, clicks: int, x: int = None, y: int = None) -> Dict:
        """
        Scroll the mouse wheel.
        
        Args:
            clicks: Amount to scroll (positive = up, negative = down)
            x: X position to scroll at (optional)
            y: Y position to scroll at (optional)
        
        Example:
            scroll(5)   # Scroll up
            scroll(-3)  # Scroll down
        """
        if x is not None and y is not None:
            pyautogui.moveTo(x, y)
            time.sleep(0.2)
        
        pyautogui.scroll(clicks)
        return {"status": "success", "action": "scroll", "clicks": clicks}
    
    # ==================== APPLICATION CONTROL ====================
    
    def open_app(self, app_name: str) -> Dict:
        """
        Open an application.
        
        Args:
            app_name: Name of the application
        
        Example:
            open_app('Chrome')
            open_app('TextEdit')
        """
        if self.platform == 'darwin':
            # macOS: Use Spotlight with keyDown/keyUp for reliability
            pyautogui.keyDown('command')
            time.sleep(0.1)
            pyautogui.press('space')
            time.sleep(0.1)
            pyautogui.keyUp('command')
            
            time.sleep(1.5)  # Wait for Spotlight to appear
            pyautogui.write(app_name, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            
        elif self.platform == 'linux':
            # Linux: Use application launcher
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_name)
            time.sleep(0.3)
            pyautogui.press('enter')
            
        elif self.platform == 'windows':
            # Windows: Use Start menu
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_name)
            time.sleep(0.3)
            pyautogui.press('enter')
        
        time.sleep(1.5)  # Give app time to open
        return {"status": "success", "action": "open_app", "app_name": app_name}
    
    def close_window(self) -> Dict:
        """
        Close the current window.
        
        Example:
            close_window()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('w')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('w')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        return {"status": "success", "action": "close_window"}
    
    def switch_window(self) -> Dict:
        """
        Switch to next window (Alt+Tab / Cmd+Tab).
        
        Example:
            switch_window()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('tab')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('alt')
            time.sleep(0.05)
            pyautogui.press('tab')
            time.sleep(0.05)
            pyautogui.keyUp('alt')
        
        time.sleep(0.3)
        return {"status": "success", "action": "switch_window"}
    
    def new_tab(self) -> Dict:
        """
        Open a new tab (Cmd+T / Ctrl+T).
        
        Example:
            new_tab()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('t')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('t')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.3)
        return {"status": "success", "action": "new_tab"}
    
    def close_tab(self) -> Dict:
        """
        Close current tab (Cmd+W / Ctrl+W).
        
        Example:
            close_tab()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('w')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('w')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        return {"status": "success", "action": "close_tab"}
    
    # ==================== CLIPBOARD ACTIONS ====================
    
    def copy(self) -> Dict:
        """
        Copy selected content to clipboard.
        
        Example:
            copy()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('c')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('c')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.1)
        return {"status": "success", "action": "copy"}
    
    def paste(self) -> Dict:
        """
        Paste from clipboard.
        
        Example:
            paste()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('v')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('v')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.1)
        return {"status": "success", "action": "paste"}
    
    def cut(self) -> Dict:
        """
        Cut selected content to clipboard.
        
        Example:
            cut()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('x')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('x')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.1)
        return {"status": "success", "action": "cut"}
    
    def select_all(self) -> Dict:
        """
        Select all content.
        
        Example:
            select_all()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('a')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('a')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        return {"status": "success", "action": "select_all"}
    
    # ==================== TEXT EDITING ====================
    
    def undo(self) -> Dict:
        """
        Undo last action.
        
        Example:
            undo()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('z')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('z')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        return {"status": "success", "action": "undo"}
    
    def redo(self) -> Dict:
        """
        Redo last undone action.
        
        Example:
            redo()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            pyautogui.keyDown('shift')
            time.sleep(0.05)
            pyautogui.press('z')
            time.sleep(0.05)
            pyautogui.keyUp('shift')
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('y')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        return {"status": "success", "action": "redo"}
    
    def find(self) -> Dict:
        """
        Open find dialog.
        
        Example:
            find()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('f')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('f')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.3)
        return {"status": "success", "action": "find"}
    
    def save(self) -> Dict:
        """
        Save current document.
        
        Example:
            save()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('s')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('s')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.2)
        return {"status": "success", "action": "save"}
    
    # ==================== BROWSER ACTIONS ====================
    
    def open_url(self, url: str) -> Dict:
        """
        Open a URL (assumes browser is open, navigates to address bar and types URL).
        
        Args:
            url: URL to open
        
        Example:
            open_url('https://github.com')
        """
        # Focus address bar
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('l')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('l')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        time.sleep(0.3)
        pyautogui.write(url, interval=0.02)
        pyautogui.press('enter')
        time.sleep(1.0)
        
        return {"status": "success", "action": "open_url", "url": url}
    
    def refresh_page(self) -> Dict:
        """
        Refresh the current page.
        
        Example:
            refresh_page()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('r')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('r')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')
        
        return {"status": "success", "action": "refresh_page"}
    
    def go_back(self) -> Dict:
        """
        Go back in browser history.
        
        Example:
            go_back()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('[')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('alt')
            time.sleep(0.05)
            pyautogui.press('left')
            time.sleep(0.05)
            pyautogui.keyUp('alt')
        
        return {"status": "success", "action": "go_back"}
    
    def go_forward(self) -> Dict:
        """
        Go forward in browser history.
        
        Example:
            go_forward()
        """
        if self.platform == 'darwin':
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press(']')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:
            pyautogui.keyDown('alt')
            time.sleep(0.05)
            pyautogui.press('right')
            time.sleep(0.05)
            pyautogui.keyUp('alt')
        
        return {"status": "success", "action": "go_forward"}
    
    # ==================== UTILITY ACTIONS ====================
    
    def wait(self, seconds: float) -> Dict:
        """
        Wait/pause for specified time.
        
        Args:
            seconds: Time to wait
        
        Example:
            wait(2.0)  # Wait 2 seconds
        """
        time.sleep(seconds)
        return {"status": "success", "action": "wait", "seconds": seconds}
    
    def screenshot(self, filename: str = None) -> Dict:
        """
        Take a screenshot.
        
        Args:
            filename: Path to save screenshot (optional)
        
        Example:
            screenshot('output.png')
        """
        img = pyautogui.screenshot()
        
        if filename:
            img.save(filename)
            return {"status": "success", "action": "screenshot", "saved": filename}
        
        return {"status": "success", "action": "screenshot", "image": img}
    
    def get_mouse_position(self) -> Dict:
        """
        Get current mouse position.
        
        Example:
            get_mouse_position()
        """
        x, y = pyautogui.position()
        return {"status": "success", "action": "get_mouse_position", "x": x, "y": y}
    
    def get_screen_size(self) -> Dict:
        """
        Get screen dimensions.
        
        Example:
            get_screen_size()
        """
        width, height = pyautogui.size()
        return {"status": "success", "action": "get_screen_size", "width": width, "height": height}


# ==================== ACTION REGISTRY ====================

def get_action_descriptions() -> Dict[str, Dict[str, Any]]:
    """
    Get a dictionary of all available actions with their descriptions.
    This is what you'd pass to the AI to let it know what it can do.
    """
    actions = ComputerActions()
    
    return {
        # Keyboard
        "type_text": {
            "description": "Type text character by character",
            "params": {"text": "string", "interval": "float (optional)"},
            "example": "type_text('hello world')"
        },
        "press_key": {
            "description": "Press a single key",
            "params": {"key": "string (e.g., 'enter', 'tab', 'escape')"},
            "example": "press_key('enter')"
        },
        "hotkey": {
            "description": "Press multiple keys simultaneously",
            "params": {"keys": "list of strings"},
            "example": "hotkey(['command', 'c'])"
        },
        
        # Mouse
        "move_mouse": {
            "description": "Move mouse to coordinates",
            "params": {"x": "int", "y": "int", "duration": "float (optional)"},
            "example": "move_mouse(100, 200)"
        },
        "click": {
            "description": "Click the mouse",
            "params": {"x": "int (optional)", "y": "int (optional)", "button": "string (optional)", "clicks": "int (optional)"},
            "example": "click(100, 200) or click(button='right')"
        },
        "drag": {
            "description": "Drag from one point to another",
            "params": {"from_x": "int", "from_y": "int", "to_x": "int", "to_y": "int"},
            "example": "drag(100, 100, 200, 200)"
        },
        "scroll": {
            "description": "Scroll mouse wheel (positive=up, negative=down)",
            "params": {"clicks": "int", "x": "int (optional)", "y": "int (optional)"},
            "example": "scroll(5) or scroll(-3)"
        },
        
        # Applications
        "open_app": {
            "description": "Open an application by name",
            "params": {"app_name": "string"},
            "example": "open_app('Chrome')"
        },
        "close_window": {
            "description": "Close the current window",
            "params": {},
            "example": "close_window()"
        },
        "switch_window": {
            "description": "Switch to next window (Alt+Tab)",
            "params": {},
            "example": "switch_window()"
        },
        "new_tab": {
            "description": "Open new tab in current app",
            "params": {},
            "example": "new_tab()"
        },
        "close_tab": {
            "description": "Close current tab",
            "params": {},
            "example": "close_tab()"
        },
        
        # Clipboard
        "copy": {
            "description": "Copy selected content",
            "params": {},
            "example": "copy()"
        },
        "paste": {
            "description": "Paste from clipboard",
            "params": {},
            "example": "paste()"
        },
        "cut": {
            "description": "Cut selected content",
            "params": {},
            "example": "cut()"
        },
        "select_all": {
            "description": "Select all content",
            "params": {},
            "example": "select_all()"
        },
        
        # Text editing
        "undo": {
            "description": "Undo last action",
            "params": {},
            "example": "undo()"
        },
        "redo": {
            "description": "Redo last undone action",
            "params": {},
            "example": "redo()"
        },
        "find": {
            "description": "Open find dialog",
            "params": {},
            "example": "find()"
        },
        "save": {
            "description": "Save current document",
            "params": {},
            "example": "save()"
        },
        
        # Browser
        "open_url": {
            "description": "Navigate to URL in browser",
            "params": {"url": "string"},
            "example": "open_url('https://github.com')"
        },
        "refresh_page": {
            "description": "Refresh current page",
            "params": {},
            "example": "refresh_page()"
        },
        "go_back": {
            "description": "Go back in browser history",
            "params": {},
            "example": "go_back()"
        },
        "go_forward": {
            "description": "Go forward in browser history",
            "params": {},
            "example": "go_forward()"
        },
        
        # Utility
        "wait": {
            "description": "Pause for specified seconds",
            "params": {"seconds": "float"},
            "example": "wait(2.0)"
        },
        "screenshot": {
            "description": "Take a screenshot",
            "params": {"filename": "string (optional)"},
            "example": "screenshot('output.png')"
        },
        "get_mouse_position": {
            "description": "Get current mouse coordinates",
            "params": {},
            "example": "get_mouse_position()"
        },
        "get_screen_size": {
            "description": "Get screen width and height",
            "params": {},
            "example": "get_screen_size()"
        }
    }


if __name__ == "__main__":
    # Test the actions
    actions = ComputerActions()
    
    print("Available Actions:")
    print("=" * 60)
    
    for name, info in get_action_descriptions().items():
        print(f"\n{name}()")
        print(f"  Description: {info['description']}")
        print(f"  Example: {info['example']}")