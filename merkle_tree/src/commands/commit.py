"""
提交命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class CommitCommand:
    """提交命令"""
    
    def __init__(self):
        self.name = 'commit'
        self.description = '记录变更到仓库'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            '-m',
            '--message',
            required=True,
            help='提交消息'
        )
        parser.add_argument(
            '--allow-empty',
            action='store_true',
            help='允许空提交'
        )
        parser.add_argument(
            '--amend',
            action='store_true',
            help='修改最后一次提交'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            repo = Repository()
            if not repo.is_valid_repo:
                print("错误: 不是PyGit仓库")
                return 1
            
            # 检查是否有用户配置
            if not repo.config.get('user', {}).get('name'):
                print("错误: 请先设置用户名")
                print("使用: pygit config user.name \"Your Name\"")
                return 1
            
            if not repo.config.get('user', {}).get('email'):
                print("错误: 请先设置用户邮箱")
                print("使用: pygit config user.email \"your@email.com\"")
                return 1
            
            # 处理amend选项
            if args.amend:
                print("错误: amend功能尚未实现")
                return 1
            
            # 创建提交
            commit_hash = repo.commit(args.message, args.allow_empty)
            
            # 显示提交信息
            print(f"提交成功: {commit_hash}")
            
            # 显示简短的提交信息
            commit = repo.odb.get_object(commit_hash)
            print(f"  {commit.hash[:8]} {commit.message}")
            
            return 0
            
        except ValueError as e:
            print(f"提交失败: {e}")
            return 1
        except Exception as e:
            print(f"提交失败: {e}")
            return 1