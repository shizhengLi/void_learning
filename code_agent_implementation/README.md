# Code Editor Agent

An AI-powered code editor agent implemented using LangChain and OpenAI's GPT models. This agent can help you navigate, analyze, and modify codebases through natural language interactions.

## Features

- **File System Tools**: Search, read, edit, and create files
- **Terminal Tools**: Execute commands, manage persistent terminals
- **Context Management**: Maintains conversation history for context
- **Safety Features**: Option to run in read-only mode and require approval for dangerous operations
- **Customizable**: Configure model, temperature, and behavior through environment variables
- **Demo Mode**: Run without API access for demonstration purposes

## Usage

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (create a `.env` file based on `.env.example`)
4. Run the agent: `python main.py`

### Command-Line Options

- `--safe`: Run in safe mode (read-only)
- `--demo`: Run in demo mode with mock responses (no API calls)
- `--working-dir`: Specify working directory

## Environment Variables

Configure these in your `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_BASE_URL`: Custom OpenAI API endpoint (optional)
- `MODEL_NAME`: Model to use (default: "gpt-4o")
- `TEMPERATURE`: Temperature setting (default: 0)
- `VERBOSE`: Enable verbose output (default: True)
- `DETAILED_PROMPT`: Use detailed system prompt (default: False)
- `SAFE_MODE`: Run in safe mode (read-only) (default: False)
- `APPROVAL_NEEDED`: Require approval for dangerous operations (default: True)
- `MAX_ITERATIONS`: Maximum iterations per agent run (default: 10)
- `MAX_CONSECUTIVE_TOOL_CALLS`: Maximum consecutive calls to the same tool (default: 3)
- `MAX_IDENTICAL_TOOL_CALLS`: Maximum identical calls to the same tool with same args (default: 2)

## Architecture

The agent consists of several key components:

1. **Tools**: Implemented as LangChain `BaseTool` classes:
   - File tools (`FileSearchTool`, `PathSearchTool`, `FileReadTool`, `FileEditTool`, `FileWriteTool`, `ListDirectoryTool`)
   - Terminal tools (`ExecuteCommandTool`, `PersistentTerminalCreateTool`, etc.)

2. **Agent**: `CodeAgent` class that:
   - Uses OpenAI's function calling API
   - Manages tool selection based on mode (safe vs. full)
   - Handles conversation history
   - Manages approval requests for dangerous operations

3. **Prompts**: System messages for different modes (standard, detailed, safe)

## Safety Features

The agent includes several safety mechanisms:

1. **Safe Mode**: When enabled, only allows read-only operations
2. **Approval System**: Prompts for user approval before executing potentially dangerous operations
3. **Tool Wrappers**: Tools are wrapped with additional validation and error handling
4. **Loop Prevention**: Detects and prevents infinite loops and repetitive tool calls
5. **Empty File Detection**: Handles empty files gracefully without entering infinite read loops
6. **Proper Error Handling**: Provides clear error messages for common issues (file not found, permission denied, etc.)

## Custom API Endpoint

To use a custom OpenAI API endpoint, set the `OPENAI_BASE_URL` environment variable in your `.env` file:

```
OPENAI_BASE_URL=https://your-custom-endpoint.com/v1
```

This is useful for:
- Using OpenAI-compatible APIs hosted on your own infrastructure
- Routing requests through a proxy
- Using third-party API compatibility layers

## Customization

To extend or customize the agent:

1. Add new tools by creating subclasses of `BaseTool`
2. Modify system prompts in `agent/prompts.py`
3. Adjust safety parameters in `.env` or via command line arguments

## License

[MIT License](LICENSE) 