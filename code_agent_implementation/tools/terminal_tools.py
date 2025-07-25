"""
Terminal tools for the code editor agent.
These tools provide capabilities for executing commands and managing terminal sessions.
"""

from langchain.tools import BaseTool
import subprocess
import threading
import time
import uuid
import os
from typing import Dict, Optional, Any, List, Union


class TerminalStore:
    """Store for persistent terminals."""
    _terminals: Dict[str, subprocess.Popen] = {}
    
    @classmethod
    def create_terminal(cls, cwd: Optional[str] = None) -> str:
        """Create a new persistent terminal and return its ID.
        
        Args:
            cwd: The working directory for the terminal
            
        Returns:
            Terminal ID
        """
        terminal_id = str(uuid.uuid4())
        
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
        """Get a terminal by ID.
        
        Args:
            terminal_id: The ID of the terminal to get
            
        Returns:
            Terminal process or None if not found
        """
        return cls._terminals.get(terminal_id)
    
    @classmethod
    def kill_terminal(cls, terminal_id: str) -> bool:
        """Kill a terminal by ID.
        
        Args:
            terminal_id: The ID of the terminal to kill
            
        Returns:
            True if terminal was killed, False otherwise
        """
        terminal = cls.get_terminal(terminal_id)
        if terminal:
            terminal.terminate()
            terminal.wait()
            del cls._terminals[terminal_id]
            return True
        return False
    
    @classmethod
    def list_terminals(cls) -> List[str]:
        """List all terminal IDs.
        
        Returns:
            List of terminal IDs
        """
        return list(cls._terminals.keys())


class ExecuteCommandTool(BaseTool):
    """Tool for executing a single command."""
    name: str = "run_command"
    description: str = "Execute a terminal command and return the output"
    
    def _run(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a command and return the output.
        
        Args:
            command: The command to execute
            cwd: The working directory for the command
            
        Returns:
            Dictionary with output and exit code
        """
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
            return {
                "output": f"Error executing command: {str(e)}",
                "exit_code": -1
            }


class PersistentTerminalCreateTool(BaseTool):
    """Tool for creating a persistent terminal."""
    name: str = "open_persistent_terminal"
    description: str = "Open a persistent terminal that can be used for multiple commands"
    
    def _run(self, cwd: Optional[str] = None) -> Dict[str, str]:
        """Create a persistent terminal and return its ID.
        
        Args:
            cwd: The working directory for the terminal
            
        Returns:
            Dictionary with terminal ID and message
        """
        terminal_id = TerminalStore.create_terminal(cwd)
        return {
            "persistent_terminal_id": terminal_id,
            "message": f"Persistent terminal created with ID: {terminal_id}"
        }


class PersistentTerminalCommandTool(BaseTool):
    """Tool for running a command in a persistent terminal."""
    name: str = "run_persistent_command"
    description: str = "Run a command in a persistent terminal"
    
    def _run(self, command: str, persistent_terminal_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Run a command in a persistent terminal.
        
        Args:
            command: The command to run
            persistent_terminal_id: The ID of the terminal to use
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with output and exit code
        """
        terminal = TerminalStore.get_terminal(persistent_terminal_id)
        if not terminal:
            return {
                "output": f"Error: Terminal with ID {persistent_terminal_id} not found",
                "exit_code": -1
            }
        
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
                    "output": output + f"\n[Command timed out after {timeout} seconds]",
                    "timed_out": True,
                    "exit_code": -1
                }
                
            return {
                "output": output,
                "exit_code": exit_code
            }
        except Exception as e:
            return {
                "output": f"Error running command: {str(e)}",
                "exit_code": -1
            }


class PersistentTerminalKillTool(BaseTool):
    """Tool for killing a persistent terminal."""
    name: str = "kill_persistent_terminal"
    description: str = "Kill a persistent terminal"
    
    def _run(self, persistent_terminal_id: str) -> str:
        """Kill a persistent terminal.
        
        Args:
            persistent_terminal_id: The ID of the terminal to kill
            
        Returns:
            Success or error message
        """
        if TerminalStore.kill_terminal(persistent_terminal_id):
            return f"Terminal {persistent_terminal_id} killed successfully"
        else:
            return f"Error: Terminal with ID {persistent_terminal_id} not found"


class ListTerminalsTool(BaseTool):
    """Tool for listing all persistent terminals."""
    name: str = "list_terminals"
    description: str = "List all persistent terminals"
    
    def _run(self) -> List[str]:
        """List all persistent terminals.
        
        Returns:
            List of terminal IDs
        """
        return TerminalStore.list_terminals() 