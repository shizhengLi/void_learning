"""
索引管理实现

实现Git风格的索引管理，用于跟踪工作区和暂存区的文件状态
"""

import os
import sys
import json
from typing import Dict, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.hash import HashCalculator


@dataclass
class IndexEntry:
    """索引条目"""
    path: str                    # 文件路径
    mode: str                    # 文件模式
    blob_hash: str               # Blob对象哈希
    size: int                    # 文件大小
    mtime: float                 # 修改时间
    stage: int = 0               # 暂存区阶段（用于合并）
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'IndexEntry':
        """从字典创建"""
        return cls(**data)


class Index:
    """索引管理器"""
    
    def __init__(self, repo_path: str):
        """
        初始化索引管理器
        
        Args:
            repo_path: 仓库路径
        """
        self.repo_path = Path(repo_path)
        self.index_file = self.repo_path / '.pygit' / 'index'
        self.entries: Dict[str, IndexEntry] = {}  # path -> IndexEntry
        
        # 确保索引目录存在
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载现有索引
        self.load()
    
    def load(self) -> None:
        """加载索引文件"""
        if not self.index_file.exists():
            return
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.entries.clear()
            for entry_data in data.get('entries', []):
                entry = IndexEntry.from_dict(entry_data)
                self.entries[entry.path] = entry
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"警告: 索引文件损坏，重新创建: {e}")
            self.entries.clear()
    
    def save(self) -> None:
        """保存索引文件"""
        data = {
            'version': 1,
            'entries': [entry.to_dict() for entry in self.entries.values()]
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_entry(self, entry: IndexEntry) -> None:
        """
        添加索引条目
        
        Args:
            entry: 索引条目
        """
        self.entries[entry.path] = entry
        self.save()
    
    def remove_entry(self, path: str) -> bool:
        """
        移除索引条目
        
        Args:
            path: 文件路径
            
        Returns:
            是否成功移除
        """
        if path in self.entries:
            del self.entries[path]
            self.save()
            return True
        return False
    
    def get_entry(self, path: str) -> Optional[IndexEntry]:
        """
        获取索引条目
        
        Args:
            path: 文件路径
            
        Returns:
            索引条目或None
        """
        return self.entries.get(path)
    
    def has_entry(self, path: str) -> bool:
        """
        检查索引中是否存在指定路径
        
        Args:
            path: 文件路径
            
        Returns:
            是否存在
        """
        return path in self.entries
    
    def list_entries(self) -> List[IndexEntry]:
        """
        获取所有索引条目
        
        Returns:
            索引条目列表
        """
        return list(self.entries.values())
    
    def get_tracked_files(self) -> Set[str]:
        """
        获取所有跟踪的文件路径
        
        Returns:
            文件路径集合
        """
        return set(self.entries.keys())
    
    def add_file(self, file_path: str, mode: str = "100644") -> Optional[IndexEntry]:
        """
        添加文件到索引
        
        Args:
            file_path: 文件路径
            mode: 文件模式
            
        Returns:
            创建的索引条目或None
        """
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not full_path.is_file():
            raise ValueError(f"不是文件: {file_path}")
        
        # 获取文件信息
        stat = full_path.stat()
        size = stat.st_size
        mtime = stat.st_mtime
        
        # 计算文件哈希
        blob_hash = HashCalculator.hash_file_content(str(full_path))
        
        # 创建索引条目
        entry = IndexEntry(
            path=file_path,
            mode=mode,
            blob_hash=blob_hash,
            size=size,
            mtime=mtime
        )
        
        self.add_entry(entry)
        return entry
    
    def remove_file(self, file_path: str) -> bool:
        """
        从索引中移除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功移除
        """
        return self.remove_entry(file_path)
    
    def is_file_modified(self, file_path: str) -> bool:
        """
        检查文件是否被修改
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否被修改
        """
        entry = self.get_entry(file_path)
        if not entry:
            return False
        
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return True
        
        # 检查修改时间
        stat = full_path.stat()
        if stat.st_mtime != entry.mtime:
            return True
        
        # 检查文件大小
        if stat.st_size != entry.size:
            return True
        
        # 检查文件内容哈希
        current_hash = HashCalculator.hash_file_content(str(full_path))
        if current_hash != entry.blob_hash:
            return True
        
        return False
    
    def get_modified_files(self) -> List[str]:
        """
        获取所有被修改的文件
        
        Returns:
            被修改的文件路径列表
        """
        modified = []
        
        for file_path in self.get_tracked_files():
            if self.is_file_modified(file_path):
                modified.append(file_path)
        
        return modified
    
    def get_untracked_files(self) -> List[str]:
        """
        获取未被跟踪的文件
        
        Returns:
            未被跟踪的文件路径列表
        """
        untracked = []
        tracked_files = self.get_tracked_files()
        
        # 遍历工作目录
        for root, dirs, files in os.walk(self.repo_path):
            # 跳过.git/.pygit目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(self.repo_path))
                
                if rel_path not in tracked_files:
                    untracked.append(rel_path)
        
        return untracked
    
    def get_staged_files(self) -> List[str]:
        """
        获取所有暂存的文件
        
        Returns:
            暂存的文件路径列表
        """
        return list(self.get_tracked_files())
    
    def update_entry(self, file_path: str) -> Optional[IndexEntry]:
        """
        更新索引条目
        
        Args:
            file_path: 文件路径
            
        Returns:
            更新后的索引条目或None
        """
        entry = self.get_entry(file_path)
        if not entry:
            return None
        
        return self.add_file(file_path, entry.mode)
    
    def clear(self) -> None:
        """清空索引"""
        self.entries.clear()
        self.save()
    
    def get_stats(self) -> Dict:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        total_files = len(self.entries)
        total_size = sum(entry.size for entry in self.entries.values())
        modified_files = len(self.get_modified_files())
        untracked_files = len(self.get_untracked_files())
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'modified_files': modified_files,
            'untracked_files': untracked_files,
            'staged_files': total_files
        }
    
    def validate(self) -> Dict:
        """
        验证索引完整性
        
        Returns:
            验证结果字典
        """
        valid_entries = 0
        invalid_entries = 0
        missing_files = 0
        modified_files = 0
        
        for entry in self.entries.values():
            full_path = self.repo_path / entry.path
            
            if not full_path.exists():
                missing_files += 1
                invalid_entries += 1
            elif self.is_file_modified(entry.path):
                modified_files += 1
                invalid_entries += 1
            else:
                valid_entries += 1
        
        return {
            'total_entries': len(self.entries),
            'valid_entries': valid_entries,
            'invalid_entries': invalid_entries,
            'missing_files': missing_files,
            'modified_files': modified_files
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Index(entries={len(self.entries)})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"Index(repo_path='{self.repo_path}', entries={len(self.entries)})"