#!/usr/bin/env python3
"""
Merkle Tree 工作原理演示

演示Merkle Tree的核心概念和PyGit中的实现：
1. 创建文件和目录结构
2. 构建Merkle Tree
3. 展示树结构
4. 演示哈希计算
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加路径以便导入模块
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用pygit.py中的路径解析方式
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.merkle import MerkleTree
from core.hash import HashCalculator


def merkle_tree_demo():
    """演示Merkle Tree工作原理"""
    print("=== Merkle Tree 工作原理演示 ===\n")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"工作目录: {temp_dir}")
        
        # 1. 创建文件结构
        print("1. 创建文件结构...")
        file_structure = {
            'src': {
                'main.py': 'print("Hello World")',
                'utils.py': 'def helper():\n    return "help"',
                '__init__.py': '# Package init'
            },
            'docs': {
                'README.md': '# Project Docs',
                'guide.md': '# User Guide'
            },
            'config.json': '{"name": "demo", "version": "1.0"}',
            'LICENSE': 'MIT License'
        }
        
        def create_files(base_path, structure):
            for name, content in structure.items():
                if isinstance(content, dict):
                    # 目录
                    dir_path = base_path / name
                    dir_path.mkdir(exist_ok=True)
                    create_files(dir_path, content)
                else:
                    # 文件
                    file_path = base_path / name
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  创建文件: {file_path.relative_to(Path(temp_dir))}")
        
        create_files(Path(temp_dir), file_structure)
        print()
        
        # 2. 演示文件哈希计算
        print("2. 文件哈希计算...")
        hash_calculator = HashCalculator()
        
        def calculate_file_hashes(base_path):
            for file_path in base_path.rglob('*'):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    file_hash = hash_calculator.sha1(content)
                    print(f"  {file_path.relative_to(base_path)}: {file_hash[:8]}...")
        
        calculate_file_hashes(Path(temp_dir))
        print()
        
        # 3. 构建Merkle Tree
        print("3. 构建Merkle Tree...")
        merkle_tree = MerkleTree(temp_dir)
        root_tree = merkle_tree.build_tree_from_directory(temp_dir)
        
        print(f"  根节点哈希: {root_tree.hash[:8]}...")
        print(f"  树节点数量: {count_tree_nodes(root_tree)}")
        print()
        
        # 4. 展示树结构
        print("4. 树结构:")
        print_tree_structure(root_tree, Path(temp_dir), "")
        print()
        
        # 5. 演示Merkle Tree属性
        print("5. Merkle Tree 属性:")
        print(f"  - 根哈希: {root_tree.hash}")
        print(f"  - 节点类型: {type(root_tree).__name__}")
        print(f"  - 条目数量: {len(root_tree.entries) if hasattr(root_tree, 'entries') else 0}")
        
        if hasattr(root_tree, 'entries'):
            print(f"  - 条目:")
            for name, entry in root_tree.entries.items():
                print(f"    {name}: {entry.hash[:8]}...")
        print()
        
        # 6. 演示PyGit仓库中的Merkle Tree
        print("6. PyGit仓库中的Merkle Tree...")
        print("  Merkle Tree是PyGit的核心数据结构")
        print("  每次提交都会创建一个新的Tree对象")
        print("  Tree对象的哈希作为提交的根哈希")
        print("  这确保了数据的完整性和版本追踪")
        print()
        
        print("=== Merkle Tree 演示完成 ===")


def count_tree_nodes(tree):
    """计算树节点数量"""
    if not hasattr(tree, 'entries'):
        return 1
    
    count = 1
    for entry in tree.entries.values():
        count += 1  # Count the entry itself
    return count


def print_tree_structure(tree, base_path, indent):
    """打印树结构"""
    if hasattr(tree, 'entries'):
        # Tree节点
        print(f"{indent}📁 Tree: {tree.hash[:8]}...")
        for name, entry in sorted(tree.entries.items()):
            print(f"{indent}  📄 {entry.name}: {entry.hash[:8]}...")
    else:
        # Blob节点
        print(f"{indent}📄 Blob: {tree.hash[:8]}...")


if __name__ == '__main__':
    merkle_tree_demo()