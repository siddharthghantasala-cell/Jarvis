"""
step_agent.py - One action at a time, based on current state

Each prompt to Claude includes:
- The goal
- Last action taken
- Current screenshot

Claude returns ONE next action (or "done")
"""

import json
import base64
import io
from typing import Dict, Any, Optional
from anthropic import Anthropic
import pyautogui
from actions import ComputerActions, get_action_descriptions
from grounding import GroundingModel, SmartActions
import os

class StepAgent:
    """
    Agent that decides one action at a time based on current screen state.
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        grounding_model: Optional[GroundingModel] = None
    ):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.grounding = grounding_model
        self.actions = SmartActions(grounding_model) if grounding_model else ComputerActions()
        self.action_descriptions = get_action_descriptions()
        
        # Add grounding actions if available
        if grounding_model:
            self.action_descriptions.update({
                "click_element": {
                    "description": "Click on a UI element by description (uses AI vision)",
                    "params": {"description": "string"},
                    "example": "click_element('the search button')"
                },
                "type_in_element": {
                    "description": "Click an element and type text (uses AI vision)",
                    "params": {"description": "string", "text": "string"},
                    "example": "type_in_element('the search box', 'hello')"
                }
            })
        
        self.history = []  # List of executed actions
    
    def _screenshot_to_base64(self) -> str:
        """Take screenshot and encode as base64, compressed to stay under 5MB."""
        from PIL import Image
        
        screenshot = pyautogui.screenshot()
        
        # Convert RGBA to RGB (JPEG doesn't support transparency)
        if screenshot.mode == 'RGBA':
            rgb_screenshot = Image.new('RGB', screenshot.size, (255, 255, 255))
            rgb_screenshot.paste(screenshot, mask=screenshot.split()[3])
            screenshot = rgb_screenshot
        
        # Resize if too large (keep aspect ratio)
        max_dimension = 1920
        if screenshot.width > max_dimension or screenshot.height > max_dimension:
            screenshot.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Save as JPEG with compression
        quality = 85
        buffered = io.BytesIO()
        screenshot.save(buffered, format="JPEG", quality=quality, optimize=True)
        
        # Check size and reduce quality if needed
        while buffered.tell() > 4.5 * 1024 * 1024:  # 4.5MB to be safe
            quality = max(60, quality - 10)
            buffered = io.BytesIO()
            screenshot.save(buffered, format="JPEG", quality=quality, optimize=True)
        
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with available actions."""
        actions_json = json.dumps(self.action_descriptions, indent=2)
        
        return f"""You are a computer automation agent that decides ONE action at a time.

AVAILABLE ACTIONS:
{actions_json}

YOUR JOB:
1. Look at the current screenshot
2. Consider the goal and what's been done so far
3. Decide the NEXT SINGLE ACTION to take
4. Output ONLY that action in JSON format

OUTPUT FORMAT:
If you need to take another action:
{{
  "action": "action_name",
  "params": {{"param1": "value1"}},
  "reasoning": "why this action"
}}

If the goal is complete:
{{
  "action": "done",
  "params": {{}},
  "reasoning": "goal accomplished"
}}

RULES:
- Output ONLY valid JSON, nothing else
- ONE action per response
- Use click_element() and type_in_element() when you need to find UI elements
- Use wait() after actions that change the UI (1-3 seconds)
- Be specific in element descriptions
- Output "done" when goal is accomplished

CRITICAL: Your entire response must be a single JSON object. No text before or after."""

    def next_action(self, goal: str) -> Dict[str, Any]:
        """
        Decide the next action to take.
        
        Args:
            goal: The overall goal to accomplish
            
        Returns:
            Action dictionary with 'action', 'params', 'reasoning'
        """
        # Build context about what's been done
        if self.history:
            # Build a summary of completed actions
            history_summary = "ACTIONS COMPLETED SO FAR:\n"
            for i, h in enumerate(self.history, 1):
                status_str = "✓" if h['status'] == 'success' else "✗"
                history_summary += f"{i}. [{status_str}] {h['action']}({h.get('params', {})}) - {h.get('reasoning', '')}\n"
            
            history_summary += "\nDO NOT repeat these actions. Continue from where you left off.\n"
            
            last_action = self.history[-1]
            context = f"\nLast action: {last_action['action']}({last_action['params']}) - {last_action['status']}\n"
            context = history_summary + context
        else:
            context = "No actions taken yet. This is the first action."
        
        # Take screenshot
        screenshot_b64 = self._screenshot_to_base64()
        
        # Build prompt
        user_message = f"""Goal: {goal}

{context}

Based on the current screenshot and what's been done so far, what is the NEXT action to take?

IMPORTANT: 
- Look at the completed actions above
- Do NOT repeat actions that already succeeded
- Continue from where you left off
- If the goal is complete, return {{"action": "done"}}"""
        
        # Call Claude
        print("🤔 Asking Claude for next action...")
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=self._build_system_prompt(),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": screenshot_b64
                            }
                        }
                    ]
                }
            ]
        )
        
        # Parse response
        response_text = response.content[0].text.strip()
        
        # Try to extract JSON from response
        # Look for { ... } pattern
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            response_text = json_match.group(0)
        else:
            # Try cleaning up markdown
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
        
        try:
            action_dict = json.loads(response_text)
            return action_dict
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse: {e}")
            print(f"Response: {response_text}")
            raise
    
    def _find_click_position(self, target_description: str, max_attempts: int = 5) -> tuple:
        """
        Iteratively find the right position to click using visual feedback.
        
        Args:
            target_description: What to click (e.g., "the like button")
            max_attempts: Maximum refinement attempts
            
        Returns:
            (x, y) coordinates
        """
        print(f"🎯 Finding position for: {target_description}")
        
        current_x, current_y = None, None
        
        for attempt in range(1, max_attempts + 1):
            print(f"   Attempt {attempt}/{max_attempts}...")
            
            # Take screenshot
            screenshot_b64 = self._screenshot_to_base64()
            
            # Ask Claude for coordinates
            if attempt == 1:
                prompt = f"""Look at the screenshot and find: {target_description}

Provide the X and Y coordinates for the CENTER of this element.

IMPORTANT: Aim for the dead center of the element, not the edge.

Respond ONLY with JSON:
{{
  "x": <number>,
  "y": <number>,
  "reasoning": "why these coordinates point to the center"
}}"""
            else:
                prompt = f"""The cursor is currently visible in the screenshot at position ({current_x}, {current_y}).

Target: {target_description}

CRITICAL INSTRUCTIONS:
1. Check if the cursor is CENTERED on the target element
2. If not centered, provide NEW coordinates that are at least 10-20 pixels different
3. Aim for the DEAD CENTER of the element, not edges or corners
4. Make BOLD adjustments if you're off

Respond ONLY with JSON:
{{
  "on_target": true/false,
  "x": <number or null>,
  "y": <number or null>,
  "reasoning": "detailed explanation of cursor position relative to target"
}}

If the cursor is NOT on target, you MUST provide new x,y coordinates that differ by at least 10 pixels."""
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": screenshot_b64
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            try:
                result = json.loads(response_text)
            except:
                print(f"   ❌ Could not parse response")
                continue
            
            # First attempt - just get coordinates
            if attempt == 1:
                x, y = result['x'], result['y']
                current_x, current_y = x, y
                print(f"   Initial guess: ({x}, {y}) - {result.get('reasoning', '')}")
                
                # Move cursor there
                pyautogui.moveTo(x, y, duration=0.3)
                import time
                time.sleep(0.5)
                
            # Subsequent attempts - check if on target
            else:
                if result.get('on_target'):
                    print(f"   ✅ Cursor is centered on target!")
                    return current_x, current_y
                
                if result.get('x') is not None and result.get('y') is not None:
                    new_x, new_y = result['x'], result['y']
                    
                    # Enforce minimum movement of 10 pixels
                    if current_x is not None and current_y is not None:
                        distance = ((new_x - current_x)**2 + (new_y - current_y)**2)**0.5
                        
                        if distance < 10:
                            print(f"   ⚠️  Movement too small ({distance:.1f}px), encouraging larger adjustment...")
                            # Ask again with stronger language
                            continue
                    
                    current_x, current_y = new_x, new_y
                    print(f"   Adjusting to: ({new_x}, {new_y}) - {result.get('reasoning', '')}")
                    
                    pyautogui.moveTo(new_x, new_y, duration=0.3)
                    import time
                    time.sleep(0.5)
                else:
                    print(f"   ⚠️  No new coordinates provided")
        
        # Return final position
        final_x, final_y = current_x or pyautogui.position()[0], current_y or pyautogui.position()[1]
        print(f"   Using final position: ({final_x}, {final_y})")
        return final_x, final_y
    
    def execute_action(self, action_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single action.
        
        Args:
            action_dict: Action from next_action()
            
        Returns:
            Execution result
        """
        action_name = action_dict['action']
        params = action_dict.get('params', {})
        reasoning = action_dict.get('reasoning', '')
        
        print(f"\n⚡ Action: {action_name}")
        print(f"   Params: {params}")
        print(f"   Why: {reasoning}")
        
        if action_name == "done":
            return {
                "action": "done",
                "status": "complete",
                "params": params,
                "reasoning": reasoning
            }
        
        # Check if this is a coordinate-based action - if so, HANDOFF
        coordinate_actions = ["click", "move_mouse", "drag", "scroll"]
        if action_name in coordinate_actions:
            print(f"\n🔄 HANDOFF REQUIRED!")
            print(f"   This action requires coordinates: {action_name}")
            print(f"   Terminating and passing to grounding system...")
            
            return {
                "action": action_name,
                "params": params,
                "reasoning": reasoning,
                "status": "handoff",
                "handoff_reason": "coordinate_based_action"
            }
        
        try:
            # Get the action method
            if not hasattr(self.actions, action_name):
                raise ValueError(f"Unknown action: {action_name}")
            
            action_method = getattr(self.actions, action_name)
            
            # Execute
            result = action_method(**params)
            
            print(f"   ✅ Success")
            
            return {
                "action": action_name,
                "params": params,
                "reasoning": reasoning,
                "result": result,
                "status": "success"
            }
            
        except Exception as e:
            print(f"   ❌ Exception occurred: {e}")
            print(f"   🔄 Routing to handoff...")
            
            # Instead of failing, handoff to the other system
            return {
                "action": action_name,
                "params": params,
                "reasoning": reasoning,
                "error": str(e),
                "status": "handoff",
                "handoff_reason": "exception_during_execution"
            }
    
    def run(self, goal: str, max_steps: int = 20) -> Dict[str, Any]:
        """
        Run the agent step-by-step until done or handoff needed.
        
        Args:
            goal: Goal to accomplish
            max_steps: Maximum number of steps before stopping
            
        Returns:
            Dictionary with status and history
        """
        print("=" * 60)
        print(f"🎯 GOAL: {goal}")
        print("=" * 60)
        
        self.history = []
        handoff_info = None
        
        for step in range(1, max_steps + 1):
            print(f"\n{'='*60}")
            print(f"STEP {step}/{max_steps}")
            print(f"{'='*60}")
            
            # Try to get next action with retries
            max_retries = 3
            action_dict = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    action_dict = self.next_action(goal)
                    break
                except Exception as e:
                    print(f"❌ Attempt {attempt}/{max_retries} failed: {e}")
                    if attempt < max_retries:
                        print("   Retrying...")
                        import time
                        time.sleep(1)
                    else:
                        print("   Max retries reached, skipping this step")
                        # Add a wait action as fallback
                        action_dict = {
                            "action": "wait",
                            "params": {"seconds": 1.0},
                            "reasoning": "Failed to get action from Claude, waiting"
                        }
            
            if action_dict is None:
                print("⚠️  Could not get action, stopping")
                break
            
            # Execute it
            result = self.execute_action(action_dict)
            self.history.append(result)
            
            # Check if we need to handoff
            if result['status'] == 'handoff':
                handoff_info = {
                    "action": result['action'],
                    "params": result['params'],
                    "reasoning": result['reasoning'],
                    "goal": goal,
                    "history": self.history
                }
                print("\n" + "=" * 60)
                print("🔄 HANDOFF TO GROUNDING SYSTEM")
                print("=" * 60)
                print(f"Action needed: {result['action']}")
                print(f"Description: {result['reasoning']}")
                break
            
            # Check if done
            if result['action'] == 'done':
                print("\n" + "=" * 60)
                print("✅ GOAL COMPLETE!")
                print("=" * 60)
                break
            
            # Check if we should continue
            if result['status'] == 'failed':
                print(f"   ⚠️  Action failed, but continuing...")
        
        if step >= max_steps:
            print("\n" + "=" * 60)
            print("⚠️  Reached max steps")
            print("=" * 60)
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Total steps: {len(self.history)}")
        successes = sum(1 for h in self.history if h['status'] == 'success')
        print(f"   Successful: {successes}/{len(self.history)}")
        
        if handoff_info:
            print(f"   Status: HANDOFF")
        
        return {
            "status": "handoff" if handoff_info else ("complete" if any(h['action'] == 'done' for h in self.history) else "incomplete"),
            "goal": goal,
            "history": self.history,
            "handoff": handoff_info
        }


def run_agent(instruction: str, anthropic_api_key: str = None) -> Dict[str, Any]:
    """
    Run the agent with a single instruction.
    
    Args:
        instruction: What the user wants to do
        anthropic_api_key: Anthropic API key (optional, will use env var if not provided)
        
    Returns:
        Result dictionary with status, history, and handoff info
        
    Example:
        result = run_agent("open google docs and create a new document")
        if result['status'] == 'handoff':
            print(f"Need to: {result['handoff']['action']}")
    """
    # Get API key
    if anthropic_api_key is None:
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
    
    # Create agent WITHOUT grounding model
    agent = StepAgent(
        anthropic_api_key=anthropic_api_key,
        grounding_model=None  # No grounding
    )
    
    # Run the instruction
    result = agent.run(instruction, max_steps=15)
    
    return result

# res = run_agent("open chrome")
# print(res, "is the result")

# # if __name__ == "__main__":
#     import os
    
#     # Get API keys
#     anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
#     hf_token = os.environ.get('HF_TOKEN')
    
#     if not anthropic_key:
#         print("Error: Set ANTHROPIC_API_KEY environment variable")
#         exit(1)
    
#     # Decide if we want grounding
#     use_grounding = input("Use grounding model? (y/n): ").strip().lower() == 'y'
    
#     grounding = None
#     if use_grounding:
#         if not hf_token:
#             print("Error: Set HF_TOKEN environment variable")
#             exit(1)
        
#         print("\n🔧 Setting up grounding model...")
#         grounding = GroundingModel(
#             endpoint_url="https://k0mkv3j05m8vnmea.us-east-1.aws.endpoints.huggingface.cloud",
#             hf_token=hf_token
#         )
    
#     # Create agent
#     agent = StepAgent(
#         anthropic_api_key=anthropic_key,
#         grounding_model=grounding
#     )
    
#     # Get goal
#     print("\n" + "=" * 60)
#     print("STEP-BY-STEP AUTOMATION AGENT")
#     print("=" * 60)
    
#     goal = input("\n🎯 What would you like to do? ").strip()
    
#     if goal:
#         result = agent.run(goal, max_steps=15)
        
#         print("\n" + "=" * 60)
#         print("📋 FINAL RESULT:")
#         print("=" * 60)
#         print(f"Status: {result['status']}")
        
#         if result.get('handoff'):
#             print("\n🔄 HANDOFF INFO:")
#             print(f"   Next action: {result['handoff']['action']}")
#             print(f"   Params: {result['handoff']['params']}")
#             print(f"   Description: {result['handoff']['reasoning']}")
#             print(f"\n   → Pass this to your grounding system")
        
#         print("\n📋 ACTION HISTORY:")
#         print("=" * 60)
#         for i, h in enumerate(result['history'], 1):
#             status_icon = "✅" if h['status'] == 'success' else ("🔄" if h['status'] == 'handoff' else "❌")
#             print(f"{i}. {status_icon} {h['action']}({h.get('params', {})})")