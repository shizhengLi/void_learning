"""
初始化命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class InitCommand:
    """初始化仓库命令"""
    
    def __init__(self):
        self.name = 'init'
        self.description = '初始化一个空的PyGit仓库'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            'directory',
            nargs='?',
            default='.',
            help='仓库目录路径（默认为当前目录）'
        )
        parser.add_argument(
            '--bare',
            action='store_true',
            help='创建裸仓库'
        )
        parser.add_argument(
            '--quiet',
            '-q',
            action='store_true',
            help='静默模式'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            # 解析目录路径
            repo_path = os.path.abspath(args.directory)
            
            # 检查目录是否存在
            if not os.path.exists(repo_path):
                if not args.quiet:
                    print(f"创建目录: {repo_path}")
                os.makedirs(repo_path, exist_ok=True)
            
            # 切换到目标目录
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            try:
                # 检查是否已经是仓库
                if Path('.pygit').exists():
                    print(f"错误: '{repo_path}' 已经是一个PyGit仓库")
                    return 1
                
                # 初始化仓库
                repo = Repository(repo_path)
                repo.init(bare=args.bare)
                
                if not args.quiet:
                    if args.bare:
                        print(f"在 '{repo_path}' 初始化空的PyGit裸仓库")
                    else:
                        print(f"在 '{repo_path}' 初始化空的PyGit仓库")
                
                return 0
                
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"初始化仓库失败: {e}")
            return 1