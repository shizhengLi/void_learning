"""
仓库管理实现

实现完整的仓库管理功能，包括初始化、状态检查、提交等核心操作
"""

import os
import sys
import json
from typing import Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository import ObjectDatabase
from core.index import Index
from core.merkle import MerkleTree
from objects.blob import Blob
from objects.tree import Tree
from objects.commit import Commit
from objects.tag import Tag


class Repository:
    """仓库管理器"""
    
    def __init__(self, repo_path: str = '.'):
        """
        初始化仓库管理器
        
        Args:
            repo_path: 仓库路径
        """
        self.repo_path = Path(repo_path).resolve()
        self.pygit_dir = self.repo_path / '.pygit'
        
        # 检查是否为有效仓库
        self.is_valid_repo = self.pygit_dir.exists()
        
        if self.is_valid_repo:
            # 初始化组件
            self.odb = ObjectDatabase(str(self.repo_path))
            self.index = Index(str(self.repo_path))
            self.merkle_tree = MerkleTree(str(self.repo_path))
            
            # 加载仓库配置
            self.config = self._load_config()
            
            # 加载HEAD引用
            self.head = self._load_head()
        else:
            self.odb = None
            self.index = None
            self.merkle_tree = None
            self.config = {}
            self.head = None
    
    def _load_config(self) -> Dict:
        """加载仓库配置"""
        config_file = self.pygit_dir / 'config'
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_config(self) -> None:
        """保存仓库配置"""
        config_file = self.pygit_dir / 'config'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _load_head(self) -> Optional[str]:
        """加载HEAD引用"""
        head_file = self.pygit_dir / 'HEAD'
        if head_file.exists():
            try:
                with open(head_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith('ref: '):
                        # 分支引用
                        ref_name = content[5:]
                        ref_file = self.pygit_dir / ref_name
                        if ref_file.exists():
                            with open(ref_file, 'r', encoding='utf-8') as ref_f:
                                return ref_f.read().strip()
                    else:
                        # 直接指向commit
                        return content
            except IOError:
                pass
        return None
    
    def _save_head(self, commit_hash: str, ref_name: str = 'refs/heads/main') -> None:
        """保存HEAD引用"""
        # 保存HEAD文件
        head_file = self.pygit_dir / 'HEAD'
        with open(head_file, 'w', encoding='utf-8') as f:
            f.write(f'ref: {ref_name}')
        
        # 保存分支引用
        ref_file = self.pygit_dir / ref_name
        ref_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ref_file, 'w', encoding='utf-8') as f:
            f.write(commit_hash)
        
        self.head = commit_hash
    
    def init(self, bare: bool = False) -> None:
        """
        初始化仓库
        
        Args:
            bare: 是否为裸仓库
        """
        if self.is_valid_repo:
            raise ValueError("仓库已经存在")
        
        # 创建.pygit目录
        self.pygit_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.pygit_dir / 'objects').mkdir(parents=True, exist_ok=True)
        (self.pygit_dir / 'refs').mkdir(parents=True, exist_ok=True)
        (self.pygit_dir / 'refs' / 'heads').mkdir(parents=True, exist_ok=True)
        (self.pygit_dir / 'refs' / 'tags').mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.odb = ObjectDatabase(str(self.repo_path))
        self.index = Index(str(self.repo_path))
        self.merkle_tree = MerkleTree(str(self.repo_path))
        
        # 设置默认配置
        self.config = {
            'core': {
                'bare': bare,
                'repositoryformatversion': 0
            },
            'user': {
                'name': 'Unknown User',
                'email': 'unknown@example.com'
            }
        }
        self._save_config()
        
        # 创建HEAD文件
        head_file = self.pygit_dir / 'HEAD'
        with open(head_file, 'w', encoding='utf-8') as f:
            f.write('ref: refs/heads/main')
        
        self.is_valid_repo = True
        self.head = None
    
    def set_user_config(self, name: str, email: str) -> None:
        """
        设置用户配置
        
        Args:
            name: 用户名
            email: 邮箱
        """
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        self.config['user']['name'] = name
        self.config['user']['email'] = email
        self._save_config()
    
    def add(self, paths: List[str]) -> None:
        """
        添加文件到暂存区
        
        Args:
            paths: 文件路径列表
        """
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        for path in paths:
            file_path = Path(path)
            if file_path.is_absolute():
                # 转换为相对路径
                try:
                    rel_path = str(file_path.relative_to(self.repo_path))
                except ValueError:
                    raise ValueError(f"文件不在仓库内: {path}")
            else:
                rel_path = path
            
            full_path = self.repo_path / rel_path
            
            if not full_path.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            
            if full_path.is_file():
                self.index.add_file(rel_path)
            elif full_path.is_dir():
                # 递归添加目录
                self._add_directory_recursive(full_path)
    
    def _add_directory_recursive(self, directory: Path) -> None:
        """
        递归添加目录
        
        Args:
            directory: 目录路径
        """
        for item in directory.rglob('*'):
            if item.is_file():
                rel_path = str(item.relative_to(self.repo_path))
                self.index.add_file(rel_path)
    
    def add_all(self) -> None:
        """添加所有文件到暂存区"""
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        # 获取所有未跟踪和修改的文件
        untracked = self.index.get_untracked_files()
        modified = self.index.get_modified_files()
        
        all_files = set(untracked) | set(modified)
        
        for file_path in all_files:
            full_path = self.repo_path / file_path
            if full_path.exists() and full_path.is_file():
                self.index.add_file(file_path)
    
    def commit(self, message: str, allow_empty: bool = False) -> str:
        """
        创建提交
        
        Args:
            message: 提交消息
            allow_empty: 是否允许空提交
            
        Returns:
            提交哈希
        """
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        if not message.strip():
            raise ValueError("提交消息不能为空")
        
        # 构建Tree
        tree = self.merkle_tree.build_tree_from_directory(str(self.repo_path))
        
        # 检查是否有变更
        if not allow_empty and self.head:
            parent_commit = self.odb.get_object(self.head)
            if parent_commit.tree_hash == tree.hash:
                raise ValueError("没有变更需要提交")
        
        # 存储Tree
        self.odb.store_object(tree)
        
        # 创建Commit
        author = f"{self.config['user']['name']} <{self.config['user']['email']}>"
        commit = Commit(
            tree_hash=tree.hash,
            parent_hash=self.head,
            author=author,
            committer=author,
            message=message,
            timestamp=datetime.now()
        )
        
        # 存储Commit
        commit_hash = self.odb.store_object(commit)
        
        # 更新HEAD
        self._save_head(commit_hash)
        
        return commit_hash
    
    def status(self) -> Dict:
        """
        获取仓库状态
        
        Returns:
            状态信息字典
        """
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        staged_files = self.index.get_staged_files()
        modified_files = self.index.get_modified_files()
        untracked_files = self.index.get_untracked_files()
        
        return {
            'branch': self._get_current_branch(),
            'head': self.head,
            'staged_files': staged_files,
            'modified_files': modified_files,
            'untracked_files': untracked_files,
            'is_clean': len(modified_files) == 0 and len(untracked_files) == 0
        }
    
    def _get_current_branch(self) -> str:
        """获取当前分支名"""
        head_file = self.pygit_dir / 'HEAD'
        if head_file.exists():
            try:
                with open(head_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith('ref: '):
                        return content[5:]  # 移除 'ref: ' 前缀
            except IOError:
                pass
        return 'HEAD'
    
    def log(self, max_count: int = 10) -> List[Dict]:
        """
        获取提交历史
        
        Args:
            max_count: 最大返回数量
            
        Returns:
            提交历史列表
        """
        if not self.is_valid_repo or not self.head:
            return []
        
        commits = []
        current_hash = self.head
        
        while current_hash and len(commits) < max_count:
            try:
                commit = self.odb.get_object(current_hash)
                commits.append({
                    'hash': commit.hash,
                    'tree_hash': commit.tree_hash,
                    'parent_hash': commit.parent_hash,
                    'author': commit.author,
                    'message': commit.message,
                    'timestamp': commit.timestamp
                })
                current_hash = commit.parent_hash
            except Exception:
                break
        
        return commits
    
    def diff(self, commit_hash1: Optional[str] = None, commit_hash2: Optional[str] = None) -> Dict:
        """
        比较差异
        
        Args:
            commit_hash1: 第一个提交哈希
            commit_hash2: 第二个提交哈希
            
        Returns:
            差异信息字典
        """
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        # 获取要比较的Tree
        if commit_hash1 and commit_hash2:
            # 比较两个提交
            commit1 = self.odb.get_object(commit_hash1)
            commit2 = self.odb.get_object(commit_hash2)
            tree1 = self.odb.get_object(commit1.tree_hash)
            tree2 = self.odb.get_object(commit2.tree_hash)
        elif commit_hash1:
            # 比较指定提交与工作区
            commit1 = self.odb.get_object(commit_hash1)
            tree1 = self.odb.get_object(commit1.tree_hash)
            tree2 = self.merkle_tree.build_tree_from_directory(str(self.repo_path))
        elif self.head:
            # 比较HEAD与工作区
            commit1 = self.odb.get_object(self.head)
            tree1 = self.odb.get_object(commit1.tree_hash)
            tree2 = self.merkle_tree.build_tree_from_directory(str(self.repo_path))
        else:
            # 没有提交，显示所有文件
            tree1 = Tree()
            tree2 = self.merkle_tree.build_tree_from_directory(str(self.repo_path))
        
        return self.merkle_tree.compare_trees(tree1, tree2)
    
    def tag(self, tag_name: str, commit_hash: Optional[str] = None, message: str = '') -> str:
        """
        创建标签
        
        Args:
            tag_name: 标签名称
            commit_hash: 目标提交哈希
            message: 标签消息
            
        Returns:
            标签哈希
        """
        if not self.is_valid_repo:
            raise ValueError("无效的仓库")
        
        target_hash = commit_hash or self.head
        if not target_hash:
            raise ValueError("没有可标记的提交")
        
        # 创建标签
        author = f"{self.config['user']['name']} <{self.config['user']['email']}>"
        tag = Tag(
            tag_name=tag_name,
            target_hash=target_hash,
            target_type='commit',
            tagger=author,
            message=message,
            timestamp=datetime.now()
        )
        
        # 存储标签
        tag_hash = self.odb.store_object(tag)
        
        # 创建标签引用
        ref_file = self.pygit_dir / 'refs' / 'tags' / tag_name
        ref_file.parent.mkdir(parents=True, exist_ok=True)
        with open(ref_file, 'w', encoding='utf-8') as f:
            f.write(tag_hash)
        
        return tag_hash
    
    def get_stats(self) -> Dict:
        """
        获取仓库统计信息
        
        Returns:
            统计信息字典
        """
        if not self.is_valid_repo:
            return {'is_valid': False}
        
        odb_stats = self.odb.get_stats()
        index_stats = self.index.get_stats()
        
        return {
            'is_valid': True,
            'path': str(self.repo_path),
            'head': self.head,
            'branch': self._get_current_branch(),
            'objects': odb_stats,
            'index': index_stats,
            'total_commits': len(self.log(max_count=1000))
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_valid_repo:
            return f"Repository(path='{self.repo_path}', head='{self.head[:8] if self.head else 'None'}')"
        else:
            return f"Repository(path='{self.repo_path}', invalid)"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"Repository(repo_path='{self.repo_path}', is_valid={self.is_valid_repo})"