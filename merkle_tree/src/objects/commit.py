"""
Commit对象实现

Commit对象用于存储提交信息，是Merkle Tree的根节点
"""

import os
import sys
from typing import Optional, List
from datetime import datetime

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.hash import HashCalculator
from objects.tree import Tree


class Commit:
    """Commit对象 - 存储提交信息"""
    
    def __init__(self, 
                 tree_hash: str,
                 parent_hash: Optional[str] = None,
                 author: str = "",
                 committer: str = "",
                 message: str = "",
                 timestamp: Optional[datetime] = None):
        """
        初始化Commit对象
        
        Args:
            tree_hash: 关联的Tree对象哈希
            parent_hash: 父Commit对象哈希
            author: 作者信息
            committer: 提交者信息
            message: 提交消息
            timestamp: 提交时间
        """
        self.tree_hash = tree_hash
        self.parent_hash = parent_hash
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or datetime.now()
        
        self._hash = None
        self._content = None
    
    @property
    def hash(self) -> str:
        """获取Commit对象的哈希值"""
        if self._hash is None:
            content = self._get_content()
            self._hash = HashCalculator.hash_object('commit', content)
        return self._hash
    
    @property
    def type(self) -> str:
        """获取对象类型"""
        return 'commit'
    
    @property
    def size(self) -> int:
        """获取Commit对象的大小"""
        return len(self._get_content())
    
    def _get_content(self) -> str:
        """获取Commit对象的内容"""
        if self._content is None:
            lines = []
            
            # 添加tree信息
            lines.append(f"tree {self.tree_hash}")
            
            # 添加parent信息
            if self.parent_hash:
                lines.append(f"parent {self.parent_hash}")
            
            # 添加author信息
            if self.author:
                timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"author {self.author} {timestamp_str}")
            
            # 添加committer信息
            if self.committer:
                timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"committer {self.committer} {timestamp_str}")
            
            # 添加空行分隔符
            lines.append("")
            
            # 添加提交消息
            lines.append(self.message)
            
            self._content = '\n'.join(lines)
        
        return self._content
    
    def set_tree(self, tree: Tree) -> None:
        """
        设置关联的Tree对象
        
        Args:
            tree: Tree对象
        """
        self.tree_hash = tree.hash
        self._hash = None  # 重置哈希
        self._content = None  # 重置内容
    
    def set_parent(self, parent_commit: 'Commit') -> None:
        """
        设置父Commit对象
        
        Args:
            parent_commit: 父Commit对象
        """
        self.parent_hash = parent_commit.hash
        self._hash = None  # 重置哈希
        self._content = None  # 重置内容
    
    def get_parent_hash(self) -> Optional[str]:
        """
        获取父Commit哈希
        
        Returns:
            父Commit哈希或None
        """
        return self.parent_hash
    
    def is_initial_commit(self) -> bool:
        """
        判断是否为初始提交
        
        Returns:
            是否为初始提交
        """
        return self.parent_hash is None
    
    def serialize(self) -> bytes:
        """
        序列化Commit对象
        
        Returns:
            序列化后的字节数据
        """
        content = self._get_content()
        header = f"commit {len(content)}\0"
        return header.encode('utf-8') + content.encode('utf-8')
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Commit':
        """
        反序列化Commit对象
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            Commit对象
        """
        # 查找分隔符
        null_pos = data.find(b'\0')
        if null_pos == -1:
            raise ValueError("无效的Commit对象格式")
        
        # 解析头部
        header = data[:null_pos].decode('utf-8')
        parts = header.split(' ')
        if len(parts) != 2 or parts[0] != 'commit':
            raise ValueError("无效的Commit对象头部")
        
        # 获取内容
        content = data[null_pos + 1:].decode('utf-8')
        
        # 解析内容
        lines = content.split('\n')
        
        tree_hash = ""
        parent_hash = None
        author = ""
        committer = ""
        timestamp = None
        message_lines = []
        
        # 解析头部信息
        i = 0
        while i < len(lines) and lines[i].strip():
            line = lines[i].strip()
            if line.startswith('tree '):
                tree_hash = line[5:]
            elif line.startswith('parent '):
                parent_hash = line[7:]
            elif line.startswith('author '):
                author = line[7:]
            elif line.startswith('committer '):
                committer = line[10:]
            i += 1
        
        # 跳过空行
        while i < len(lines) and not lines[i].strip():
            i += 1
        
        # 获取提交消息
        while i < len(lines):
            message_lines.append(lines[i])
            i += 1
        
        message = '\n'.join(message_lines).strip()
        
        # 解析时间戳（简化处理）
        if committer:
            parts = committer.split()
            if len(parts) >= 2:
                try:
                    timestamp_str = ' '.join(parts[-2:])
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        return cls(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            author=author,
            committer=committer,
            message=message,
            timestamp=timestamp
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        parent_str = f"parent={self.parent_hash[:8]}..." if self.parent_hash else "parent=None"
        return f"Commit(hash={self.hash[:8]}..., tree={self.tree_hash[:8]}..., {parent_str})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"Commit(hash='{self.hash}', tree_hash='{self.tree_hash}', parent_hash='{self.parent_hash}')"
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Commit):
            return False
        return self.hash == other.hash
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.hash)