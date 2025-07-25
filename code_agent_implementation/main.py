"""
Main entry point for the code editor agent.
"""

import os
import asyncio
import argparse
from dotenv import load_dotenv

# Load tools
from tools.file_tools import FileSearchTool, PathSearchTool, FileReadTool, FileEditTool, FileWriteTool
from tools.terminal_tools import (
    ExecuteCommandTool, 
    PersistentTerminalCreateTool,
    PersistentTerminalCommandTool,
    PersistentTerminalKillTool,
    ListTerminalsTool
)

# Load agent
from agent.agent import CodeAgent, create_agent_from_env


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Code Editor Agent")
    parser.add_argument("--safe", action="store_true", help="Run in safe mode (read-only)")
    parser.add_argument("--no-approval", action="store_true", help="Don't require approval for dangerous operations")
    parser.add_argument("--detailed", action="store_true", help="Use detailed prompt")
    parser.add_argument("--model", type=str, help="Model name to use")
    parser.add_argument("--dir", type=str, help="Working directory")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with mock responses")
    return parser.parse_args()


class MockAgent:
    """Mock agent for demonstration purposes."""
    
    def __init__(self, safe_mode=False, approval_needed=True):
        """Initialize the mock agent."""
        self.safe_mode = safe_mode
        self.approval_needed = approval_needed
        
    async def run(self, query):
        """Mock run method that returns predefined responses based on the query."""
        query_lower = query.lower()
        
        # Demo responses for common queries
        if "hello" in query_lower or "hi" in query_lower:
            return {
                "output": "Hello! I'm the Code Editor Agent. I can help you search, read, and edit files, as well as run commands."
            }
        elif "what can you do" in query_lower:
            return {
                "output": "I can:\n- Search for files and content\n- Read and edit files\n- Execute terminal commands\n- Help analyze and modify code"
            }
        elif "search" in query_lower and "todo" in query_lower:
            return {
                "output": "I found a TODO comment in geometry.py: 'TODO: Add functions for triangle calculations'"
            }
        elif "error handling" in query_lower:
            if self.safe_mode:
                return {
                    "output": "I'm in safe mode, so I can't edit files directly. Here's the code change you need:\n\n```python\ndef divide(a, b):\n    \"\"\"Divide a by b and return the result.\"\"\"\n    if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b\n```"
                }
            else:
                return {
                    "output": "I've added error handling to the divide function in calculator.py. The function now raises a ValueError when trying to divide by zero."
                }
        elif "add triangle" in query_lower:
            if self.safe_mode:
                return {
                    "output": "I'm in safe mode, so I can't edit files directly. Here's the code you should add to geometry.py:\n\n```python\ndef calculate_triangle_area(base, height):\n    \"\"\"Calculate the area of a triangle.\"\"\"\n    return 0.5 * base * height\n\ndef calculate_triangle_perimeter(a, b, c):\n    \"\"\"Calculate the perimeter of a triangle with sides a, b, and c.\"\"\"\n    return a + b + c\n```"
                }
            else:
                return {
                    "output": "I've added functions for triangle calculations to geometry.py. You can now calculate the area and perimeter of triangles."
                }
        elif "list files" in query_lower:
            return {
                "output": "Here are the files in the project:\n- demo_project/\n  - README.md\n  - src/\n    - calculator.py\n    - geometry.py"
            }
        else:
            return {
                "output": "I understand you're asking about: " + query + "\n\nIn a real implementation, I would process this query using the LLM. For this demo, I'm using predefined responses."
            }


async def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Set working directory if provided
    if args.dir:
        os.chdir(args.dir)
    else:
        # Default to demo project directory if not specified
        demo_dir = os.path.join(os.getcwd(), "demo_project")
        if os.path.exists(demo_dir):
            os.chdir(demo_dir)
    
    # Load environment variables
    load_dotenv()
    
    # Set environment variables based on arguments
    if args.safe:
        os.environ["SAFE_MODE"] = "True"
    if args.no_approval:
        os.environ["APPROVAL_NEEDED"] = "False"
    if args.detailed:
        os.environ["DETAILED_PROMPT"] = "True"
    if args.model:
        os.environ["MODEL_NAME"] = args.model
    
    # Print startup information
    print("\n🤖 Code Editor Agent initialized.")
    print(f"🌎 Working directory: {os.getcwd()}")
    
    if args.demo:
        # Use the mock agent for demonstration
        agent = MockAgent(safe_mode=args.safe, approval_needed=not args.no_approval)
        print(f"🔒 Safe mode: {'Enabled' if agent.safe_mode else 'Disabled'}")
        print(f"✅ Approval required: {'Yes' if agent.approval_needed else 'No'}")
        print(f"🎮 Running in DEMO mode (no API calls)")
    else:
        # Initialize tools
        tools = [
            FileSearchTool(),
            PathSearchTool(),
            FileReadTool(),
            FileEditTool(),
            FileWriteTool(),
            ExecuteCommandTool(),
            PersistentTerminalCreateTool(),
            PersistentTerminalCommandTool(),
            PersistentTerminalKillTool(),
            ListTerminalsTool()
        ]
        
        # Initialize agent
        agent = create_agent_from_env(tools)
        print(f"🔒 Safe mode: {'Enabled' if agent.safe_mode else 'Disabled'}")
        print(f"✅ Approval required: {'Yes' if agent.approval_needed else 'No'}")
        print(f"🧠 Model: {os.getenv('MODEL_NAME', 'gpt-4o')}")
    
    print("\nType 'exit' or 'quit' to end the session.\n")
    
    # Show example commands in demo mode
    if args.demo:
        print("Demo commands you can try:")
        print("- \"Hello\"")
        print("- \"What can you do?\"")
        print("- \"Search for TODO comments\"")
        print("- \"Add error handling to divide function\"")
        print("- \"Add triangle calculations to geometry\"")
        print("- \"List files in this project\"")
        print()
    
    # REPL loop
    while True:
        query = input("\n💻 > ")
        
        if query.lower() in ['exit', 'quit']:
            print("\nExiting Code Editor Agent. Goodbye! 👋\n")
            break
            
        try:
            print("\n🧠 Thinking...")
            response = await agent.run(query)
            print("\n🤖 Agent response:")
            print(response["output"])
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting Code Editor Agent. Goodbye! 👋\n") 