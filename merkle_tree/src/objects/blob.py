"""
Blob对象实现

Blob对象用于存储文件内容，是Merkle Tree的叶子节点
"""

import os
import sys
from typing import Union

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.hash import HashCalculator


class Blob:
    """Blob对象 - 存储文件内容"""
    
    def __init__(self, content: Union[str, bytes] = ""):
        """
        初始化Blob对象
        
        Args:
            content: 文件内容
        """
        if isinstance(content, str):
            self.content = content.encode('utf-8')
        else:
            self.content = content
        
        self._hash = None
        self._size = len(self.content)
    
    @property
    def hash(self) -> str:
        """获取Blob对象的哈希值"""
        if self._hash is None:
            self._hash = HashCalculator.hash_object('blob', self.content)
        return self._hash
    
    @property
    def size(self) -> int:
        """获取Blob对象的大小"""
        return self._size
    
    @property
    def type(self) -> str:
        """获取对象类型"""
        return 'blob'
    
    def get_content(self) -> bytes:
        """获取Blob对象的内容"""
        return self.content
    
    def get_content_string(self) -> str:
        """获取Blob对象的字符串内容"""
        return self.content.decode('utf-8')
    
    def serialize(self) -> bytes:
        """
        序列化Blob对象
        
        Returns:
            序列化后的字节数据
        """
        header = f"blob {self.size}\0"
        return header.encode('utf-8') + self.content
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Blob':
        """
        反序列化Blob对象
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            Blob对象
        """
        # 查找分隔符
        null_pos = data.find(b'\0')
        if null_pos == -1:
            raise ValueError("无效的Blob对象格式")
        
        # 解析头部
        header = data[:null_pos].decode('utf-8')
        parts = header.split(' ')
        if len(parts) != 2 or parts[0] != 'blob':
            raise ValueError("无效的Blob对象头部")
        
        # 获取内容
        content = data[null_pos + 1:]
        
        return cls(content)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Blob':
        """
        从文件创建Blob对象
        
        Args:
            file_path: 文件路径
            
        Returns:
            Blob对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        return cls(content)
    
    def to_file(self, file_path: str) -> None:
        """
        将Blob对象写入文件
        
        Args:
            file_path: 文件路径
        """
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:  # 只有当目录路径不为空时才创建
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(self.content)
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Blob(hash={self.hash[:8]}..., size={self.size})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"Blob(hash='{self.hash}', size={self.size})"
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Blob):
            return False
        return self.hash == other.hash
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.hash)