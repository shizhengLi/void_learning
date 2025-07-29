"""
Tree对象实现

Tree对象用于存储目录结构，是Merkle Tree的内部节点
"""

import os
import sys
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.hash import HashCalculator
from objects.blob import Blob


@dataclass
class TreeEntry:
    """Tree条目"""
    mode: str  # 文件模式，如 "100644"（普通文件）、"100755"（可执行文件）、"040000"（目录）
    obj_type: str  # 对象类型：blob或tree
    hash: str  # 对象哈希
    name: str  # 文件/目录名
    
    def __str__(self) -> str:
        return f"{self.mode} {self.obj_type} {self.hash[:8]}... {self.name}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TreeEntry):
            return False
        return (self.mode == other.mode and 
                self.obj_type == other.obj_type and 
                self.hash == other.hash and 
                self.name == other.name)


class Tree:
    """Tree对象 - 存储目录结构"""
    
    def __init__(self):
        """初始化Tree对象"""
        self.entries: Dict[str, TreeEntry] = {}  # 文件名 -> TreeEntry
        self._hash = None
        self._content = None
    
    @property
    def hash(self) -> str:
        """获取Tree对象的哈希值"""
        if self._hash is None:
            content = self._get_content()
            self._hash = HashCalculator.hash_object('tree', content)
        return self._hash
    
    @property
    def type(self) -> str:
        """获取对象类型"""
        return 'tree'
    
    @property
    def size(self) -> int:
        """获取Tree对象的大小"""
        return len(self._get_content())
    
    def _get_content(self) -> str:
        """获取Tree对象的内容"""
        if self._content is None:
            # 按名称排序条目
            sorted_entries = sorted(self.entries.values(), key=lambda x: x.name)
            
            # 构建内容
            lines = []
            for entry in sorted_entries:
                line = f"{entry.mode} {entry.obj_type} {entry.hash}\t{entry.name}"
                lines.append(line)
            
            self._content = '\n'.join(lines)
        
        return self._content
    
    def add_entry(self, entry: TreeEntry) -> None:
        """
        添加条目到Tree
        
        Args:
            entry: TreeEntry对象
        """
        self.entries[entry.name] = entry
        self._hash = None  # 重置哈希
        self._content = None  # 重置内容
    
    def add_blob(self, blob: Blob, name: str, mode: str = "100644") -> None:
        """
        添加Blob对象到Tree
        
        Args:
            blob: Blob对象
            name: 文件名
            mode: 文件模式
        """
        entry = TreeEntry(mode=mode, obj_type='blob', hash=blob.hash, name=name)
        self.add_entry(entry)
    
    def add_tree(self, tree: 'Tree', name: str, mode: str = "040000") -> None:
        """
        添加子Tree到Tree
        
        Args:
            tree: Tree对象
            name: 目录名
            mode: 目录模式
        """
        entry = TreeEntry(mode=mode, obj_type='tree', hash=tree.hash, name=name)
        self.add_entry(entry)
    
    def remove_entry(self, name: str) -> bool:
        """
        从Tree中移除条目
        
        Args:
            name: 条目名称
            
        Returns:
            是否成功移除
        """
        if name in self.entries:
            del self.entries[name]
            self._hash = None  # 重置哈希
            self._content = None  # 重置内容
            return True
        return False
    
    def get_entry(self, name: str) -> Optional[TreeEntry]:
        """
        获取指定名称的条目
        
        Args:
            name: 条目名称
            
        Returns:
            TreeEntry对象或None
        """
        return self.entries.get(name)
    
    def get_entries(self) -> List[TreeEntry]:
        """
        获取所有条目
        
        Returns:
            TreeEntry列表
        """
        return list(self.entries.values())
    
    def get_blob_entries(self) -> List[TreeEntry]:
        """
        获取所有Blob条目
        
        Returns:
            Blob条目列表
        """
        return [entry for entry in self.entries.values() if entry.obj_type == 'blob']
    
    def get_tree_entries(self) -> List[TreeEntry]:
        """
        获取所有Tree条目
        
        Returns:
            Tree条目列表
        """
        return [entry for entry in self.entries.values() if entry.obj_type == 'tree']
    
    def serialize(self) -> bytes:
        """
        序列化Tree对象
        
        Returns:
            序列化后的字节数据
        """
        content = self._get_content()
        header = f"tree {len(content)}\0"
        return header.encode('utf-8') + content.encode('utf-8')
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Tree':
        """
        反序列化Tree对象
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            Tree对象
        """
        # 查找分隔符
        null_pos = data.find(b'\0')
        if null_pos == -1:
            raise ValueError("无效的Tree对象格式")
        
        # 解析头部
        header = data[:null_pos].decode('utf-8')
        parts = header.split(' ')
        if len(parts) != 2 or parts[0] != 'tree':
            raise ValueError("无效的Tree对象头部")
        
        # 获取内容
        content = data[null_pos + 1:].decode('utf-8')
        
        # 创建Tree对象
        tree = cls()
        
        # 解析条目
        if content:
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) != 2:
                        continue
                    
                    obj_info = parts[0]
                    name = parts[1]
                    
                    obj_parts = obj_info.split(' ')
                    if len(obj_parts) != 3:
                        continue
                    
                    mode, obj_type, obj_hash = obj_parts
                    entry = TreeEntry(mode=mode, obj_type=obj_type, hash=obj_hash, name=name)
                    tree.add_entry(entry)
        
        return tree
    
    @classmethod
    def from_directory(cls, directory: str) -> 'Tree':
        """
        从目录创建Tree对象
        
        Args:
            directory: 目录路径
            
        Returns:
            Tree对象
        """
        tree = cls()
        
        if not os.path.exists(directory):
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        # 遍历目录
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isfile(item_path):
                # 创建Blob对象
                blob = Blob.from_file(item_path)
                tree.add_blob(blob, item)
            elif os.path.isdir(item_path):
                # 创建子Tree对象
                subtree = cls.from_directory(item_path)
                tree.add_tree(subtree, item)
        
        return tree
    
    def __str__(self) -> str:
        """字符串表示"""
        entries_str = '\n  '.join(str(entry) for entry in self.get_entries())
        return f"Tree(hash={self.hash[:8]}..., entries={len(self.entries)}):\n  {entries_str}"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"Tree(hash='{self.hash}', entries={len(self.entries)})"
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Tree):
            return False
        return self.hash == other.hash
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.hash)