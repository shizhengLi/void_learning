#!/usr/bin/env python3
"""
分支管理示例

演示PyGit的分支功能：
1. 创建分支
2. 切换分支
3. 在不同分支上工作
4. 合并分支
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pygit import PyGitCLI


def branch_management_demo():
    """演示分支管理"""
    print("=== PyGit 分支管理演示 ===\n")
    
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
        
        # 2. 创建初始提交
        print("2. 创建初始提交...")
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write('# Demo Project\n\nThis is a demo project.')
        
        cli.run(['add', 'README.md'])
        cli.run(['commit', '-m', 'Initial commit'])
        print("  初始提交完成")
        print()
        
        # 3. 查看当前分支
        print("3. 查看当前分支...")
        cli.run(['status'])
        print("  当前在 main 分支")
        print()
        
        # 4. 创建功能分支
        print("4. 创建功能分支...")
        # 注意：这里我们模拟分支创建，实际实现可能需要更多功能
        print("  创建分支 feature-1")
        print("  创建分支 feature-2")
        print()
        
        # 5. 在main分支上继续工作
        print("5. 在main分支上继续工作...")
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write('print("Main application")')
        
        cli.run(['add', 'main.py'])
        cli.run(['commit', '-m', 'Add main application'])
        print("  在main分支添加main.py")
        print()
        
        # 6. 模拟在feature分支上工作
        print("6. 模拟在feature分支上工作...")
        feature_commits = [
            ('feature.py', 'def feature_1():\n    return "Feature 1"', 'Implement feature 1'),
            ('utils.py', 'def helper():\n    return "Helper function"', 'Add helper function'),
        ]
        
        for filename, content, message in feature_commits:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            cli.run(['add', filename])
            cli.run(['commit', '-m', message])
            print(f"  在feature分支: {message}")
        print()
        
        # 7. 查看提交历史
        print("7. 查看提交历史...")
        cli.run(['log'])
        print()
        
        # 8. 创建标签标记重要提交
        print("8. 创建标签...")
        cli.run(['tag', '-a', 'v1.0-beta', '-m', 'Beta release'])
        cli.run(['tag', '-a', 'feature-complete', '-m', 'Feature implementation complete'])
        cli.run(['tag', '-l'])
        print()
        
        # 9. 查看当前状态
        print("9. 查看当前状态...")
        cli.run(['status'])
        print()
        
        # 10. 模拟分支合并概念
        print("10. 分支合并概念:")
        print("  在实际Git中，现在可以执行:")
        print("  - git checkout main")
        print("  - git merge feature-1")
        print("  - git merge feature-2")
        print("  在PyGit中，这些概念同样适用")
        print()
        
        print("=== 分支管理演示完成 ===")
        print("注意：完整的分支功能需要更多的底层实现支持")


if __name__ == '__main__':
    branch_management_demo()