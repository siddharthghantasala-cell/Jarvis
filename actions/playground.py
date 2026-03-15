"""
test_grounding_accuracy.py - Measure how off the grounding model is

This will:
1. Show you test points on screen
2. Ask grounding model to find them
3. Calculate the error
"""
import os
import time
import pyautogui
from PIL import Image, ImageDraw, ImageFont
import io
from grounding import GroundingModel

# Get HF token
HF_TOKEN = os.environ.get('HF_TOKEN')
if not HF_TOKEN:
    print("Error: HF_TOKEN not set")
    exit(1)

grounding = GroundingModel(
    endpoint_url="https://k0mkv3j05m8vnmea.us-east-1.aws.endpoints.huggingface.cloud",
    hf_token=HF_TOKEN
)

print("=" * 60)
print("GROUNDING MODEL ACCURACY TEST")
print("=" * 60)

# Get screen size
screen_width, screen_height = pyautogui.size()
print(f"Screen size: {screen_width}x{screen_height}")

# Define test points (we'll draw markers at these locations)
test_points = [
    {"x": screen_width // 4, "y": screen_height // 4, "label": "TOP LEFT MARKER"},
    {"x": screen_width // 2, "y": screen_height // 4, "label": "TOP CENTER MARKER"},
    {"x": 3 * screen_width // 4, "y": screen_height // 4, "label": "TOP RIGHT MARKER"},
    {"x": screen_width // 2, "y": screen_height // 2, "label": "CENTER MARKER"},
    {"x": screen_width // 4, "y": 3 * screen_height // 4, "label": "BOTTOM LEFT MARKER"},
    {"x": 3 * screen_width // 4, "y": 3 * screen_height // 4, "label": "BOTTOM RIGHT MARKER"},
]

print("\n📍 I will create a test image with markers at known positions")
print("Then ask the grounding model to find them")
print("\nStarting in 3 seconds...")

time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")

# Create a test image with markers
print("\n🎨 Creating test image with markers...")
img = Image.new('RGB', (screen_width, screen_height), color='white')
draw = ImageDraw.Draw(img)

# Try to use a font, fallback to default if not available
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
except:
    font = ImageFont.load_default()

# Draw markers at each test point
for point in test_points:
    x, y = point['x'], point['y']
    label = point['label']
    
    # Draw a big red circle
    radius = 30
    draw.ellipse(
        [(x - radius, y - radius), (x + radius, y + radius)],
        fill='red',
        outline='black',
        width=3
    )
    
    # Draw crosshair
    draw.line([(x - radius - 10, y), (x + radius + 10, y)], fill='black', width=2)
    draw.line([(x, y - radius - 10), (x, y + radius + 10)], fill='black', width=2)
    
    # Draw label
    draw.text((x - 100, y - radius - 60), label, fill='black', font=font)

# Save and display the test image
test_image_path = 'grounding_test_markers.png'
img.save(test_image_path)
print(f"✅ Saved test image to: {test_image_path}")

# Display the image (open it)
print("\n📺 Opening test image... Make sure it's FULLSCREEN and visible!")
if os.system(f'open {test_image_path}') != 0:  # macOS
    os.system(f'xdg-open {test_image_path}')  # Linux

print("\nWaiting 5 seconds for image to display...")
for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# Now test the grounding model
print("\n" + "=" * 60)
print("TESTING GROUNDING MODEL")
print("=" * 60)

errors = []

for i, point in enumerate(test_points, 1):
    true_x, true_y = point['x'], point['y']
    label = point['label']
    
    print(f"\n[{i}/{len(test_points)}] Testing: {label}")
    print(f"   True position: ({true_x}, {true_y})")
    
    try:
        # Ask grounding model to find it
        description = f"the red circular marker labeled '{label}'"
        found_x, found_y = grounding.find_coordinates(description)
        
        print(f"   Found position: ({found_x}, {found_y})")
        
        # Calculate error
        error_x = found_x - true_x
        error_y = found_y - true_y
        distance_error = ((error_x ** 2) + (error_y ** 2)) ** 0.5
        
        print(f"   Error: X={error_x:+d}, Y={error_y:+d}, Distance={distance_error:.1f} pixels")
        
        errors.append({
            'label': label,
            'true': (true_x, true_y),
            'found': (found_x, found_y),
            'error_x': error_x,
            'error_y': error_y,
            'distance': distance_error
        })
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        errors.append({
            'label': label,
            'true': (true_x, true_y),
            'found': None,
            'error_x': None,
            'error_y': None,
            'distance': None
        })

# Calculate statistics
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

valid_errors = [e for e in errors if e['found'] is not None]

if valid_errors:
    avg_error_x = sum(e['error_x'] for e in valid_errors) / len(valid_errors)
    avg_error_y = sum(e['error_y'] for e in valid_errors) / len(valid_errors)
    avg_distance = sum(e['distance'] for e in valid_errors) / len(valid_errors)
    
    print(f"\n📊 Average Error:")
    print(f"   X offset: {avg_error_x:+.1f} pixels")
    print(f"   Y offset: {avg_error_y:+.1f} pixels")
    print(f"   Distance: {avg_distance:.1f} pixels")
    
    print(f"\n📋 Individual Results:")
    for e in errors:
        if e['found']:
            print(f"   {e['label']}: X={e['error_x']:+d}, Y={e['error_y']:+d}, Distance={e['distance']:.1f}px")
        else:
            print(f"   {e['label']}: FAILED")
    
    # Determine if there's a systematic offset
    if abs(avg_error_x) > 10 or abs(avg_error_y) > 10:
        print(f"\n⚠️  SYSTEMATIC OFFSET DETECTED!")
        print(f"   The grounding model is consistently off by:")
        print(f"   X: {avg_error_x:+.1f} pixels")
        print(f"   Y: {avg_error_y:+.1f} pixels")
        print(f"\n💡 You can fix this by adding a correction:")
        print(f"   corrected_x = found_x - {int(avg_error_x)}")
        print(f"   corrected_y = found_y - {int(avg_error_y)}")
    else:
        print(f"\n✅ No systematic offset detected!")
        print(f"   Average error is within acceptable range.")

else:
    print("\n❌ All tests failed! Grounding model is not working.")

print("\n" + "=" * 60)