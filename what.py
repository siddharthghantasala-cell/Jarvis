#!/usr/bin/env python3
"""
LinkedIn Message Box Finder - 5 second delay
"""
import pyautogui
import io
import requests
import re
import os
import base64
import time

# Your endpoint
ENDPOINT_URL = "https://k0mkv3j05m8vnmea.us-east-1.aws.endpoints.huggingface.cloud"

# Get HF token
HF_TOKEN = os.environ.get('HF_TOKEN')
if not HF_TOKEN:
    HF_TOKEN = input("Enter your HuggingFace token: ").strip()

def take_screenshot():
    """Take a screenshot and return as bytes"""
    screenshot = pyautogui.screenshot()
    buffered = io.BytesIO()
    screenshot.save(buffered, format="PNG")
    return buffered.getvalue()

def find_element(query, screenshot_bytes):
    """
    Find element using UI-TARS grounding model
    """
    print(f"Looking for: {query}")
    
    # Convert screenshot to base64
    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    
    # Prepare the prompt
    prompt = f"Query:{query}\nOutput only the coordinate of one point in your response.\n"
    
    # vLLM uses OpenAI-compatible chat completions format
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Format for vision models in vLLM
    payload = {
        "model": "ByteDance-Seed/UI-TARS-1.5-7B",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
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
    
    try:
        print("Sending request to grounding model...")
        url = f"{ENDPOINT_URL}/v1/chat/completions"
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract text from response
            if 'choices' in result and len(result['choices']) > 0:
                text = result['choices'][0]['message']['content']
                print(f"Model response: {text}")
                
                # Parse coordinates
                numericals = re.findall(r"\d+", text)
                if len(numericals) >= 2:
                    coords = [int(numericals[0]), int(numericals[1])]
                    print(f"✅ Found coordinates: {coords}")
                    return coords
                else:
                    print(f"❌ Could not parse coordinates from response")
            else:
                print(f"❌ Unexpected response format: {result}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
        
        return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*60)
    print("LinkedIn Message Box Finder")
    print("="*60)
    
    print("\n🔵 Make sure LinkedIn is open in your browser!")
    print("🔵 Navigate to a conversation or messaging page")
    print("\n⏱️  Starting in 5 seconds...")
    
    # Count down
    for i in range(5, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n📸 Taking screenshot...")
    screenshot = take_screenshot()
    
    print("\n🔍 Searching for LinkedIn message box...")
    
    # Try different descriptions for the message box
    queries = [
        "the message input box where you type messages",
        "the text input field for writing a message",
        "the message composition box at the bottom",
    ]
    
    coords = None
    for query in queries:
        print(f"\nTrying: '{query}'")
        coords = find_element(query, screenshot)
        if coords:
            break
        print("   Didn't find it, trying next description...")
    
    if coords:
        print(f"\n{'='*60}")
        print(f"✅ FOUND IT!")
        print(f"✅ Coordinates: {coords}")
        print('='*60)
        
        print("\n🖱️  Moving mouse in 2 seconds...")
        time.sleep(2)
        
        pyautogui.moveTo(coords[0], coords[1], duration=1.5)
        print("✅ Mouse moved to message box!")
        
        # Optional: click and type a test message
        test = input("\nClick and type a test message? (y/n): ")
        if test.lower() == 'y':
            pyautogui.click()
            time.sleep(0.5)
            pyautogui.write("Hello from Jarvis!")
            print("✅ Typed test message!")
    else:
        print(f"\n{'='*60}")
        print("❌ Could not find the message box")
        print("="*60)
        print("\nTroubleshooting:")
        print("1. Make sure you're on a LinkedIn messaging page")
        print("2. Make sure the message input box is visible")
        print("3. Try scrolling to make the input box fully visible")

if __name__ == "__main__":
    main()