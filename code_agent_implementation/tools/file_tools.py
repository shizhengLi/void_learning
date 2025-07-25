"""
File system tools for the code editor agent.
These tools provide capabilities for searching, reading, and editing files.
"""

from langchain.tools import BaseTool
from typing import Optional, List, Dict, Any, Type
import os
import glob
import re
import pathlib


class FileSearchTool(BaseTool):
    """Tool for searching file contents."""
    name: str = "search_for_files"
    description: str = "Search for files containing specific content"
    
    def _run(self, query: str, search_dir: Optional[str] = None, is_regex: bool = False) -> List[str]:
        """Search for files containing the specified content.
        
        Args:
            query: The content to search for
            search_dir: The directory to search in (defaults to current directory)
            is_regex: Whether to treat the query as a regex pattern
            
        Returns:
            List of file paths matching the query
        """
        if search_dir is None:
            search_dir = os.getcwd()
        
        # Check if the directory exists
        if not os.path.exists(search_dir):
            return [f"Error: Directory '{search_dir}' does not exist."]
            
        if not os.path.isdir(search_dir):
            return [f"Error: '{search_dir}' is not a directory."]
        
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
                except Exception:
                    # Skip files that can't be read as text
                    pass
                
                if len(results) >= 50:  # Limit results
                    break
        
        if not results:
            return [f"No files containing '{query}' found in '{search_dir}'."]
            
        return results


class PathSearchTool(BaseTool):
    """Tool for searching file paths."""
    name: str = "search_pathnames_only"
    description: str = "Search for files with names matching a pattern"
    
    def _run(self, query: str, include_pattern: Optional[str] = None) -> List[str]:
        """Search for files with names matching the pattern.
        
        Args:
            query: The filename pattern to search for (can be '*' for all files)
            include_pattern: Optional path or glob pattern (e.g. '/path/to/dir/*.py')
            
        Returns:
            List of matching file paths
        """
        results = []
        
        # If a specific include_pattern is provided (path or glob)
        if include_pattern:
            # Handle absolute paths
            if os.path.isabs(include_pattern):
                base_dir = os.path.dirname(include_pattern)
                file_pattern = os.path.basename(include_pattern)
                
                # Check if the directory exists
                if not os.path.exists(base_dir):
                    return [f"Error: Directory '{base_dir}' does not exist."]
                
                # If it's a directory without pattern
                if os.path.isdir(include_pattern):
                    base_dir = include_pattern
                    file_pattern = '*'
                
                # Get files with the given pattern in the specified directory
                if '*' in file_pattern:
                    for item in glob.glob(os.path.join(base_dir, file_pattern)):
                        if os.path.isfile(item):
                            results.append(item)
                else:
                    # Specific file
                    if os.path.exists(include_pattern) and os.path.isfile(include_pattern):
                        results.append(include_pattern)
            else:
                # Relative path or glob pattern
                for item in glob.glob(include_pattern, recursive=True):
                    if os.path.isfile(item):
                        results.append(item)
        else:
            # No specific path/pattern provided, search based on query
            # Special case for '*' to list all files in current directory
            if query == '*':
                for root, _, files in os.walk('.'):
                    for file in files:
                        results.append(os.path.join(root, file))
                        if len(results) >= 50:  # Limit results
                            break
                    if len(results) >= 50:
                        break
            # Search for files containing the query in their name
            else:
                for root, _, files in os.walk('.'):
                    for file in files:
                        if query.lower() in file.lower():
                            results.append(os.path.join(root, file))
                            if len(results) >= 50:  # Limit results
                                break
                    if len(results) >= 50:
                        break
        
        if not results:
            if include_pattern:
                return [f"No files found matching the pattern '{include_pattern}'."]
            else:
                return [f"No files found matching '{query}'."]
                
        return results[:50]  # Ensure limit of 50 results


class FileReadTool(BaseTool):
    """Tool for reading file contents."""
    name: str = "read_file"
    description: str = "Read the contents of a file"
    
    def _run(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file to read
            start_line: Optional start line (0-indexed)
            end_line: Optional end line (0-indexed)
            
        Returns:
            File contents as a string
        """
        # First, check if the file exists
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist. Please verify the path."
            
        # Check if it's actually a file
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is a directory, not a file."
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if start_line is None and end_line is None:
                    return f.read()
                else:
                    lines = f.readlines()
                    start = start_line if start_line is not None else 0
                    end = end_line if end_line is not None else len(lines)
                    return ''.join(lines[start:end])
        except UnicodeDecodeError:
            return f"Error: File '{file_path}' appears to be a binary file and cannot be read as text."
        except PermissionError:
            return f"Error: Permission denied when trying to read '{file_path}'."
        except Exception as e:
            return f"Error reading file '{file_path}': {str(e)}"


class FileEditTool(BaseTool):
    """Tool for editing file contents."""
    name: str = "edit_file"
    description: str = "Edit a file using search/replace blocks"
    
    def _run(self, file_path: str, search_replace_blocks: str) -> str:
        """
        Edit a file using search/replace blocks.
        
        Args:
            file_path: Path to the file to edit
            search_replace_blocks: String containing search/replace blocks formatted as:
                <<<<<<< ORIGINAL
                // original code
                =======
                // replaced code
                >>>>>>> UPDATED
                
        Returns:
            Success message or error
        """
        # First, check if the file exists
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist. Please verify the path."
            
        # Check if it's actually a file
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is a directory, not a file."
            
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the search/replace blocks
            blocks = self._parse_search_replace_blocks(search_replace_blocks)
            
            if not blocks:
                return "Error: No valid search/replace blocks found. Please check the format."
            
            # Apply each block
            new_content = content
            changes_applied = 0
            
            for block in blocks:
                original = block['original']
                updated = block['updated']
                
                # Perform an exact string replacement
                if original in new_content:
                    # Use replacement with exact string match
                    new_content = new_content.replace(original, updated)
                    changes_applied += 1
                else:
                    return f"Error: Original block not found in file: {original[:50]}..."
            
            # Write the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"File {file_path} edited successfully with {changes_applied} changes."
        except UnicodeDecodeError:
            return f"Error: File '{file_path}' appears to be a binary file and cannot be edited as text."
        except PermissionError:
            return f"Error: Permission denied when trying to edit '{file_path}'."
        except Exception as e:
            return f"Error editing file '{file_path}': {str(e)}"
    
    def _parse_search_replace_blocks(self, blocks_str: str) -> List[Dict[str, str]]:
        """Parse search/replace blocks from the input string.
        
        Args:
            blocks_str: String containing search/replace blocks
            
        Returns:
            List of dictionaries with 'original' and 'updated' keys
        """
        pattern = r'<<<<<<< ORIGINAL\n(.*?)=======\n(.*?)>>>>>>> UPDATED'
        matches = re.findall(pattern, blocks_str, re.DOTALL)
        
        blocks = []
        for match in matches:
            blocks.append({
                'original': match[0],
                'updated': match[1]
            })
        
        return blocks


class FileWriteTool(BaseTool):
    """Tool for writing new files."""
    name: str = "write_file"
    description: str = "Write content to a new file or overwrite an existing file"
    
    def _run(self, file_path: str, content: str) -> str:
        """Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            
        Returns:
            Success message or error
        """
        try:
            # Check if path is a directory
            if os.path.isdir(file_path):
                return f"Error: '{file_path}' is a directory, not a file."
                
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except PermissionError:
                    return f"Error: Permission denied when creating directory '{directory}'."
                except Exception as e:
                    return f"Error creating directory '{directory}': {str(e)}"
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File '{file_path}' written successfully."
        except PermissionError:
            return f"Error: Permission denied when writing to '{file_path}'."
        except Exception as e:
            return f"Error writing file '{file_path}': {str(e)}"


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""
    name: str = "list_directory"
    description: str = "List files and folders in a directory"
    
    def _run(self, directory: Optional[str] = None) -> Dict[str, List[str]]:
        """List files and folders in a directory.
        
        Args:
            directory: Path to the directory to list (defaults to current directory)
            
        Returns:
            Dictionary with 'files' and 'folders' keys containing lists of paths
        """
        if directory is None or directory == '.':
            directory = os.getcwd()
        
        # Check if directory exists
        if not os.path.exists(directory):
            return {
                "error": f"Error: Directory '{directory}' does not exist.",
                "files": [],
                "folders": [],
                "directory": directory
            }
            
        # Check if it's actually a directory
        if not os.path.isdir(directory):
            return {
                "error": f"Error: '{directory}' is a file, not a directory.",
                "files": [],
                "folders": [],
                "directory": directory
            }
        
        try:
            # Get all items in the directory
            items = os.listdir(directory)
            
            # Separate files and folders
            files = []
            folders = []
            
            for item in items:
                full_path = os.path.join(directory, item)
                if os.path.isfile(full_path):
                    files.append(item)
                elif os.path.isdir(full_path):
                    folders.append(item)
            
            return {
                "files": files,
                "folders": folders,
                "directory": directory
            }
        except PermissionError:
            return {
                "error": f"Error: Permission denied when listing directory '{directory}'.",
                "files": [],
                "folders": [],
                "directory": directory
            }
        except Exception as e:
            return {
                "error": f"Error listing directory '{directory}': {str(e)}",
                "files": [],
                "folders": [],
                "directory": directory
            } 