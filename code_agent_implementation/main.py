"""
Main entry point for the code editor agent.
This script initializes the agent and provides a simple REPL for interaction.
"""

import os
import argparse
import asyncio
from dotenv import load_dotenv

# Import tools
from tools.file_tools import (
    FileSearchTool, 
    PathSearchTool, 
    FileReadTool, 
    FileEditTool, 
    FileWriteTool,
    ListDirectoryTool
)
from tools.terminal_tools import (
    ExecuteCommandTool, 
    PersistentTerminalCreateTool,
    PersistentTerminalCommandTool,
    PersistentTerminalKillTool,
    ListTerminalsTool
)

# Import agent
from agent.agent import create_agent_from_env


class MockAgent:
    """Mock agent for demo purposes."""
    
    async def run(self, query):
        """Run the agent with a query.
        
        Args:
            query: The query to run
            
        Returns:
            The response
        """
        if "hello" in query.lower():
            return {"output": "Hello! I'm a mock agent. I can't actually do anything, but I can pretend to!"}
        elif "file" in query.lower():
            return {"output": "I found some files that might be relevant: example.py, main.py"}
        elif "search" in query.lower():
            return {"output": "I searched for that and found some results in the mock_directory."}
        else:
            return {"output": "I'm just a mock agent. In the real version, I would try to help with your request."}


async def repl(agent, working_dir):
    """Run the agent in a REPL.
    
    Args:
        agent: The agent to run
        working_dir: The working directory
    """
    print("\n🤖 Code Editor Agent initialized.")
    print(f"🌎 Working directory: {working_dir}")
    
    # Print mode information
    if hasattr(agent, "safe_mode") and agent.safe_mode:
        print("🔒 Safe mode: Enabled")
    else:
        print("🔒 Safe mode: Disabled")
        
    if hasattr(agent, "approval_needed") and agent.approval_needed:
        print("✅ Approval required: Yes")
    else:
        print("✅ Approval required: No")
    
    if hasattr(agent, "llm") and hasattr(agent.llm, "model_name"):
        print(f"🧠 Model: {agent.llm.model_name}")
    
    print("\nType 'exit' or 'quit' to end the session.\n")
    
    while True:
        try:
            user_input = input("\n💻 > ")
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nExiting Code Editor Agent. Goodbye! 👋")
                break
                
            print("\n🧠 Thinking...\n")
            
            response = await agent.run(user_input)
            
            print("\n🤖 Agent response:")
            print(response["output"])
            
        except KeyboardInterrupt:
            print("\n\nExiting Code Editor Agent. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def init_tools():
    """Initialize the tools.
    
    Returns:
        List of initialized tools
    """
    # File tools
    file_search = FileSearchTool()
    path_search = PathSearchTool()
    file_read = FileReadTool()
    file_edit = FileEditTool()
    file_write = FileWriteTool()
    list_directory = ListDirectoryTool()
    
    # Terminal tools
    execute_command = ExecuteCommandTool()
    open_terminal = PersistentTerminalCreateTool()
    run_in_terminal = PersistentTerminalCommandTool()
    kill_terminal = PersistentTerminalKillTool()
    list_terminals = ListTerminalsTool()
    
    # Return all tools
    return [
        file_search,
        path_search,
        file_read,
        file_edit,
        file_write,
        list_directory,
        execute_command,
        open_terminal,
        run_in_terminal,
        kill_terminal,
        list_terminals
    ]


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Code Editor Agent")
    parser.add_argument("--safe", action="store_true", help="Run in safe mode (read-only)")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (no API calls)")
    parser.add_argument("--working-dir", type=str, help="Working directory")
    args = parser.parse_args()
    
    # Set working directory
    if args.working_dir:
        working_dir = args.working_dir
        if not os.path.isabs(working_dir):
            working_dir = os.path.abspath(working_dir)
    else:
        # 使用当前目录作为默认工作目录，而不是demo_project
        working_dir = os.getcwd()
    
    # Change to the working directory
    os.chdir(working_dir)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize tools
    tools = init_tools()
    
    # Initialize agent
    if args.demo:
        agent = MockAgent()
    else:
        # Override environment variables based on arguments
        if args.safe:
            os.environ["SAFE_MODE"] = "True"
            
        agent = create_agent_from_env(tools)
        
    # Run the REPL
    asyncio.run(repl(agent, working_dir))


if __name__ == "__main__":
    main() 