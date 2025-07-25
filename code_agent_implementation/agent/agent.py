"""
Code editor agent implementation.
"""

import os
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain.callbacks import StdOutCallbackHandler

from .prompts import SYSTEM_PROMPT, DETAILED_SYSTEM_PROMPT, SAFE_SYSTEM_PROMPT


class CodeAgent:
    """Code editor agent implementation."""
    
    def __init__(
        self, 
        tools: List[BaseTool], 
        model_name: str = "gpt-4o", 
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = True,
        detailed_prompt: bool = False,
        safe_mode: bool = False,
        approval_needed: bool = True
    ):
        """Initialize the code agent with tools and model.
        
        Args:
            tools: List of tools to provide to the agent
            model_name: Name of the model to use
            api_key: API key for the model provider
            temperature: Temperature for the model
            verbose: Whether to enable verbose output
            detailed_prompt: Whether to use the detailed prompt
            safe_mode: Whether to run in safe mode (read-only)
            approval_needed: Whether to require approval for dangerous operations
        """
        self.tools = tools
        self.verbose = verbose
        self.approval_needed = approval_needed
        self.safe_mode = safe_mode
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Select which tools to use based on mode
        if safe_mode:
            self.active_tools = [tool for tool in tools if not self._is_dangerous_tool(tool.name)]
        else:
            self.active_tools = tools
            
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key
        )
        
        # Select which prompt to use
        if safe_mode:
            prompt = SAFE_SYSTEM_PROMPT
        elif detailed_prompt:
            prompt = DETAILED_SYSTEM_PROMPT
        else:
            prompt = SYSTEM_PROMPT
            
        # Create the agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.active_tools,
            prompt=prompt
        )
        
        # Create the callbacks
        callbacks = []
        if verbose:
            callbacks.append(StdOutCallbackHandler())
            
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.active_tools,
            memory=self.memory,
            verbose=verbose,
            handle_parsing_errors=True,
            max_iterations=15,
            callbacks=callbacks
        )
        
    async def run(self, query: str) -> Dict[str, Any]:
        """Run the agent on a query.
        
        Args:
            query: The query to run the agent on
            
        Returns:
            Dictionary with agent response
        """
        # If approval is needed, wrap the tools with approval handlers
        if self.approval_needed and not self.safe_mode:
            # Create wrapped tools with approval
            wrapped_tools = self._wrap_tools_with_approval()
            
            # Create a new agent executor with wrapped tools
            temp_agent = create_react_agent(
                llm=self.llm,
                tools=wrapped_tools,
                prompt=self.agent.prompt
            )
            
            temp_executor = AgentExecutor(
                agent=temp_agent,
                tools=wrapped_tools,
                memory=self.memory,
                verbose=self.verbose,
                handle_parsing_errors=True,
                max_iterations=15
            )
            
            return await temp_executor.ainvoke({"input": query})
        else:
            # Run without approval
            return await self.agent_executor.ainvoke({"input": query})
        
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
    
    def _wrap_tools_with_approval(self) -> List[BaseTool]:
        """Wrap tools with approval handlers.
        
        Returns:
            List of wrapped tools
        """
        wrapped_tools = []
        
        for tool in self.active_tools:
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
                return original_run(*args, **kwargs)
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
    temperature = float(os.getenv("TEMPERATURE", "0"))
    verbose = os.getenv("VERBOSE", "True").lower() == "true"
    detailed_prompt = os.getenv("DETAILED_PROMPT", "False").lower() == "true"
    safe_mode = os.getenv("SAFE_MODE", "False").lower() == "true"
    approval_needed = os.getenv("APPROVAL_NEEDED", "True").lower() == "true"
    
    # Create and return the agent
    return CodeAgent(
        tools=tools,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        verbose=verbose,
        detailed_prompt=detailed_prompt,
        safe_mode=safe_mode,
        approval_needed=approval_needed
    ) 