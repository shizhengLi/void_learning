"""
Helper utilities for the code editor agent.
"""

import os
import re
from typing import List, Dict, Optional, Tuple


class CodebaseAnalyzer:
    """Utility for analyzing codebases."""
    
    @staticmethod
    def get_file_extensions(directory: str) -> Dict[str, int]:
        """Get file extensions in a directory and their counts.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Dictionary mapping extensions to counts
        """
        extensions = {}
        
        for root, _, files in os.walk(directory):
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
                    
        return extensions
    
    @staticmethod
    def detect_project_type(directory: str) -> str:
        """Detect the type of project in a directory.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Project type description
        """
        # Check for common project files
        files = os.listdir(directory)
        files_lower = [f.lower() for f in files]
        
        # Python project detection
        if 'setup.py' in files or 'pyproject.toml' in files or 'requirements.txt' in files:
            return 'Python project'
            
        # JavaScript/Node.js detection
        if 'package.json' in files:
            # Check if it's React
            with open(os.path.join(directory, 'package.json'), 'r') as f:
                content = f.read()
                if '"react"' in content:
                    return 'React project'
            return 'Node.js project'
            
        # Java project detection
        if 'pom.xml' in files or 'build.gradle' in files:
            return 'Java project'
            
        # .NET project detection
        if any(f.endswith('.csproj') or f.endswith('.sln') for f in files):
            return '.NET project'
            
        # Rust project detection
        if 'cargo.toml' in files_lower:
            return 'Rust project'
            
        # Go project detection
        if 'go.mod' in files or 'go.sum' in files:
            return 'Go project'
            
        # Ruby project detection
        if 'gemfile' in files_lower or 'gemfile.lock' in files_lower:
            return 'Ruby project'
            
        # Default
        return 'Unknown project type'
    
    @staticmethod
    def count_lines_of_code(directory: str, extensions: Optional[List[str]] = None) -> Dict[str, int]:
        """Count lines of code in a directory by extension.
        
        Args:
            directory: Directory to analyze
            extensions: List of extensions to count (default: None, count all)
            
        Returns:
            Dictionary mapping extensions to line counts
        """
        line_counts = {}
        
        for root, _, files in os.walk(directory):
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                
                # Skip extensions not in the list
                if extensions and ext not in extensions:
                    continue
                    
                # Count lines
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                        line_counts[ext] = line_counts.get(ext, 0) + line_count
                except Exception:
                    # Skip files that can't be read as text
                    pass
                    
        return line_counts


class SearchHelper:
    """Utilities for searching in code."""
    
    @staticmethod
    def find_function_definition(code: str, function_name: str) -> Optional[Tuple[int, int, str]]:
        """Find the definition of a function in code.
        
        Args:
            code: The code to search
            function_name: The name of the function to find
            
        Returns:
            Tuple of (start_line, end_line, function_code) if found, None otherwise
        """
        lines = code.split('\n')
        
        # Common patterns for function definitions in different languages
        patterns = [
            # Python
            rf'def\s+{function_name}\s*\([^)]*\):',
            # JavaScript/TypeScript
            rf'function\s+{function_name}\s*\([^)]*\)',
            # C-style (C, C++, Java, etc.)
            rf'[a-zA-Z_][a-zA-Z0-9_]*\s+{function_name}\s*\([^)]*\)'
        ]
        
        start_line = -1
        end_line = -1
        brace_count = 0
        in_function = False
        
        for i, line in enumerate(lines):
            if not in_function:
                # Look for function definition
                if any(re.search(pattern, line) for pattern in patterns):
                    start_line = i
                    in_function = True
                    
                    # Check for opening brace
                    brace_count += line.count('{') - line.count('}')
                    
                    # Python functions don't use braces
                    if re.search(patterns[0], line) and ':' in line:
                        # This is a Python function, we'll detect the end by indentation
                        for j in range(i + 1, len(lines)):
                            # Python function ends when indentation decreases
                            if j == len(lines) - 1 or (lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t')):
                                end_line = j
                                break
            else:
                # Already in function, look for the end
                brace_count += line.count('{') - line.count('}')
                
                if brace_count <= 0:
                    end_line = i
                    break
                    
        if start_line >= 0 and end_line >= 0:
            function_code = '\n'.join(lines[start_line:end_line + 1])
            return start_line, end_line, function_code
            
        return None


class CodeFormatter:
    """Utilities for formatting code."""
    
    @staticmethod
    def format_search_replace(original: str, updated: str) -> str:
        """Format code for search/replace blocks.
        
        Args:
            original: Original code
            updated: Updated code
            
        Returns:
            Formatted search/replace block
        """
        return f"<<<<<<< ORIGINAL\n{original}=======\n{updated}>>>>>>> UPDATED" 