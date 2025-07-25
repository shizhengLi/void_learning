"""
Code editor agent implementation.
"""

import os
import inspect
import json
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, HumanMessage, FunctionMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.config import RunnableConfig
from langchain.memory.chat_memory import InMemoryChatMessageHistory
from langchain.callbacks import StdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler

from .prompts import SYSTEM_MESSAGE, DETAILED_SYSTEM_MESSAGE, SAFE_SYSTEM_MESSAGE


# Custom callback handler to track and prevent tool call loops
class LoopPreventionHandler(BaseCallbackHandler):
    """Callback handler to prevent infinite loops in tool calls."""

    def __init__(self, max_consecutive_calls: int = 3, max_identical_calls: int = 2):
        """Initialize the loop prevention handler.
        
        Args:
            max_consecutive_calls: Maximum number of consecutive calls to the same tool
            max_identical_calls: Maximum number of identical calls (same tool + same args)
        """
        self.tool_call_history = []
        self.consecutive_calls = {}
        self.identical_calls = {}
        self.max_consecutive_calls = max_consecutive_calls
        self.max_identical_calls = max_identical_calls
        # 特别处理空文件的情况
        self.empty_file_reads = set()

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when a tool starts running.
        
        Args:
            serialized: Information about the tool
            input_str: Input to the tool
        """
        tool_name = serialized.get("name", "unknown")
        
        # 特别处理文件读取的情况
        if tool_name == "read_file" and "file_path" in input_str:
            # 尝试提取文件路径
            try:
                import json
                args = json.loads(input_str)
                file_path = args.get("file_path", "")
                
                # 如果这个文件之前被检测为空，直接提前结束
                if file_path in self.empty_file_reads:
                    raise ValueError(
                        f"Avoiding repeated reads of empty file: {file_path}"
                    )
            except json.JSONDecodeError:
                pass
        
        # Create a hash of tool name + args to track identical calls
        call_hash = hashlib.md5(f"{tool_name}:{input_str}".encode()).hexdigest()
        
        # Track consecutive calls to the same tool
        if tool_name in self.consecutive_calls:
            self.consecutive_calls[tool_name] += 1
        else:
            self.consecutive_calls = {tool_name: 1}
            
        # Track identical calls
        if call_hash in self.identical_calls:
            self.identical_calls[call_hash] += 1
        else:
            self.identical_calls[call_hash] = 1
            
        # Check for loops
        if self.consecutive_calls[tool_name] > self.max_consecutive_calls:
            raise ValueError(
                f"Potential infinite loop detected: Tool '{tool_name}' called {self.consecutive_calls[tool_name]} times consecutively."
            )
        
        if self.identical_calls[call_hash] > self.max_identical_calls:
            raise ValueError(
                f"Potential infinite loop detected: Identical call to '{tool_name}' with the same arguments detected multiple times."
            )
        
        # Add to history
        self.tool_call_history.append((tool_name, input_str))
        
        # Keep history at a reasonable size
        if len(self.tool_call_history) > 100:
            self.tool_call_history = self.tool_call_history[-100:]
            
    def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool finishes running.
        
        Args:
            output: Output of the tool
        """
        if not self.tool_call_history:
            return
            
        # 检查最后一次调用是否是read_file，且返回空字符串
        last_tool, last_input = self.tool_call_history[-1]
        if last_tool == "read_file" and output == '':
            try:
                import json
                args = json.loads(last_input)
                file_path = args.get("file_path", "")
                if file_path:
                    # 标记这个文件是空的，避免重复读取
                    self.empty_file_reads.add(file_path)
            except json.JSONDecodeError:
                pass


def _convert_tool_to_openai_function(tool: BaseTool) -> Dict[str, Any]:
    """Convert a LangChain tool to an OpenAI function format.
    
    Args:
        tool: The tool to convert
        
    Returns:
        The tool in OpenAI function format
    """
    # Get function signature
    schema = {"type": "object", "properties": {}}
    parameters = {}
    
    # Get signature of the _run method
    sig = inspect.signature(tool._run)
    
    # Add required parameters
    required_params = []
    
    for name, param in sig.parameters.items():
        # Skip 'self'
        if name == "self":
            continue
            
        # Get parameter type and default
        param_type = "string"  # Default type
        has_default = param.default != inspect.Parameter.empty
        
        # Try to infer type from annotation
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == str:
                param_type = "string"
            elif param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            
        # Add parameter to schema
        parameters[name] = {"type": param_type}
        
        # Add description if available
        if hasattr(tool, "arg_descriptions") and name in tool.arg_descriptions:
            parameters[name]["description"] = tool.arg_descriptions.get(name)
            
        # If no default value, it's required
        if not has_default:
            required_params.append(name)
    
    # Build the function definition
    schema["properties"] = parameters
    if required_params:
        schema["required"] = required_params
        
    function_def = {
        "name": tool.name,
        "description": tool.description,
        "parameters": schema
    }
    
    return function_def


# Custom function to format intermediate steps to ensure proper message structure
def custom_format_to_openai_function_messages(intermediate_steps):
    """Format intermediate steps to ensure valid message structure.
    
    Args:
        intermediate_steps: List of (action, observation) tuples
        
    Returns:
        List of messages
    """
    messages = []
    for action, observation in intermediate_steps:
        messages.append(
            FunctionMessage(
                name=action.tool,
                content=str(observation) if observation is not None else "",
            )
        )
    return messages


class CodeAgent:
    """Code editor agent implementation."""
    
    def __init__(
        self, 
        tools: List[BaseTool], 
        model_name: str = "gpt-4o", 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = True,
        detailed_prompt: bool = False,
        safe_mode: bool = False,
        approval_needed: bool = True,
        max_iterations: int = 10,
        max_consecutive_tool_calls: int = 3,
        max_identical_tool_calls: int = 2
    ):
        """Initialize the code agent with tools and model.
        
        Args:
            tools: List of tools to provide to the agent
            model_name: Name of the model to use
            api_key: API key for the model provider
            base_url: Base URL for the OpenAI API (optional for custom endpoints)
            temperature: Temperature for the model
            verbose: Whether to enable verbose output
            detailed_prompt: Whether to use the detailed prompt
            safe_mode: Whether to run in safe mode (read-only)
            approval_needed: Whether to require approval for dangerous operations
            max_iterations: Maximum number of iterations for the agent
            max_consecutive_tool_calls: Maximum number of consecutive calls to the same tool
            max_identical_tool_calls: Maximum number of identical calls to the same tool with same args
        """
        self.tools = tools
        self.verbose = verbose
        self.approval_needed = approval_needed
        self.safe_mode = safe_mode
        self.max_iterations = max_iterations
        
        # Initialize memory using the new approach
        self.chat_history = InMemoryChatMessageHistory()
        
        # Initialize loop prevention
        self.loop_prevention = LoopPreventionHandler(
            max_consecutive_calls=max_consecutive_tool_calls,
            max_identical_calls=max_identical_tool_calls
        )
        
        # Select which tools to use based on mode
        if safe_mode:
            self.active_tools = [tool for tool in tools if not self._is_dangerous_tool(tool.name)]
        else:
            self.active_tools = tools
        
        # Initialize LLM with optional custom base_url
        llm_kwargs = {
            "model": model_name,
            "temperature": temperature,
        }
        
        if api_key:
            llm_kwargs["api_key"] = api_key
            
        if base_url:
            llm_kwargs["base_url"] = base_url
            
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # Select which prompt template to use
        if safe_mode:
            system_message = SAFE_SYSTEM_MESSAGE
        elif detailed_prompt:
            system_message = DETAILED_SYSTEM_MESSAGE
        else:
            system_message = SYSTEM_MESSAGE
            
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        
        # Convert tools to OpenAI functions
        openai_functions = [_convert_tool_to_openai_function(tool) for tool in self.active_tools]
        
        # Create the agent using the new LangChain API
        self.agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", []),
                "agent_scratchpad": lambda x: custom_format_to_openai_function_messages(
                    x.get("intermediate_steps", [])
                ),
                "tools": lambda _: self._get_tools_description(),
                "tool_names": lambda _: ", ".join([tool.name for tool in self.active_tools]),
            }
            | prompt
            | self.llm.bind(functions=openai_functions)
            | OpenAIFunctionsAgentOutputParser()
        )
        
        # Create the callbacks
        callbacks = [self.loop_prevention]
        if verbose:
            callbacks.append(StdOutCallbackHandler())
            
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.active_tools,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=self.max_iterations,
            callbacks=callbacks
        )
    
    def _wrap_tool_for_safety(self, tool: BaseTool) -> BaseTool:
        """Wrap a tool with additional safety checks.
        
        Args:
            tool: The tool to wrap
            
        Returns:
            Wrapped tool with safety checks
        """
        original_run = tool._run
        
        def safe_run(*args, **kwargs):
            try:
                # For file operations, check if file exists first for certain tools
                if tool.name == "read_file" and "file_path" in kwargs:
                    file_path = kwargs["file_path"]
                    
                    # 检查文件是否存在
                    if not os.path.exists(file_path):
                        return f"Error: File '{file_path}' does not exist. Please verify the path."
                    
                    # 检查是否为文件
                    if not os.path.isfile(file_path):
                        return f"Error: '{file_path}' is a directory, not a file."
                    
                    # 检查文件是否为空
                    if os.path.getsize(file_path) == 0:
                        return f"Note: File '{file_path}' exists but is empty."
                    
                # Run the original tool
                result = original_run(*args, **kwargs)
                
                # 特别处理文件读取返回空字符串的情况
                if tool.name == "read_file" and result == '' and "file_path" in kwargs:
                    file_path = kwargs["file_path"]
                    return f"Note: File '{file_path}' exists but is empty."
                
                # Ensure result is not None
                if result is None:
                    return "Operation completed successfully but returned no output."
                
                return result
            except Exception as e:
                # Provide a helpful error message
                return f"Error using {tool.name}: {str(e)}"
        
        # Replace the original run method with the safe version
        tool._run = safe_run
        
        return tool
        
    async def run(self, query: str) -> Dict[str, Any]:
        """Run the agent on a query.
        
        Args:
            query: The query to run the agent on
            
        Returns:
            Dictionary with agent response
        """
        # Reset loop prevention handler for new query
        self.loop_prevention = LoopPreventionHandler()
        
        # Add user message to chat history
        self.chat_history.add_user_message(query)
        
        # Wrap tools with safety checks
        safe_tools = [self._wrap_tool_for_safety(tool) for tool in self.active_tools]
        
        # If approval is needed, wrap the tools with approval handlers
        if self.approval_needed and not self.safe_mode:
            # Create wrapped tools with approval
            wrapped_tools = self._wrap_tools_with_approval(safe_tools)
            
            # Create a temporary agent executor with wrapped tools
            temp_executor = AgentExecutor(
                agent=self.agent,
                tools=wrapped_tools,
                verbose=self.verbose,
                handle_parsing_errors=True,
                max_iterations=self.max_iterations,
                callbacks=[self.loop_prevention]
            )
            
            try:
                # Run the agent
                result = await temp_executor.ainvoke({
                    "input": query, 
                    "chat_history": self.chat_history.messages
                })
                
                # Add AI response to chat history
                self.chat_history.add_ai_message(result["output"])
                
                return result
            except Exception as e:
                error_message = f"Error during agent execution: {str(e)}"
                print(f"\n❌ {error_message}")
                # Add error message to chat history
                self.chat_history.add_ai_message(f"I encountered an error: {str(e)}. Let's try again with a different approach.")
                return {"output": error_message}
        else:
            try:
                # Create a temporary agent executor with safe tools
                temp_executor = AgentExecutor(
                    agent=self.agent,
                    tools=safe_tools,
                    verbose=self.verbose,
                    handle_parsing_errors=True,
                    max_iterations=self.max_iterations,
                    callbacks=[self.loop_prevention]
                )
                
                # Run without approval
                result = await temp_executor.ainvoke({
                    "input": query, 
                    "chat_history": self.chat_history.messages
                })
                
                # Add AI response to chat history
                self.chat_history.add_ai_message(result["output"])
                
                return result
            except Exception as e:
                error_message = f"Error during agent execution: {str(e)}"
                print(f"\n❌ {error_message}")
                # Add error message to chat history
                self.chat_history.add_ai_message(f"I encountered an error: {str(e)}. Let's try again with a different approach.")
                return {"output": error_message}
    
    def _get_tools_description(self) -> str:
        """Get a string description of all available tools.
        
        Returns:
            String description of all tools
        """
        return "\n".join([f"{i+1}. {tool.name}: {tool.description}" 
                         for i, tool in enumerate(self.active_tools)])
        
    def _is_dangerous_tool(self, tool_name: str) -> bool:
        """Check if a tool is considered dangerous.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if the tool is dangerous, False otherwise
        """
        dangerous_tools = [
            "edit_file",
            "write_file", 
            "run_command", 
            "run_persistent_command", 
            "open_persistent_terminal",
            "kill_persistent_terminal"
        ]
        return tool_name in dangerous_tools
    
    def _wrap_tools_with_approval(self, tools: List[BaseTool]) -> List[BaseTool]:
        """Wrap tools with approval handlers.
        
        Args:
            tools: List of tools to wrap
            
        Returns:
            List of wrapped tools
        """
        wrapped_tools = []
        
        for tool in tools:
            if self._is_dangerous_tool(tool.name):
                # Create a wrapped version of the tool
                wrapped_tool = self._create_approval_wrapped_tool(tool)
                wrapped_tools.append(wrapped_tool)
            else:
                # Keep non-dangerous tools as they are
                wrapped_tools.append(tool)
                
        return wrapped_tools
    
    def _create_approval_wrapped_tool(self, tool: BaseTool) -> BaseTool:
        """Create a wrapped version of a tool that requires approval.
        
        Args:
            tool: The tool to wrap
            
        Returns:
            Wrapped tool
        """
        # Store the original _run method
        original_run = tool._run
        
        # Create a new _run method that requires approval
        def wrapped_run(*args, **kwargs):
            # Format the arguments for display
            args_str = ", ".join([str(arg) for arg in args])
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            all_args = args_str + (", " if args_str and kwargs_str else "") + kwargs_str
            
            # Ask for approval
            print(f"\n⚠️  The agent wants to use {tool.name} with args: {all_args}")
            approval = input("Allow this action? (y/n): ")
            
            if approval.lower() == 'y':
                # Run the original tool
                result = original_run(*args, **kwargs)
                # Ensure result is a string to avoid null content errors
                if result is None:
                    return "Operation completed successfully but returned no output."
                return result
            else:
                # Return a rejection message
                return f"Action cancelled by user: {tool.name}({all_args})"
        
        # Replace the _run method
        tool._run = wrapped_run
        
        return tool


def create_agent_from_env(tools: List[BaseTool]) -> CodeAgent:
    """Create a code agent using environment variables.
    
    Args:
        tools: List of tools to provide to the agent
        
    Returns:
        Initialized CodeAgent
    """
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    model_name = os.getenv("MODEL_NAME", "gpt-4o")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")  # Add support for custom base URL
    temperature = float(os.getenv("TEMPERATURE", "0"))
    verbose = os.getenv("VERBOSE", "True").lower() == "true"
    detailed_prompt = os.getenv("DETAILED_PROMPT", "False").lower() == "true"
    safe_mode = os.getenv("SAFE_MODE", "False").lower() == "true"
    approval_needed = os.getenv("APPROVAL_NEEDED", "True").lower() == "true"
    max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
    max_consecutive_calls = int(os.getenv("MAX_CONSECUTIVE_TOOL_CALLS", "3"))
    max_identical_calls = int(os.getenv("MAX_IDENTICAL_TOOL_CALLS", "2"))
    
    # Create and return the agent
    return CodeAgent(
        tools=tools,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        verbose=verbose,
        detailed_prompt=detailed_prompt,
        safe_mode=safe_mode,
        approval_needed=approval_needed,
        max_iterations=max_iterations,
        max_consecutive_tool_calls=max_consecutive_calls,
        max_identical_tool_calls=max_identical_calls
    ) 