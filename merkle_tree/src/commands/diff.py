"""
差异命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class DiffCommand:
    """差异命令"""
    
    def __init__(self):
        self.name = 'diff'
        self.description = '显示提交、提交和工作树等之间的差异'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            'commit',
            nargs='?',
            help='提交哈希'
        )
        parser.add_argument(
            '--name-only',
            action='store_true',
            help='只显示文件名'
        )
        parser.add_argument(
            '--stat',
            action='store_true',
            help='显示差异统计'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            repo = Repository()
            if not repo.is_valid_repo:
                print("错误: 不是PyGit仓库")
                return 1
            
            # 获取差异
            if args.commit:
                # 与指定提交比较
                diff_result = repo.diff(commit_hash1=args.commit)
            else:
                # 与工作区比较
                diff_result = repo.diff()
            
            if not any(diff_result.values()):
                print("没有差异")
                return 0
            
            if args.name_only:
                # 只显示文件名
                all_files = []
                all_files.extend(diff_result['added'])
                all_files.extend(diff_result['removed'])
                all_files.extend(diff_result['modified'])
                
                for file_path in sorted(all_files):
                    print(file_path)
            
            elif args.stat:
                # 显示统计信息
                added_count = len(diff_result['added'])
                removed_count = len(diff_result['removed'])
                modified_count = len(diff_result['modified'])
                
                total_files = added_count + removed_count + modified_count
                
                print(f" {total_files} 个文件被修改")
                if added_count:
                    print(f" {added_count} 个新增文件")
                if removed_count:
                    print(f" {removed_count} 个删除文件")
                if modified_count:
                    print(f" {modified_count} 个修改文件")
                
                # 显示具体文件
                for file_path in diff_result['added']:
                    print(f"  新增: {file_path}")
                for file_path in diff_result['removed']:
                    print(f"  删除: {file_path}")
                for file_path in diff_result['modified']:
                    print(f"  修改: {file_path}")
            
            else:
                # 完整差异显示
                if diff_result['added']:
                    print("新增文件:")
                    for file_path in diff_result['added']:
                        print(f"  + {file_path}")
                    print()
                
                if diff_result['removed']:
                    print("删除文件:")
                    for file_path in diff_result['removed']:
                        print(f"  - {file_path}")
                    print()
                
                if diff_result['modified']:
                    print("修改文件:")
                    for file_path in diff_result['modified']:
                        print(f"  M {file_path}")
                    print()
            
            return 0
            
        except Exception as e:
            print(f"获取差异失败: {e}")
            return 1