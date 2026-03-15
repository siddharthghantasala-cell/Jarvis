"""
test_grounding.py - Test if grounding model is working with your actions
"""
import os
import time
from grounding import GroundingModel, SmartActions


# Get your HF token
HF_TOKEN = os.environ.get('HF_TOKEN')
if not HF_TOKEN:
    HF_TOKEN = input("Enter your HuggingFace token: ").strip()

# Set up grounding model
print("=" * 60)
print("GROUNDING MODEL TEST")
print("=" * 60)

grounding = GroundingModel(
    endpoint_url="https://k0mkv3j05m8vnmea.us-east-1.aws.endpoints.huggingface.cloud",
    hf_token=HF_TOKEN
)

# Create smart actions
actions = SmartActions(grounding)

print("\n📋 Test Checklist:")
print("1. Open a browser (Chrome/Safari)")
print("2. Go to any website with visible UI elements")
print("3. Make sure the window is visible and not minimized")
print("\nStarting in 5 seconds...")

for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

print("\n" + "=" * 60)
print("TEST 1: Find and highlight browser address bar")
print("=" * 60)

try:
    print("\n🔍 Looking for the browser address bar...")
    x, y = grounding.find_coordinates("the browser address bar at the top")
    print(f"✅ Found at coordinates: ({x}, {y})")
    
    print("\n🖱️  Moving mouse to show you where it found it...")
    actions.move_mouse(x, y, duration=1.5)
    print("✅ Mouse moved! Is it pointing at the address bar?")
    
    response = input("\nDid it find the address bar correctly? (y/n): ")
    if response.lower() == 'y':
        print("✅ TEST 1 PASSED")
    else:
        print("❌ TEST 1 FAILED")
        
except Exception as e:
    print(f"❌ TEST 1 FAILED: {e}")

print("\n" + "=" * 60)
print("TEST 2: Find and click an element")
print("=" * 60)

try:
    print("\nWhat should I look for and click?")
    print("Examples:")
    print("  - 'the search button'")
    print("  - 'the back button'")
    print("  - 'any link on the page'")
    
    target = input("\nEnter description: ").strip()
    
    if target:
        print(f"\n🔍 Looking for: {target}")
        result = actions.click_element(target)
        print(f"✅ Clicked at: ({result['x']}, {result['y']})")
        
        response = input("\nDid it click the right thing? (y/n): ")
        if response.lower() == 'y':
            print("✅ TEST 2 PASSED")
        else:
            print("❌ TEST 2 FAILED")
    else:
        print("⏭️  Skipping TEST 2")
        
except Exception as e:
    print(f"❌ TEST 2 FAILED: {e}")

print("\n" + "=" * 60)
print("TEST 3: Find input box and type")
print("=" * 60)

try:
    print("\nMake sure there's a visible text input box on screen")
    print("(like a search bar, message box, etc.)")
    
    response = input("\nReady? Press Enter to continue or 'n' to skip: ")
    
    if response.lower() != 'n':
        print("\n🔍 Looking for a text input box...")
        result = actions.type_in_element(
            "the text input box",
            "Hello from grounding model!"
        )
        print("✅ Typed text!")
        
        response = input("\nDid it type in the correct input box? (y/n): ")
        if response.lower() == 'y':
            print("✅ TEST 3 PASSED")
        else:
            print("❌ TEST 3 FAILED")
    else:
        print("⏭️  Skipping TEST 3")
        
except Exception as e:
    print(f"❌ TEST 3 FAILED: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE!")
print("=" * 60)
print("\nSummary:")
print("If most tests passed, your grounding model is working!")
print("If tests failed, check:")
print("  1. Is your HF endpoint running?")
print("  2. Is the UI element clearly visible on screen?")
print("  3. Are you giving clear descriptions?")