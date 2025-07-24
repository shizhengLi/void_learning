# Building a Code Editor Agent with LangChain

This guide provides a step-by-step approach to implementing a code editor agent similar to Void's agent functionality using LangChain. While it won't achieve the same level of integration with an editor like VSCode, it demonstrates how to create a standalone system that can interact with codebases.

## Prerequisites

- Python 3.9+
- Basic understanding of LangChain
- Access to an LLM API (OpenAI, Anthropic, etc.)

## Step 1: Setting Up the Environment

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install langchain langchain-openai pydantic python-dotenv
```

Create a `.env` file for your API keys:

```
OPENAI_API_KEY=sk-your-key-here
```

## Step 2: Basic Project Structure

```
code-agent/
├── .env                # Environment variables
├── main.py             # Entry point
├── agent/
│   ├── __init__.py
│   ├── agent.py        # Agent implementation
│   └── prompts.py      # System prompts
├── tools/
│   ├── __init__.py
│   ├── file_tools.py   # File system tools
│   └── terminal_tools.py  # Command execution tools
└── utils/
    ├── __init__.py
    └── helpers.py      # Helper functions
```

## Step 3: Implementing File Tools

Create `tools/file_tools.py`:

```python
from langchain.tools import BaseTool
from typing import Optional, List
import os
import glob
import re

class FileSearchTool(BaseTool):
    name = "search_for_files"
    description = "Search for files containing specific content"
    
    def _run(self, query: str, search_dir: Optional[str] = None, is_regex: bool = False):
        """Search for files containing the specified content."""
        if search_dir is None:
            search_dir = os.getcwd()
        
        results = []
        for root, _, files in os.walk(search_dir):
            for file in files:
                # Skip binary files and very large files
                filepath = os.path.join(root, file)
                if os.path.getsize(filepath) > 10000000:  # Skip files > 10MB
                    continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if is_regex:
                        if re.search(query, content):
                            results.append(filepath)
                    else:
                        if query in content:
                            results.append(filepath)
                except:
                    # Skip files that can't be read as text
                    pass
                    
                if len(results) >= 50:  # Limit results
                    break
        
        return results

class PathSearchTool(BaseTool):
    name = "search_pathnames_only"
    description = "Search for files with names matching a pattern"
    
    def _run(self, query: str, include_pattern: Optional[str] = None):
        """Search for files with names matching the pattern."""
        if include_pattern:
            files = glob.glob(f"**/{include_pattern}", recursive=True)
        else:
            files = []
            for root, _, filenames in os.walk('.'):
                for filename in filenames:
                    if query.lower() in filename.lower():
                        files.append(os.path.join(root, filename))
        
        return files[:50]  # Limit to 50 results

class FileReadTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file"
    
    def _run(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None):
        """Read the contents of a file, optionally from start_line to end_line."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if start_line is None and end_line is None:
                    return f.read()
                else:
                    lines = f.readlines()
                    start = start_line if start_line is not None else 0
                    end = end_line if end_line is not None else len(lines)
                    return ''.join(lines[start:end])
        except Exception as e:
            return f"Error reading file: {str(e)}"

class FileEditTool(BaseTool):
    name = "edit_file"
    description = "Edit a file using search/replace blocks"
    
    def _run(self, file_path: str, search_replace_blocks: str):
        """
        Edit a file using search/replace blocks.
        
        Search/Replace blocks should be formatted as:
        <<<<<<< ORIGINAL
        // original code
        =======
        // replaced code
        >>>>>>> UPDATED
        """
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the search/replace blocks
            blocks = self._parse_search_replace_blocks(search_replace_blocks)
            
            # Apply each block
            new_content = content
            for block in blocks:
                if block['original'] in new_content:
                    new_content = new_content.replace(block['original'], block['updated'])
                else:
                    return f"Error: Original block not found in file: {block['original'][:50]}..."
            
            # Write the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"File {file_path} edited successfully."
        except Exception as e:
            return f"Error editing file: {str(e)}"
    
    def _parse_search_replace_blocks(self, blocks_str):
        """Parse search/replace blocks from the input string."""
        pattern = r'<<<<<<< ORIGINAL\n(.*?)=======\n(.*?)>>>>>>> UPDATED'
        matches = re.findall(pattern, blocks_str, re.DOTALL)
        
        blocks = []
        for match in matches:
            blocks.append({
                'original': match[0],
                'updated': match[1]
            })
        
        return blocks
```

## Step 4: Implementing Terminal Tools

Create `tools/terminal_tools.py`:

```python
from langchain.tools import BaseTool
import subprocess
import threading
import time
import uuid
from typing import Dict, Optional

# Store for persistent terminals
class TerminalStore:
    _terminals: Dict[str, subprocess.Popen] = {}
    
    @classmethod
    def create_terminal(cls, cwd: Optional[str] = None) -> str:
        """Create a new persistent terminal and return its ID."""
        terminal_id = str(uuid.uuid4())
        
        # On Windows, use cmd.exe instead
        if cwd is None:
            cwd = "."
            
        # Start a bash process that stays alive
        process = subprocess.Popen(
            ["bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            bufsize=1,
            universal_newlines=True
        )
        
        cls._terminals[terminal_id] = process
        return terminal_id
    
    @classmethod
    def get_terminal(cls, terminal_id: str) -> Optional[subprocess.Popen]:
        """Get a terminal by ID."""
        return cls._terminals.get(terminal_id)
    
    @classmethod
    def kill_terminal(cls, terminal_id: str) -> bool:
        """Kill a terminal by ID."""
        terminal = cls.get_terminal(terminal_id)
        if terminal:
            terminal.terminate()
            terminal.wait()
            del cls._terminals[terminal_id]
            return True
        return False
    
    @classmethod
    def list_terminals(cls) -> list[str]:
        """List all terminal IDs."""
        return list(cls._terminals.keys())


class ExecuteCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a terminal command and return the output"
    
    def _run(self, command: str, cwd: Optional[str] = None):
        """Execute a command and return the output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                text=True,
                capture_output=True,
                cwd=cwd
            )
            
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
                
            return {
                "output": output,
                "exit_code": result.returncode
            }
        except Exception as e:
            return f"Error executing command: {str(e)}"


class PersistentTerminalCreateTool(BaseTool):
    name = "open_persistent_terminal"
    description = "Open a persistent terminal that can be used for multiple commands"
    
    def _run(self, cwd: Optional[str] = None):
        """Create a persistent terminal and return its ID."""
        terminal_id = TerminalStore.create_terminal(cwd)
        return {
            "persistent_terminal_id": terminal_id,
            "message": f"Persistent terminal created with ID: {terminal_id}"
        }


class PersistentTerminalCommandTool(BaseTool):
    name = "run_persistent_command"
    description = "Run a command in a persistent terminal"
    
    def _run(self, command: str, persistent_terminal_id: str, timeout: int = 30):
        """Run a command in a persistent terminal."""
        terminal = TerminalStore.get_terminal(persistent_terminal_id)
        if not terminal:
            return f"Error: Terminal with ID {persistent_terminal_id} not found"
        
        try:
            # Send the command to the terminal
            terminal.stdin.write(f"{command}\n")
            terminal.stdin.write("echo COMMAND_FINISHED_$?\n")
            terminal.stdin.flush()
            
            # Read output with timeout
            output_lines = []
            exit_code = None
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                line = terminal.stdout.readline().strip()
                if line.startswith("COMMAND_FINISHED_"):
                    exit_code = int(line.split("_")[-1])
                    break
                output_lines.append(line)
                
            output = "\n".join(output_lines)
            
            if exit_code is None:
                return {
                    "output": output + "\n[Command timed out after {timeout} seconds]",
                    "timed_out": True
                }
                
            return {
                "output": output,
                "exit_code": exit_code
            }
        except Exception as e:
            return f"Error running command: {str(e)}"


class PersistentTerminalKillTool(BaseTool):
    name = "kill_persistent_terminal"
    description = "Kill a persistent terminal"
    
    def _run(self, persistent_terminal_id: str):
        """Kill a persistent terminal."""
        if TerminalStore.kill_terminal(persistent_terminal_id):
            return f"Terminal {persistent_terminal_id} killed successfully"
        else:
            return f"Error: Terminal with ID {persistent_terminal_id} not found"
```

## Step 5: Creating System Prompts

Create `agent/prompts.py`:

```python
from langchain.prompts import PromptTemplate

# System message for the agent
SYSTEM_MESSAGE = """You are a coding assistant with the ability to search, read, and edit files,
as well as execute commands in the terminal. Your goal is to help the user with their coding tasks.

You have access to these tools:
1. search_for_files - Search for files containing specific content
2. search_pathnames_only - Search for files with names matching a pattern
3. read_file - Read the contents of a file
4. edit_file - Edit a file using search/replace blocks
5. run_command - Execute a terminal command
6. open_persistent_terminal - Create a persistent terminal
7. run_persistent_command - Run a command in a persistent terminal
8. kill_persistent_terminal - Kill a persistent terminal

When editing files, use search/replace blocks in this format:
<<<<<<< ORIGINAL
// original code
=======
// replaced code
>>>>>>> UPDATED

Always verify your changes by reading files before and after modifications. 
Try to understand the project structure before making changes.
When executing terminal commands, be cautious and explain what each command does.

IMPORTANT: When completing a task, provide a brief summary of what you did and any next steps.
"""

SYSTEM_PROMPT = PromptTemplate.from_template(SYSTEM_MESSAGE)
```

## Step 6: Creating the Agent

Create `agent/agent.py`:

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

from typing import List

from .prompts import SYSTEM_PROMPT

class CodeAgent:
    def __init__(self, tools: List[BaseTool], model_name: str = "gpt-4o", api_key: str = None):
        """Initialize the code agent with tools and model."""
        self.tools = tools
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=api_key
        )
        
        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )
    
    async def run(self, query: str):
        """Run the agent on a query."""
        return await self.agent_executor.ainvoke({"input": query})
```

## Step 7: Creating the Main Application

Create `main.py`:

```python
import os
import asyncio
from dotenv import load_dotenv

# Load tools
from tools.file_tools import FileSearchTool, PathSearchTool, FileReadTool, FileEditTool
from tools.terminal_tools import (
    ExecuteCommandTool, 
    PersistentTerminalCreateTool,
    PersistentTerminalCommandTool,
    PersistentTerminalKillTool
)

# Load agent
from agent.agent import CodeAgent

# Load environment variables
load_dotenv()

async def main():
    # Initialize tools
    tools = [
        FileSearchTool(),
        PathSearchTool(),
        FileReadTool(),
        FileEditTool(),
        ExecuteCommandTool(),
        PersistentTerminalCreateTool(),
        PersistentTerminalCommandTool(),
        PersistentTerminalKillTool()
    ]
    
    # Initialize agent
    api_key = os.getenv("OPENAI_API_KEY")
    agent = CodeAgent(tools=tools, api_key=api_key)
    
    print("Code Agent initialized. Type 'exit' to quit.")
    
    while True:
        query = input("\nEnter your query: ")
        
        if query.lower() == 'exit':
            break
            
        try:
            response = await agent.run(query)
            print("\nAgent response:")
            print(response["output"])
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 8: Adding UI Integration (Optional)

For a more user-friendly interface, you could add a simple web UI using Gradio:

```bash
pip install gradio
```

Update `main.py`:

```python
import os
import asyncio
from dotenv import load_dotenv
import gradio as gr

# Load tools
from tools.file_tools import FileSearchTool, PathSearchTool, FileReadTool, FileEditTool
from tools.terminal_tools import (
    ExecuteCommandTool, 
    PersistentTerminalCreateTool,
    PersistentTerminalCommandTool,
    PersistentTerminalKillTool
)

# Load agent
from agent.agent import CodeAgent

# Load environment variables
load_dotenv()

# Initialize tools
tools = [
    FileSearchTool(),
    PathSearchTool(),
    FileReadTool(),
    FileEditTool(),
    ExecuteCommandTool(),
    PersistentTerminalCreateTool(),
    PersistentTerminalCommandTool(),
    PersistentTerminalKillTool()
]

# Initialize agent
api_key = os.getenv("OPENAI_API_KEY")
agent = CodeAgent(tools=tools, api_key=api_key)

# Set working directory
working_dir = os.getcwd()

async def process_query(query, history):
    try:
        response = await agent.run(query)
        return response["output"]
    except Exception as e:
        return f"Error: {str(e)}"

def respond(query, history):
    response = asyncio.run(process_query(query, history))
    return response

def set_directory(new_dir):
    global working_dir
    try:
        os.chdir(new_dir)
        working_dir = os.getcwd()
        return f"Working directory set to: {working_dir}"
    except Exception as e:
        return f"Error setting directory: {str(e)}"

# Create the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Code Agent")
    
    with gr.Row():
        with gr.Column():
            dir_input = gr.Textbox(label="Working Directory", value=working_dir)
            dir_button = gr.Button("Set Working Directory")
        
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Query")
    clear = gr.Button("Clear")
    
    msg.submit(respond, [msg, chatbot], [chatbot])
    dir_button.click(set_directory, [dir_input], [chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()
```

## Step 9: Adding Safety Features

For safety, add an approval system in `main.py`:

```python
# Add to main.py
def needs_approval(tool_name, args):
    """Determine if a tool call needs approval."""
    high_risk_tools = ["edit_file", "run_command", "run_persistent_command"]
    
    if tool_name in high_risk_tools:
        return True
        
    return False

def get_approval(tool_name, args):
    """Get user approval for a tool call."""
    print(f"\n⚠️ The agent wants to use {tool_name} with args: {args}")
    response = input("Allow this action? (y/n): ")
    return response.lower() == 'y'

# Modify the agent.py file to add approval logic
```

## Step 10: Enhancing Context Management

Add better context management:

```python
# Add to agent/agent.py
from langchain.memory import ConversationBufferMemory

class CodeAgent:
    def __init__(self, tools: List[BaseTool], model_name: str = "gpt-4o", api_key: str = None):
        # ... existing code ...
        
        # Add memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create the agent executor with memory
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
            memory=self.memory
        )
        
    # ... rest of the code ...
```

## Conclusion

This implementation provides a foundation for a code agent similar to Void's functionality. While it doesn't have the tight integration with an editor like VSCode, it demonstrates the core concepts:

1. **File System Interaction**: Tools for searching, reading, and editing files
2. **Command Execution**: Tools for running commands and managing terminals
3. **Agent Framework**: Using LangChain's React agent pattern for reasoning
4. **Safety Features**: Basic approval mechanisms for risky operations

To enhance this implementation further, consider:

1. Adding integrations with specific editors via plugins
2. Implementing more sophisticated search and indexing
3. Adding version control awareness
4. Improving the UI for better user experience
5. Adding more robust error handling and recovery

Remember that this is a starting point - a production-quality implementation would require more extensive development and testing. 