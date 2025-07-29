"""
状态命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class StatusCommand:
    """状态命令"""
    
    def __init__(self):
        self.name = 'status'
        self.description = '显示工作树状态'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            '--short',
            '-s',
            action='store_true',
            help='以短格式输出'
        )
        parser.add_argument(
            '--porcelain',
            action='store_true',
            help='以机器可读格式输出'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            repo = Repository()
            if not repo.is_valid_repo:
                print("错误: 不是PyGit仓库")
                return 1
            
            status = repo.status()
            
            if args.porcelain:
                # 机器可读格式
                for file_path in status['staged_files']:
                    print(f"A  {file_path}")
                for file_path in status['modified_files']:
                    print(f" M {file_path}")
                for file_path in status['untracked_files']:
                    print(f"?? {file_path}")
            elif args.short:
                # 短格式
                branch = status['branch']
                if branch.startswith('refs/heads/'):
                    branch = branch[11:]  # 移除 'refs/heads/' 前缀
                
                print(f"## {branch}")
                
                staged_files = status['staged_files']
                modified_files = status['modified_files']
                untracked_files = status['untracked_files']
                
                if staged_files:
                    print("已暂存的文件:")
                    for file_path in staged_files:
                        print(f"  M {file_path}")
                
                if modified_files:
                    print("已修改但未暂存的文件:")
                    for file_path in modified_files:
                        print(f"  M {file_path}")
                
                if untracked_files:
                    print("未跟踪的文件:")
                    for file_path in untracked_files:
                        print(f"  ?? {file_path}")
                
                if status['is_clean']:
                    print("工作目录干净")
            else:
                # 完整格式
                branch = status['branch']
                if branch.startswith('refs/heads/'):
                    branch = branch[11:]  # 移除 'refs/heads/' 前缀
                
                print(f"位于分支 {branch}")
                
                if status['head']:
                    print(f"提交 {status['head'][:8]}")
                else:
                    print("初始提交")
                
                print()
                
                staged_files = status['staged_files']
                modified_files = status['modified_files']
                untracked_files = status['untracked_files']
                
                if staged_files:
                    print("已暂存的文件:")
                    for file_path in staged_files:
                        print(f"  新文件:   {file_path}")
                    print()
                
                if modified_files:
                    print("已修改但未暂存的文件:")
                    for file_path in modified_files:
                        print(f"  已修改:   {file_path}")
                    print()
                
                if untracked_files:
                    print("未跟踪的文件:")
                    for file_path in untracked_files:
                        print(f"  {file_path}")
                    print()
                
                if status['is_clean']:
                    print("没有要提交的文件，工作目录干净")
            
            return 0
            
        except Exception as e:
            print(f"获取状态失败: {e}")
            return 1