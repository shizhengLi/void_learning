#!/usr/bin/env python3
"""
基础工作流程示例

演示PyGit的基本使用流程：
1. 初始化仓库
2. 配置用户信息
3. 添加文件
4. 提交更改
5. 查看状态和历史
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pygit import PyGitCLI


def basic_workflow_demo():
    """演示基础工作流程"""
    print("=== PyGit 基础工作流程演示 ===\n")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"工作目录: {temp_dir}")
        
        # 创建CLI实例
        cli = PyGitCLI()
        
        # 1. 初始化仓库
        print("1. 初始化仓库...")
        cli.run(['init'])
        print()
        
        # 2. 配置用户信息
        print("2. 配置用户信息...")
        cli.run(['config', 'user.name', 'Demo User'])
        cli.run(['config', 'user.email', 'demo@example.com'])
        print()
        
        # 3. 创建一些文件
        print("3. 创建文件...")
        files = [
            ('README.md', '# Demo Project\n\nThis is a demo project for PyGit.'),
            ('main.py', 'print("Hello, PyGit!")\n'),
            ('utils.py', 'def helper():\n    return "Helper function"\n')
        ]
        
        for filename, content in files:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  创建文件: {filename}")
        print()
        
        # 4. 添加文件到暂存区
        print("4. 添加文件到暂存区...")
        for filename in ['README.md', 'main.py', 'utils.py']:
            cli.run(['add', filename])
        print()
        
        # 5. 查看状态
        print("5. 查看状态...")
        cli.run(['status'])
        print()
        
        # 6. 提交更改
        print("6. 提交更改...")
        cli.run(['commit', '-m', 'Initial commit'])
        print()
        
        # 7. 修改文件
        print("7. 修改文件...")
        with open('main.py', 'a', encoding='utf-8') as f:
            f.write('\nprint("New line added")\n')
        print("  修改 main.py")
        print()
        
        # 8. 查看差异
        print("8. 查看差异...")
        cli.run(['diff'])
        print()
        
        # 9. 添加修改并提交
        print("9. 提交修改...")
        cli.run(['add', 'main.py'])
        cli.run(['commit', '-m', 'Add new line to main.py'])
        print()
        
        # 10. 查看提交历史
        print("10. 查看提交历史...")
        cli.run(['log'])
        print()
        
        # 11. 创建标签
        print("11. 创建标签...")
        cli.run(['tag', '-a', 'v1.0', '-m', 'Version 1.0'])
        cli.run(['tag', '-l'])
        print()
        
        # 12. 查看最终状态
        print("12. 最终状态...")
        cli.run(['status'])
        print()
        
        print("=== 演示完成 ===")


if __name__ == '__main__':
    basic_workflow_demo()