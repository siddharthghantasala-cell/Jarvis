"""
gtest.py - Test grounding model with a prompt
Usage: python gtest.py "description of element"
Example: python gtest.py "the search button"
"""
import sys
import time
import os
from grounding import GroundingModel

if len(sys.argv) != 2:
    print('Usage: python gtest.py "description of element"')
    print('Example: python gtest.py "the search button"')
    sys.exit(1)

description = sys.argv[1]

# Get HF token
HF_TOKEN = os.environ.get('HF_TOKEN')
if not HF_TOKEN:
    print("Error: HF_TOKEN environment variable not set")
    sys.exit(1)

print("=" * 60)
print("GROUNDING MODEL TEST")
print("=" * 60)
print(f"Looking for: {description}")
print("\nStarting in 3 seconds...")

time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")

print("\n📸 Taking screenshot...")

# Set up grounding model
grounding = GroundingModel(
    endpoint_url="https://k0mkv3j05m8vnmea.us-east-1.aws.endpoints.huggingface.cloud",
    hf_token=HF_TOKEN
)

print(f"🔍 Finding: {description}")

try:
    x, y = grounding.find_coordinates(description)
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS!")
    print("=" * 60)
    print(f"Coordinates: ({x}, {y})")
    print("=" * 60)
    
except Exception as e:
    print("\n" + "=" * 60)
    print("❌ FAILED")
    print("=" * 60)
    print(f"Error: {e}")
    sys.exit(1)