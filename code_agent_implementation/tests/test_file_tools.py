"""
Tests for the file tools module.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from tools.file_tools import FileReadTool, FileWriteTool, FileEditTool, FileSearchTool, PathSearchTool


class FileToolsTests(unittest.TestCase):
    """Test cases for file system tools."""
    
    def setUp(self):
        """Set up test environment with temporary directory and files."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some test files
        self.test_file1 = os.path.join(self.temp_dir, 'test1.txt')
        with open(self.test_file1, 'w', encoding='utf-8') as f:
            f.write('This is test file 1.\nIt has multiple lines.\nIncluding a special keyword: testcontent.')
        
        self.test_file2 = os.path.join(self.temp_dir, 'test2.py')
        with open(self.test_file2, 'w', encoding='utf-8') as f:
            f.write('def test_function():\n    print("Hello, world!")\n    return 42')
        
        # Create a subdirectory with a file
        self.sub_dir = os.path.join(self.temp_dir, 'subdir')
        os.mkdir(self.sub_dir)
        self.test_file3 = os.path.join(self.sub_dir, 'test3.txt')
        with open(self.test_file3, 'w', encoding='utf-8') as f:
            f.write('This is test file in a subdirectory.')
            
    def tearDown(self):
        """Clean up temporary directory after tests."""
        shutil.rmtree(self.temp_dir)
        
    def test_file_read_tool(self):
        """Test FileReadTool functionality."""
        tool = FileReadTool()
        
        # Test reading an entire file
        content = tool._run(self.test_file1)
        self.assertIn('This is test file 1.', content)
        self.assertIn('testcontent', content)
        
        # Test reading specific lines
        content = tool._run(self.test_file1, 1, 2)
        self.assertIn('It has multiple lines.', content)
        self.assertNotIn('This is test file 1.', content)
        
        # Test reading a non-existent file
        content = tool._run(os.path.join(self.temp_dir, 'nonexistent.txt'))
        self.assertIn('Error reading file', content)
        
    def test_file_write_tool(self):
        """Test FileWriteTool functionality."""
        tool = FileWriteTool()
        
        # Test writing a new file
        new_file = os.path.join(self.temp_dir, 'new_file.txt')
        result = tool._run(new_file, 'This is a new file.')
        self.assertIn('written successfully', result)
        self.assertTrue(os.path.exists(new_file))
        
        with open(new_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, 'This is a new file.')
        
        # Test writing to a new directory
        new_dir_file = os.path.join(self.temp_dir, 'newdir', 'file.txt')
        result = tool._run(new_dir_file, 'File in a new directory.')
        self.assertIn('written successfully', result)
        self.assertTrue(os.path.exists(new_dir_file))
        
    def test_file_edit_tool(self):
        """Test FileEditTool functionality."""
        tool = FileEditTool()
        
        # Create a sample file for editing
        edit_file = os.path.join(self.temp_dir, 'edit_file.txt')
        with open(edit_file, 'w', encoding='utf-8') as f:
            f.write('Line 1\nLine 2\nLine 3\n')
        
        # Test editing with search/replace blocks
        search_replace = '<<<<<<< ORIGINAL\nLine 2\n=======\nModified Line 2\n>>>>>>> UPDATED'
        result = tool._run(edit_file, search_replace)
        self.assertIn('edited successfully', result)
        
        with open(edit_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Modified Line 2', content)
        
        # Check for exact line, not substring
        lines = content.splitlines()
        self.assertIn('Modified Line 2', lines)
        self.assertNotIn('Line 2', lines)  # This checks if 'Line 2' exists as a whole line
        
        # Test editing with a non-matching block
        search_replace = '<<<<<<< ORIGINAL\nNon-existent line\n=======\nNew line\n>>>>>>> UPDATED'
        result = tool._run(edit_file, search_replace)
        self.assertIn('Error: Original block not found', result)
        
    def test_file_search_tool(self):
        """Test FileSearchTool functionality."""
        tool = FileSearchTool()
        
        # Test searching for content
        results = tool._run('testcontent', self.temp_dir)
        self.assertIn(self.test_file1, results)
        self.assertNotIn(self.test_file2, results)
        
        # Test regex search
        results = tool._run('def.*\(', self.temp_dir, True)
        self.assertIn(self.test_file2, results)
        self.assertNotIn(self.test_file1, results)
        
    def test_path_search_tool(self):
        """Test PathSearchTool functionality."""
        tool = PathSearchTool()
        
        # Change directory to temp_dir for relative path search
        original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Test searching by name
            results = tool._run('test')
            self.assertTrue(any('test1.txt' in r for r in results))
            self.assertTrue(any('test2.py' in r for r in results))
            
            # Test searching with pattern
            results = tool._run('', '*.py')
            self.assertTrue(any('test2.py' in r for r in results))
            self.assertFalse(any('test1.txt' in r for r in results))
        finally:
            # Change back to original directory
            os.chdir(original_dir)


if __name__ == '__main__':
    unittest.main() 