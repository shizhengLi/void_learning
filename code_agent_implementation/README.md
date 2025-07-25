# Code Editor Agent

A LangChain-based implementation of an AI agent that can interact with codebases, similar to Void's agent functionality.

## Features

- **File Operations**: Search, read, and edit files
- **Terminal Integration**: Execute commands and manage persistent terminals
- **Approval System**: Safety mechanism for dangerous operations
- **Multiple Modes**: Standard, detailed, and safe modes
- **Codebase Analysis**: Detect project type and analyze code structure

## Usage

### Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables in `.env` file:

```
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o
TEMPERATURE=0
```

### Running the Agent

Basic usage:

```bash
python3 main.py
```

With command-line options:

```bash
# Run in safe mode (read-only)
python3 main.py --safe

# Skip approval for dangerous operations
python3 main.py --no-approval

# Use detailed prompt
python3 main.py --detailed

# Specify model
python3 main.py --model gpt-3.5-turbo

# Set working directory
python3 main.py --dir /path/to/your/project
```

## Examples

Here are some examples of what you can ask the agent:

1. **Project Analysis**:
   - "What kind of project is this?"
   - "List all Python files in this codebase"
   - "How many lines of code are in this project?"

2. **Code Search**:
   - "Find all functions that handle file operations"
   - "Search for files containing 'TODO' comments"
   - "Where is the main entry point of this application?"

3. **Code Editing**:
   - "Add error handling to the file_read function"
   - "Rename the 'process_data' function to 'process_input' in all files"
   - "Create a new utility function for parsing JSON"

4. **Terminal Operations**:
   - "Run unit tests for the project"
   - "Check the current Python version"
   - "Install the requests package"

## Architecture

The agent is built with the following components:

1. **File Tools**: Tools for file system operations
2. **Terminal Tools**: Tools for command execution
3. **Agent Core**: LangChain agent for reasoning
4. **Approval System**: Safety mechanism for dangerous operations
5. **Helper Utilities**: Code analysis and search helpers

## Safety Features

- **Safe Mode**: Restricts the agent to read-only operations
- **Approval System**: Requires user approval for dangerous operations
- **Error Handling**: Graceful error handling for commands and file operations

## Customization

You can customize the agent by:

- Modifying the system prompts in `agent/prompts.py`
- Adding new tools in `tools/` directory
- Adjusting safety settings in the `.env` file

## Credits

This implementation is based on the Void Editor's agent architecture, as described in the Void Learning repository.

## License

MIT License 