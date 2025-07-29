"""
哈希计算模块

实现Git风格的哈希计算，包括：
- SHA-1哈希计算
- 对象内容格式化
- 文件内容哈希
"""

import hashlib
from typing import Union


class HashCalculator:
    """哈希计算器"""
    
    @staticmethod
    def sha1(data: Union[str, bytes]) -> str:
        """
        计算SHA-1哈希值
        
        Args:
            data: 要计算哈希的数据（字符串或字节）
            
        Returns:
            40位的十六进制哈希字符串
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.sha1(data).hexdigest()
    
    @staticmethod
    def hash_object(obj_type: str, content: Union[str, bytes]) -> str:
        """
        计算Git对象的哈希值
        
        Git对象格式: <type> <size>\0<content>
        
        Args:
            obj_type: 对象类型（blob, tree, commit）
            content: 对象内容
            
        Returns:
            对象的哈希值
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Git对象格式
        header = f"{obj_type} {len(content)}\0"
        full_content = header.encode('utf-8') + content
        
        return HashCalculator.sha1(full_content)
    
    @staticmethod
    def hash_file_content(file_path: str) -> str:
        """
        计算文件内容的哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容的哈希值
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return HashCalculator.sha1(content)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {file_path}")
        except Exception as e:
            raise Exception(f"读取文件失败: {file_path}, 错误: {e}")
    
    @staticmethod
    def hash_string_content(content: str) -> str:
        """
        计算字符串内容的哈希值
        
        Args:
            content: 字符串内容
            
        Returns:
            内容的哈希值
        """
        return HashCalculator.sha1(content)