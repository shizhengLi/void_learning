#!/usr/bin/env python3
"""
标签管理示例

演示PyGit的标签功能：
1. 创建轻量标签
2. 创建带注释的标签
3. 列出标签
4. 删除标签
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pygit import PyGitCLI


def tag_management_demo():
    """演示标签管理"""
    print("=== PyGit 标签管理演示 ===\n")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"工作目录: {temp_dir}")
        
        # 创建CLI实例
        cli = PyGitCLI()
        
        # 1. 初始化仓库并配置
        print("1. 初始化仓库...")
        cli.run(['init'])
        cli.run(['config', 'user.name', 'Demo User'])
        cli.run(['config', 'user.email', 'demo@example.com'])
        print()
        
        # 2. 创建一些提交
        print("2. 创建一些提交...")
        commits = [
            ('README.md', '# Project\nInitial setup', 'Initial commit'),
            ('main.py', 'print("Hello World")', 'Add main.py'),
            ('utils.py', 'def helper():\n    pass', 'Add utils.py'),
        ]
        
        for filename, content, message in commits:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            cli.run(['add', filename])
            cli.run(['commit', '-m', message])
            print(f"  提交: {message}")
        print()
        
        # 3. 查看提交历史
        print("3. 查看提交历史...")
        cli.run(['log'])
        print()
        
        # 4. 创建轻量标签
        print("4. 创建轻量标签...")
        lightweight_tags = ['v0.1', 'v0.2', 'v0.3']
        for tag in lightweight_tags:
            cli.run(['tag', tag])
            print(f"  创建标签: {tag}")
        print()
        
        # 5. 创建带注释的标签
        print("5. 创建带注释的标签...")
        annotated_tags = [
            ('v1.0', 'First stable release'),
            ('v1.1', 'Bug fixes and improvements'),
            ('v2.0', 'Major feature release'),
        ]
        
        for tag, message in annotated_tags:
            cli.run(['tag', '-a', tag, '-m', message])
            print(f"  创建带注释标签: {tag}")
        print()
        
        # 6. 列出所有标签
        print("6. 列出所有标签...")
        cli.run(['tag', '-l'])
        print()
        
        # 7. 再次提交并创建新标签
        print("7. 创建更多提交和标签...")
        with open('feature.py', 'w', encoding='utf-8') as f:
            f.write('def new_feature():\n    return "New feature"')
        cli.run(['add', 'feature.py'])
        cli.run(['commit', '-m', 'Add new feature'])
        
        cli.run(['tag', '-a', 'v2.1', '-m', 'Feature release'])
        print("  创建新提交和标签 v2.1")
        print()
        
        # 8. 查看最终标签列表
        print("8. 最终标签列表...")
        cli.run(['tag', '-l'])
        print()
        
        # 9. 查看最终状态
        print("9. 最终状态...")
        cli.run(['status'])
        print()
        
        print("=== 标签管理演示完成 ===")


if __name__ == '__main__':
    tag_management_demo()