"""
Merkle Tree实现

实现Merkle Tree的核心算法，用于构建和验证版本控制树结构
"""

import os
import sys
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from objects.blob import Blob
from objects.tree import Tree, TreeEntry
from objects.commit import Commit
from core.hash import HashCalculator


class MerkleTree:
    """Merkle Tree管理器"""
    
    def __init__(self, repo_path: str):
        """
        初始化Merkle Tree管理器
        
        Args:
            repo_path: 仓库路径
        """
        self.repo_path = Path(repo_path)
        self.hash_calculator = HashCalculator()
    
    def build_tree_from_directory(self, directory: str, ignore_patterns: Optional[List[str]] = None) -> Tree:
        """
        从目录构建Merkle Tree
        
        Args:
            directory: 目录路径
            ignore_patterns: 忽略的文件模式
            
        Returns:
            构建的Tree对象
        """
        if ignore_patterns is None:
            ignore_patterns = ['.git', '.pygit', '__pycache__', '.DS_Store']
        
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        root_tree = Tree()
        self._build_tree_recursive(directory_path, root_tree, ignore_patterns)
        
        return root_tree
    
    def _build_tree_recursive(self, current_path: Path, parent_tree: Tree, ignore_patterns: List[str]) -> None:
        """
        递归构建Tree结构
        
        Args:
            current_path: 当前路径
            parent_tree: 父Tree对象
            ignore_patterns: 忽略的文件模式
        """
        for item in current_path.iterdir():
            # 跳过忽略的文件/目录
            if any(pattern in item.name for pattern in ignore_patterns):
                continue
            
            if item.is_file():
                # 创建Blob对象
                blob = Blob.from_file(str(item))
                parent_tree.add_blob(blob, item.name)
            
            elif item.is_dir():
                # 创建子Tree对象
                subtree = Tree()
                self._build_tree_recursive(item, subtree, ignore_patterns)
                parent_tree.add_tree(subtree, item.name)
    
    def build_tree_from_files(self, files: Dict[str, str]) -> Tree:
        """
        从文件列表构建Merkle Tree
        
        Args:
            files: 文件路径到内容的映射
            
        Returns:
            构建的Tree对象
        """
        root_tree = Tree()
        
        # 按路径组织文件
        path_structure = {}
        for file_path, content in files.items():
            self._add_file_to_structure(path_structure, file_path, content)
        
        # 递归构建Tree
        self._build_tree_from_structure(path_structure, root_tree)
        
        return root_tree
    
    def _add_file_to_structure(self, structure: Dict, file_path: str, content: str) -> None:
        """
        添加文件到路径结构
        
        Args:
            structure: 路径结构字典
            file_path: 文件路径
            content: 文件内容
        """
        parts = Path(file_path).parts
        current_level = structure
        
        for i, part in enumerate(parts[:-1]):
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
        
        # 添加文件内容
        filename = parts[-1]
        if '__files__' not in current_level:
            current_level['__files__'] = {}
        current_level['__files__'][filename] = content
    
    def _build_tree_from_structure(self, structure: Dict, tree: Tree) -> None:
        """
        从路径结构构建Tree
        
        Args:
            structure: 路径结构字典
            tree: Tree对象
        """
        for key, value in structure.items():
            if key == '__files__':
                # 处理文件
                for filename, content in value.items():
                    blob = Blob(content)
                    tree.add_blob(blob, filename)
            else:
                # 处理子目录
                subtree = Tree()
                self._build_tree_from_structure(value, subtree)
                tree.add_tree(subtree, key)
    
    def compare_trees(self, tree1: Tree, tree2: Tree) -> Dict:
        """
        比较两个Tree的差异
        
        Args:
            tree1: 第一个Tree对象
            tree2: 第二个Tree对象
            
        Returns:
            差异结果字典
        """
        differences = {
            'added': [],      # 新增的文件
            'removed': [],    # 删除的文件
            'modified': [],   # 修改的文件
            'renamed': []     # 重命名的文件
        }
        
        entries1 = {entry.name: entry for entry in tree1.get_entries()}
        entries2 = {entry.name: entry for entry in tree2.get_entries()}
        
        names1 = set(entries1.keys())
        names2 = set(entries2.keys())
        
        # 查找新增的文件
        for name in names2 - names1:
            entry = entries2[name]
            if entry.obj_type == 'blob':
                differences['added'].append(name)
            else:
                differences['added'].append(name + '/')
        
        # 查找删除的文件
        for name in names1 - names2:
            entry = entries1[name]
            if entry.obj_type == 'blob':
                differences['removed'].append(name)
            else:
                differences['removed'].append(name + '/')
        
        # 查找修改的文件
        for name in names1 & names2:
            entry1 = entries1[name]
            entry2 = entries2[name]
            
            if entry1.hash != entry2.hash:
                if entry1.obj_type == 'blob':
                    differences['modified'].append(name)
                else:
                    # 递归比较子Tree
                    subtree1 = self._get_subtree(tree1, name)
                    subtree2 = self._get_subtree(tree2, name)
                    if subtree1 and subtree2:
                        sub_diff = self.compare_trees(subtree1, subtree2)
                        # 添加前缀
                        for key in sub_diff:
                            for item in sub_diff[key]:
                                differences[key].append(f"{name}/{item}")
        
        return differences
    
    def _get_subtree(self, tree: Tree, name: str) -> Optional[Tree]:
        """
        获取子Tree对象
        
        Args:
            tree: 父Tree对象
            name: 子Tree名称
            
        Returns:
            子Tree对象或None
        """
        entry = tree.get_entry(name)
        if entry and entry.obj_type == 'tree':
            # 这里需要从对象数据库获取实际的Tree对象
            # 暂时返回None，后续可以扩展
            return None
        return None
    
    def find_changed_files(self, old_tree: Tree, new_tree: Tree) -> List[str]:
        """
        查找变更的文件
        
        Args:
            old_tree: 旧的Tree对象
            new_tree: 新的Tree对象
            
        Returns:
            变更的文件路径列表
        """
        differences = self.compare_trees(old_tree, new_tree)
        changed_files = []
        
        # 添加所有类型的变更
        for change_type in ['added', 'removed', 'modified']:
            changed_files.extend(differences[change_type])
        
        return changed_files
    
    def get_file_hash(self, tree: Tree, file_path: str) -> Optional[str]:
        """
        获取指定文件的哈希值
        
        Args:
            tree: Tree对象
            file_path: 文件路径
            
        Returns:
            文件哈希值或None
        """
        parts = Path(file_path).parts
        current_tree = tree
        
        for i, part in enumerate(parts[:-1]):
            entry = current_tree.get_entry(part)
            if not entry or entry.obj_type != 'tree':
                return None
            # 这里需要获取实际的子Tree对象
            # 暂时返回None，后续可以扩展
            return None
        
        # 获取文件条目
        filename = parts[-1]
        entry = current_tree.get_entry(filename)
        if entry and entry.obj_type == 'blob':
            return entry.hash
        
        return None
    
    def list_files(self, tree: Tree, prefix: str = '') -> List[str]:
        """
        列出Tree中的所有文件
        
        Args:
            tree: Tree对象
            prefix: 路径前缀
            
        Returns:
            文件路径列表
        """
        files = []
        
        for entry in tree.get_entries():
            full_path = f"{prefix}/{entry.name}" if prefix else entry.name
            
            if entry.obj_type == 'blob':
                files.append(full_path)
            elif entry.obj_type == 'tree':
                # 递归列出子Tree中的文件
                # 这里需要获取实际的子Tree对象
                # 暂时只处理当前层级的文件
                pass
        
        return files
    
    def get_tree_statistics(self, tree: Tree) -> Dict:
        """
        获取Tree的统计信息
        
        Args:
            tree: Tree对象
            
        Returns:
            统计信息字典
        """
        stats = {
            'total_files': 0,
            'total_directories': 0,
            'total_size': 0,
            'files_by_type': {}
        }
        
        self._calculate_tree_stats(tree, stats)
        
        return stats
    
    def _calculate_tree_stats(self, tree: Tree, stats: Dict) -> None:
        """
        递归计算Tree统计信息
        
        Args:
            tree: Tree对象
            stats: 统计信息字典
        """
        for entry in tree.get_entries():
            if entry.obj_type == 'blob':
                stats['total_files'] += 1
                # 这里需要获取实际的Blob对象来获取大小
                # 暂时使用估计值
                stats['total_size'] += 1024  # 估计大小
            elif entry.obj_type == 'tree':
                stats['total_directories'] += 1
                # 递归计算子Tree
                # 这里需要获取实际的子Tree对象
                # 暂时只处理当前层级
    
    def validate_tree_integrity(self, tree: Tree) -> bool:
        """
        验证Tree的完整性
        
        Args:
            tree: Tree对象
            
        Returns:
            是否完整
        """
        try:
            # 验证Tree自身的哈希
            calculated_hash = self.hash_calculator.hash_object('tree', tree._get_content())
            if tree.hash != calculated_hash:
                return False
            
            # 验证所有条目
            for entry in tree.get_entries():
                # 这里需要验证条目指向的对象是否存在
                # 暂时只验证格式
                if not entry.name or not entry.hash:
                    return False
            
            return True
        except Exception:
            return False
    
    def create_commit(self, tree: Tree, message: str, parent_commit: Optional[Commit] = None,
                     author: str = '', committer: str = '') -> Commit:
        """
        创建Commit对象
        
        Args:
            tree: Tree对象
            message: 提交消息
            parent_commit: 父Commit对象
            author: 作者信息
            committer: 提交者信息
            
        Returns:
            创建的Commit对象
        """
        from datetime import datetime
        
        commit = Commit(
            tree_hash=tree.hash,
            parent_hash=parent_commit.hash if parent_commit else None,
            author=author,
            committer=committer,
            message=message,
            timestamp=datetime.now()
        )
        
        return commit
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"MerkleTree(repo_path='{self.repo_path}')"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"MerkleTree(repo_path='{self.repo_path}')"