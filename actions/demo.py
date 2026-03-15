"""
test_complex_workflow.py - Test a longer, more complex workflow
"""
from actions import ComputerActions
import time

actions = ComputerActions()

print("=" * 60)
print("COMPLEX WORKFLOW TEST")
print("=" * 60)
print("\nThis will:")
print("1. Open Chrome and navigate to GitHub")
print("2. Search for 'Agent-S'")
print("3. Open a new tab and go to Reddit")
print("4. Search for something on Reddit")
print("5. Take a screenshot")
print("\nStarting in 5 seconds... Don't touch anything!")
print("=" * 60)


print("\n🚀 Starting workflow...\n")

# ===== PART 1: GitHub Search =====
print("📍 Step 1: Opening Chrome...")
actions.open_app('Chrome')
actions.wait(2.0)

print("📍 Step 2: Going to GitHub...")
actions.open_url('youtube.com')
actions.wait(2.0)

print("📍 Step 3: Clicking search (top left)...")
# GitHub search is usually around top-left
actions.click(1000, 200) #x coordinate takes you from left to right upon increasing, y coordinate takes you from up to down upon increasing
actions.wait(0.5)

print("📍 Step 4: Searching for Agent-S...")
actions.type_text('lazarbeam')
actions.wait(0.5)
actions.press_key('enter')
actions.wait(3.0)




# print("✅ GitHub search complete!\n")

# # ===== PART 2: Reddit =====
# print("📍 Step 5: Opening new tab...")
# actions.new_tab()
# actions.wait(1.0)

# print("📍 Step 6: Going to Reddit...")
# actions.open_url('reddit.com')
# actions.wait(3.0)

# print("📍 Step 7: Clicking Reddit search...")
# # Reddit search is usually top-right
# actions.click(1000, 100)
# actions.wait(0.5)

# print("📍 Step 8: Searching on Reddit...")
# actions.type_text('best laptop for programming')
# actions.wait(0.5)
# actions.press_key('enter')
# actions.wait(3.0)

# print("✅ Reddit search complete!\n")

# # ===== PART 3: Scroll and Screenshot =====
# print("📍 Step 9: Scrolling down...")
# actions.scroll(-5)  # Scroll down
# actions.wait(1.0)

# print("📍 Step 10: Taking screenshot...")
# actions.screenshot('workflow_result.png')

# print("\n" + "=" * 60)
# print("✅ WORKFLOW COMPLETE!")
# print("=" * 60)
# print("\nCheck 'workflow_result.png' to see the final result!")

# # ===== CLEANUP =====
# print("\n📍 Cleaning up in 2 seconds...")
# actions.wait(2.0)

# print("📍 Closing tabs...")
# actions.close_tab()  # Close Reddit tab
# actions.wait(0.5)
# actions.close_tab()  # Close GitHub tab
# actions.wait(0.5)

# print("\n✨ Done!")