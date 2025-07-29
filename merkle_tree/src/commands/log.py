"""
日志命令实现
"""

import sys
import os
from typing import List
from pathlib import Path
from datetime import datetime

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class LogCommand:
    """日志命令"""
    
    def __init__(self):
        self.name = 'log'
        self.description = '显示提交日志'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            '-n',
            '--max-count',
            type=int,
            default=10,
            help='显示的最大提交数量'
        )
        parser.add_argument(
            '--oneline',
            action='store_true',
            help='每个提交显示一行'
        )
        parser.add_argument(
            '--graph',
            action='store_true',
            help='显示提交图形'
        )
        parser.add_argument(
            '--pretty',
            choices=['oneline', 'short', 'medium', 'full', 'format'],
            default='medium',
            help='自定义提交格式'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            repo = Repository()
            if not repo.is_valid_repo:
                print("错误: 不是PyGit仓库")
                return 1
            
            if not repo.head:
                print("没有提交历史")
                return 0
            
            commits = repo.log(args.max_count)
            
            if not commits:
                print("没有提交历史")
                return 0
            
            if args.oneline or args.pretty == 'oneline':
                # 单行格式
                for commit in commits:
                    print(f"{commit['hash'][:8]} {commit['message']}")
            elif args.graph:
                # 图形格式（简化版本）
                for i, commit in enumerate(commits):
                    if i == 0:
                        print("*" + "-" * 60)
                    else:
                        print("|" + "-" * 60)
                    print(f"| 提交 {commit['hash'][:8]}")
                    print(f"| 作者: {commit['author']}")
                    print(f"| 时间: {commit['timestamp']}")
                    print(f"| 消息: {commit['message']}")
                    if i < len(commits) - 1:
                        print("*" + "-" * 60)
            else:
                # 默认格式
                for commit in commits:
                    print(f"提交 {commit['hash']}")
                    print(f"作者: {commit['author']}")
                    print(f"时间: {commit['timestamp']}")
                    print()
                    print(f"    {commit['message']}")
                    print()
                    
                    if commit['parent_hash']:
                        print(f"父提交: {commit['parent_hash'][:8]}")
                    print()
            
            return 0
            
        except Exception as e:
            print(f"获取日志失败: {e}")
            return 1