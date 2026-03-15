# grounding.py - WITH COORDINATE SCALING

import requests
import base64
import re
import pyautogui
import io
import os
from typing import Dict, Tuple

class GroundingModel:
    def __init__(
        self, 
        endpoint_url: str, 
        hf_token: str,
        model_resolution: Tuple[int, int] = (1920, 1080)  # UI-TARS training resolution
    ):
        self.endpoint_url = endpoint_url
        self.hf_token = hf_token
        self.model_width, self.model_height = model_resolution
        
        # Get actual screen resolution
        self.screen_width, self.screen_height = pyautogui.size()
        
        print(f"📐 Grounding Model Setup:")
        print(f"   Model resolution: {self.model_width}x{self.model_height}")
        print(f"   Screen resolution: {self.screen_width}x{self.screen_height}")
        print(f"   Scale factor: X={self.screen_width/self.model_width:.2f}, Y={self.screen_height/self.model_height:.2f}")
    
    def resize_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """
        Scale coordinates from model resolution to screen resolution.
        
        Args:
            x, y: Coordinates in model's resolution (e.g., 1920x1080)
            
        Returns:
            Scaled coordinates for actual screen
        """
        scaled_x = round(x * self.screen_width / self.model_width)
        scaled_y = round(y * self.screen_height / self.model_height)
        return scaled_x, scaled_y
    
    def find_coordinates(self, element_description: str) -> Tuple[int, int]:
        """
        Find coordinates of a UI element from description.
        
        Args:
            element_description: Natural language description of what to find
            
        Returns:
            (x, y) coordinates scaled to your screen resolution
        """
        # Take screenshot
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        screenshot_bytes = buffered.getvalue()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Prepare prompt - TELL THE MODEL THE RESOLUTION
        prompt = f"""Query:{element_description}
Output only the coordinate of one point in your response.
The image resolution is {self.model_width}x{self.model_height}.
"""
        
        # Call grounding model
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "ByteDance-Seed/UI-TARS-1.5-7B",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 100,
            "temperature": 0.0
        }
        
        response = requests.post(
            f"{self.endpoint_url}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"   Raw model response: {text}")
            
            # Parse coordinates (these are in model resolution)
            numericals = re.findall(r"\d+", text)
            if len(numericals) >= 2:
                model_x = int(numericals[0])
                model_y = int(numericals[1])
                print(f"   Model coordinates (in {self.model_width}x{self.model_height}): ({model_x}, {model_y})")
                
                # Scale to actual screen resolution
                screen_x, screen_y = self.resize_coordinates(model_x, model_y)
                print(f"   Scaled coordinates (in {self.screen_width}x{self.screen_height}): ({screen_x}, {screen_y})")
                
                return screen_x, screen_y
        
        raise Exception(f"Failed to find coordinates for: {element_description}")


# SmartActions stays the same
from actions import ComputerActions

class SmartActions(ComputerActions):
    """
    Actions + Grounding = Smart Actions that can find UI elements
    """
    
    def __init__(self, grounding_model: GroundingModel = None):
        super().__init__()
        self.grounding = grounding_model
    
    def click_element(self, description: str, button: str = 'left', clicks: int = 1) -> Dict:
        """
        Click on a UI element by description.
        
        Args:
            description: What to click (e.g., "the send button")
            
        Example:
            click_element("the LinkedIn message input box")
        """
        print(f"🔍 Finding: {description}")
        x, y = self.grounding.find_coordinates(description)
        print(f"✅ Found at: ({x}, {y})")
        
        return self.click(x, y, button=button, clicks=clicks)
    
    def type_in_element(self, description: str, text: str) -> Dict:
        """
        Click an element and type text into it.
        
        Args:
            description: What to click (e.g., "the search box")
            text: What to type
            
        Example:
            type_in_element("the message input box", "Hello world!")
        """
        # Click to focus
        self.click_element(description)
        self.wait(0.3)
        
        # Type text
        return self.type_text(text)