"""
Tag对象实现

Tag对象用于存储标签信息，用于标记特定的Commit
"""

import os
import sys
from typing import Optional
from datetime import datetime

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.hash import HashCalculator
from objects.commit import Commit


class Tag:
    """Tag对象 - 存储标签信息"""
    
    def __init__(self,
                 tag_name: str,
                 target_hash: str,
                 target_type: str = "commit",
                 tagger: str = "",
                 message: str = "",
                 timestamp: Optional[datetime] = None):
        """
        初始化Tag对象
        
        Args:
            tag_name: 标签名称
            target_hash: 目标对象哈希
            target_type: 目标对象类型
            tagger: 标签创建者
            message: 标签消息
            timestamp: 创建时间
        """
        self.tag_name = tag_name
        self.target_hash = target_hash
        self.target_type = target_type
        self.tagger = tagger
        self.message = message
        self.timestamp = timestamp or datetime.now()
        
        self._hash = None
        self._content = None
    
    @property
    def hash(self) -> str:
        """获取Tag对象的哈希值"""
        if self._hash is None:
            content = self._get_content()
            self._hash = HashCalculator.hash_object('tag', content)
        return self._hash
    
    @property
    def type(self) -> str:
        """获取对象类型"""
        return 'tag'
    
    @property
    def size(self) -> int:
        """获取Tag对象的大小"""
        return len(self._get_content())
    
    def _get_content(self) -> str:
        """获取Tag对象的内容"""
        if self._content is None:
            lines = []
            
            # 添加对象信息
            lines.append(f"object {self.target_hash}")
            lines.append(f"type {self.target_type}")
            lines.append(f"tag {self.tag_name}")
            
            # 添加tagger信息
            if self.tagger:
                timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"tagger {self.tagger} {timestamp_str}")
            
            # 添加空行分隔符
            lines.append("")
            
            # 添加标签消息
            lines.append(self.message)
            
            self._content = '\n'.join(lines)
        
        return self._content
    
    def set_target(self, commit: Commit) -> None:
        """
        设置目标Commit对象
        
        Args:
            commit: 目标Commit对象
        """
        self.target_hash = commit.hash
        self.target_type = commit.type
        self._hash = None  # 重置哈希
        self._content = None  # 重置内容
    
    def serialize(self) -> bytes:
        """
        序列化Tag对象
        
        Returns:
            序列化后的字节数据
        """
        content = self._get_content()
        header = f"tag {len(content)}\0"
        return header.encode('utf-8') + content.encode('utf-8')
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'Tag':
        """
        反序列化Tag对象
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            Tag对象
        """
        # 查找分隔符
        null_pos = data.find(b'\0')
        if null_pos == -1:
            raise ValueError("无效的Tag对象格式")
        
        # 解析头部
        header = data[:null_pos].decode('utf-8')
        parts = header.split(' ')
        if len(parts) != 2 or parts[0] != 'tag':
            raise ValueError("无效的Tag对象头部")
        
        # 获取内容
        content = data[null_pos + 1:].decode('utf-8')
        
        # 解析内容
        lines = content.split('\n')
        
        target_hash = ""
        target_type = ""
        tag_name = ""
        tagger = ""
        timestamp = None
        message_lines = []
        
        # 解析头部信息
        i = 0
        while i < len(lines) and lines[i].strip():
            line = lines[i].strip()
            if line.startswith('object '):
                target_hash = line[7:]
            elif line.startswith('type '):
                target_type = line[5:]
            elif line.startswith('tag '):
                tag_name = line[4:]
            elif line.startswith('tagger '):
                tagger = line[7:]
            i += 1
        
        # 跳过空行
        while i < len(lines) and not lines[i].strip():
            i += 1
        
        # 获取标签消息
        while i < len(lines):
            message_lines.append(lines[i])
            i += 1
        
        message = '\n'.join(message_lines).strip()
        
        # 解析时间戳（简化处理）
        if tagger:
            parts = tagger.split()
            if len(parts) >= 2:
                try:
                    timestamp_str = ' '.join(parts[-2:])
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        return cls(
            tag_name=tag_name,
            target_hash=target_hash,
            target_type=target_type,
            tagger=tagger,
            message=message,
            timestamp=timestamp
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Tag(name='{self.tag_name}', target={self.target_hash[:8]}..., type={self.target_type})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"Tag(tag_name='{self.tag_name}', target_hash='{self.target_hash}', target_type='{self.target_type}')"
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Tag):
            return False
        return self.hash == other.hash
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.hash)