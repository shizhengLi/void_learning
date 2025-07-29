"""
标签命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class TagCommand:
    """标签命令"""
    
    def __init__(self):
        self.name = 'tag'
        self.description = '创建、列出、删除或验证标签'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            'name',
            nargs='?',
            help='标签名称'
        )
        parser.add_argument(
            'commit',
            nargs='?',
            help='提交哈希'
        )
        parser.add_argument(
            '-a',
            '--annotate',
            action='store_true',
            help='创建带注释的标签'
        )
        parser.add_argument(
            '-m',
            '--message',
            help='标签消息'
        )
        parser.add_argument(
            '-l',
            '--list',
            action='store_true',
            help='列出标签'
        )
        parser.add_argument(
            '-d',
            '--delete',
            help='删除标签'
        )
        return parser
    
    def execute(self, args):
        """执行命令"""
        try:
            repo = Repository()
            if not repo.is_valid_repo:
                print("错误: 不是PyGit仓库")
                return 1
            
            if args.list:
                # 列出标签
                tags_dir = repo.pygit_dir / 'refs' / 'tags'
                if tags_dir.exists():
                    tags = []
                    for tag_file in tags_dir.iterdir():
                        if tag_file.is_file():
                            tags.append(tag_file.name)
                    
                    if tags:
                        for tag in sorted(tags):
                            print(tag)
                    else:
                        print("没有标签")
                else:
                    print("没有标签")
                return 0
            
            elif args.delete:
                # 删除标签
                tag_file = repo.pygit_dir / 'refs' / 'tags' / args.delete
                if tag_file.exists():
                    tag_file.unlink()
                    print(f"删除标签 '{args.delete}'")
                else:
                    print(f"标签 '{args.delete}' 不存在")
                    return 1
                return 0
            
            elif args.name:
                # 创建标签
                if not repo.head:
                    print("错误: 没有提交，无法创建标签")
                    return 1
                
                # 获取目标提交
                target_commit = args.commit or repo.head
                
                # 验证提交是否存在
                try:
                    repo.odb.get_object(target_commit)
                except:
                    print(f"错误: 提交 '{target_commit}' 不存在")
                    return 1
                
                # 创建标签
                message = args.message or ''
                if args.annotate and not message:
                    message = f"Tag {args.name}"
                
                tag_hash = repo.tag(args.name, target_commit, message)
                
                if args.annotate or message:
                    print(f"创建带注释的标签 '{args.name}'")
                else:
                    print(f"创建轻量标签 '{args.name}'")
                
                return 0
            
            else:
                # 没有参数，列出标签
                return self.execute(type('Args', (), {'list': True})())
            
        except Exception as e:
            print(f"标签操作失败: {e}")
            return 1