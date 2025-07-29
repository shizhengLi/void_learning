"""
添加文件命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class AddCommand:
    """添加文件到暂存区命令"""
    
    def __init__(self):
        self.name = 'add'
        self.description = '添加文件内容到暂存区'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            'paths',
            nargs='*',
            help='要添加的文件路径'
        )
        parser.add_argument(
            '--all',
            '-A',
            action='store_true',
            help='添加所有文件'
        )
        parser.add_argument(
            '--force',
            '-f',
            action='store_true',
            help='强制添加被忽略的文件'
        )
        parser.add_argument(
            '--dry-run',
            '-n',
            action='store_true',
            help='显示将要添加的文件，但不实际添加'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            repo = Repository()
            if not repo.is_valid_repo:
                print("错误: 不是PyGit仓库")
                return 1
            
            if args.all:
                # 添加所有文件
                if args.dry_run:
                    print("将要添加的文件:")
                    untracked = repo.index.get_untracked_files()
                    modified = repo.index.get_modified_files()
                    all_files = set(untracked) | set(modified)
                    for file_path in sorted(all_files):
                        print(f"  add '{file_path}'")
                else:
                    repo.add_all()
                    print("添加所有文件到暂存区")
            elif args.paths:
                # 添加指定文件
                if args.dry_run:
                    print("将要添加的文件:")
                    for path in args.paths:
                        if os.path.exists(path):
                            print(f"  add '{path}'")
                        else:
                            print(f"  错误: '{path}' 不存在")
                else:
                    repo.add(args.paths)
                    if len(args.paths) == 1:
                        print(f"添加 '{args.paths[0]}' 到暂存区")
                    else:
                        print(f"添加 {len(args.paths)} 个文件到暂存区")
            else:
                print("错误: 必须指定要添加的文件或使用 --all 选项")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"添加文件失败: {e}")
            return 1