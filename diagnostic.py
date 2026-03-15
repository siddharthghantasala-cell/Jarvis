#!/usr/bin/env python3
"""
HuggingFace Endpoint Diagnostics
"""
import requests
import os

ENDPOINT_URL = "https://k0mkv3j05m8vnmea.us-east-1.aws.endpoints.huggingface.cloud"
HF_TOKEN = os.environ.get('HF_TOKEN')

if not HF_TOKEN:
    HF_TOKEN = input("Enter your HuggingFace token: ").strip()

print("="*60)
print("HuggingFace Endpoint Diagnostics")
print("="*60)

# Test 1: Basic GET
print("\n1. Testing GET request...")
try:
    response = requests.get(ENDPOINT_URL, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: GET with auth
print("\n2. Testing GET with authentication...")
try:
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.get(ENDPOINT_URL, headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Simple POST with auth
print("\n3. Testing simple POST...")
try:
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": "test"}
    response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("\nPlease answer these questions:")

print("1. Go to: https://ui.endpoints.huggingface.co/")
print("2. What is the STATUS of your endpoint?")
print("   - 🟢 Running")
print("   - 🟡 Initializing")
print("   - 🔴 Stopped/Paused")
print("   - ⚪ Failed")
print("\n3. What model did you deploy?")
print("   (e.g., ByteDance-Seed/UI-TARS-1.5-7B)")
print("\n4. Copy the EXACT endpoint URL from the dashboard")
print("   (It should look like: https://xxxxx.aws.endpoints.huggingface.cloud)")