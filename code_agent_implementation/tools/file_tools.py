"""
File system tools for the code editor agent.
These tools provide capabilities for searching, reading, and editing files.
"""

from langchain.tools import BaseTool
from typing import Optional, List, Dict, Any, Type
import os
import glob
import re


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
        
        return results


class PathSearchTool(BaseTool):
    """Tool for searching file paths."""
    name: str = "search_pathnames_only"
    description: str = "Search for files with names matching a pattern"
    
    def _run(self, query: str, include_pattern: Optional[str] = None) -> List[str]:
        """Search for files with names matching the pattern.
        
        Args:
            query: The filename pattern to search for
            include_pattern: Optional glob pattern to filter results
            
        Returns:
            List of matching file paths
        """
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
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the search/replace blocks
            blocks = self._parse_search_replace_blocks(search_replace_blocks)
            
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
        except Exception as e:
            return f"Error editing file: {str(e)}"
    
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
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File {file_path} written successfully."
        except Exception as e:
            return f"Error writing file: {str(e)}" 