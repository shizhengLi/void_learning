"""
对象数据库实现

实现Git风格的对象数据库，用于存储和管理所有Git对象
"""

import os
import sys
import zlib
from typing import Dict, Optional, Union, List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from objects.blob import Blob
from objects.tree import Tree
from objects.commit import Commit
from objects.tag import Tag


class ObjectDatabase:
    """对象数据库"""
    
    def __init__(self, repo_path: str):
        """
        初始化对象数据库
        
        Args:
            repo_path: 仓库路径
        """
        self.repo_path = Path(repo_path)
        self.objects_dir = self.repo_path / '.pygit' / 'objects'
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        
        # 对象类型映射
        self.object_classes = {
            'blob': Blob,
            'tree': Tree,
            'commit': Commit,
            'tag': Tag
        }
    
    def _get_object_path(self, hash_value: str) -> Path:
        """
        获取对象存储路径
        
        Args:
            hash_value: 对象哈希值
            
        Returns:
            对象存储路径
        """
        if len(hash_value) < 2:
            raise ValueError(f"无效的哈希值: {hash_value}")
        
        # Git风格的对象存储：前两个字符作为目录名，剩余部分作为文件名
        dir_name = hash_value[:2]
        file_name = hash_value[2:]
        
        return self.objects_dir / dir_name / file_name
    
    def _compress_object(self, data: bytes) -> bytes:
        """
        压缩对象数据
        
        Args:
            data: 原始数据
            
        Returns:
            压缩后的数据
        """
        return zlib.compress(data)
    
    def _decompress_object(self, data: bytes) -> bytes:
        """
        解压缩对象数据
        
        Args:
            data: 压缩的数据
            
        Returns:
            解压缩后的数据
        """
        return zlib.decompress(data)
    
    def store_object(self, obj: Union[Blob, Tree, Commit, Tag]) -> str:
        """
        存储对象到数据库
        
        Args:
            obj: 要存储的对象
            
        Returns:
            对象的哈希值
        """
        hash_value = obj.hash
        object_path = self._get_object_path(hash_value)
        
        # 如果对象已存在，直接返回哈希值
        if object_path.exists():
            return hash_value
        
        # 序列化对象
        serialized_data = obj.serialize()
        
        # 压缩数据
        compressed_data = self._compress_object(serialized_data)
        
        # 确保目录存在
        object_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(object_path, 'wb') as f:
            f.write(compressed_data)
        
        return hash_value
    
    def get_object(self, hash_value: str) -> Union[Blob, Tree, Commit, Tag]:
        """
        从数据库获取对象
        
        Args:
            hash_value: 对象哈希值
            
        Returns:
            对象实例
            
        Raises:
            FileNotFoundError: 对象不存在
            ValueError: 无效的对象类型
        """
        object_path = self._get_object_path(hash_value)
        
        if not object_path.exists():
            raise FileNotFoundError(f"对象不存在: {hash_value}")
        
        # 读取压缩数据
        with open(object_path, 'rb') as f:
            compressed_data = f.read()
        
        # 解压缩数据
        serialized_data = self._decompress_object(compressed_data)
        
        # 解析对象类型
        null_pos = serialized_data.find(b'\0')
        if null_pos == -1:
            raise ValueError(f"无效的对象格式: {hash_value}")
        
        header = serialized_data[:null_pos].decode('utf-8')
        parts = header.split(' ')
        if len(parts) != 2:
            raise ValueError(f"无效的对象头部: {hash_value}")
        
        obj_type = parts[0]
        
        # 根据类型反序列化对象
        if obj_type not in self.object_classes:
            raise ValueError(f"未知的对象类型: {obj_type}")
        
        obj_class = self.object_classes[obj_type]
        return obj_class.deserialize(serialized_data)
    
    def object_exists(self, hash_value: str) -> bool:
        """
        检查对象是否存在
        
        Args:
            hash_value: 对象哈希值
            
        Returns:
            对象是否存在
        """
        object_path = self._get_object_path(hash_value)
        return object_path.exists()
    
    def delete_object(self, hash_value: str) -> bool:
        """
        删除对象
        
        Args:
            hash_value: 对象哈希值
            
        Returns:
            是否成功删除
        """
        object_path = self._get_object_path(hash_value)
        
        if object_path.exists():
            object_path.unlink()
            # 尝试删除空目录
            try:
                object_path.parent.rmdir()
            except OSError:
                pass  # 目录不为空，忽略错误
            return True
        
        return False
    
    def list_objects(self, obj_type: Optional[str] = None) -> List[str]:
        """
        列出所有对象
        
        Args:
            obj_type: 对象类型过滤
            
        Returns:
            对象哈希值列表
        """
        objects = []
        
        # 遍历对象目录
        for dir_path in self.objects_dir.iterdir():
            if not dir_path.is_dir():
                continue
            
            for file_path in dir_path.iterdir():
                if not file_path.is_file():
                    continue
                
                # 构建哈希值
                hash_value = dir_path.name + file_path.name
                
                # 如果指定了类型，检查对象类型
                if obj_type:
                    try:
                        obj = self.get_object(hash_value)
                        if obj.type != obj_type:
                            continue
                    except Exception:
                        continue
                
                objects.append(hash_value)
        
        return sorted(objects)
    
    def get_object_info(self, hash_value: str) -> Dict:
        """
        获取对象信息
        
        Args:
            hash_value: 对象哈希值
            
        Returns:
            对象信息字典
        """
        try:
            obj = self.get_object(hash_value)
            object_path = self._get_object_path(hash_value)
            
            return {
                'hash': hash_value,
                'type': obj.type,
                'size': obj.size,
                'path': str(object_path),
                'exists': object_path.exists()
            }
        except Exception as e:
            return {
                'hash': hash_value,
                'error': str(e),
                'exists': False
            }
    
    def get_stats(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_objects': 0,
            'objects_by_type': {},
            'total_size': 0
        }
        
        for hash_value in self.list_objects():
            try:
                obj = self.get_object(hash_value)
                object_path = self._get_object_path(hash_value)
                file_size = object_path.stat().st_size
                
                stats['total_objects'] += 1
                stats['total_size'] += file_size
                
                obj_type = obj.type
                if obj_type not in stats['objects_by_type']:
                    stats['objects_by_type'][obj_type] = 0
                stats['objects_by_type'][obj_type] += 1
                
            except Exception:
                continue
        
        return stats
    
    def verify_integrity(self) -> Dict:
        """
        验证数据库完整性
        
        Returns:
            完整性验证结果
        """
        results = {
            'total_objects': 0,
            'valid_objects': 0,
            'corrupted_objects': 0,
            'corrupted_list': []
        }
        
        for hash_value in self.list_objects():
            results['total_objects'] += 1
            
            try:
                obj = self.get_object(hash_value)
                # 验证哈希值
                if obj.hash == hash_value:
                    results['valid_objects'] += 1
                else:
                    results['corrupted_objects'] += 1
                    results['corrupted_list'].append(hash_value)
            except Exception:
                results['corrupted_objects'] += 1
                results['corrupted_list'].append(hash_value)
        
        return results
    
    def cleanup(self) -> None:
        """
        清理数据库
        删除空目录
        """
        for dir_path in self.objects_dir.iterdir():
            if not dir_path.is_dir():
                continue
            
            try:
                # 尝试删除空目录
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except OSError:
                pass  # 目录不为空，忽略错误