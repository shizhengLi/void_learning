"""
配置命令实现
"""

import sys
import os
from typing import List
from pathlib import Path

# 添加路径以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.repository_manager import Repository


class ConfigCommand:
    """配置命令"""
    
    def __init__(self):
        self.name = 'config'
        self.description = '获取和设置仓库或全局选项'
    
    def create_parser(self, subparsers):
        """创建命令解析器"""
        parser = subparsers.add_parser(self.name, help=self.description)
        parser.add_argument(
            'key',
            nargs='?',
            help='配置键'
        )
        parser.add_argument(
            'value',
            nargs='?',
            help='配置值'
        )
        parser.add_argument(
            '--global',
            action='store_true',
            help='全局配置（暂未实现）'
        )
        parser.add_argument(
            '--list',
            '-l',
            action='store_true',
            help='列出所有配置'
        )
        parser.add_argument(
            '--get',
            action='store_true',
            help='获取配置值'
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
                # 列出所有配置
                print("配置:")
                for section, values in repo.config.items():
                    print(f"[{section}]")
                    for key, value in values.items():
                        print(f"  {key} = {value}")
                return 0
            
            elif args.get and args.key:
                # 获取配置值
                keys = args.key.split('.')
                if len(keys) != 2:
                    print(f"错误: 无效的配置键格式: {args.key}")
                    return 1
                
                section, key = keys
                value = repo.config.get(section, {}).get(key, '')
                print(value)
                return 0
            
            elif args.key and args.value:
                # 设置配置值
                keys = args.key.split('.')
                if len(keys) != 2:
                    print(f"错误: 无效的配置键格式: {args.key}")
                    return 1
                
                section, key = keys
                
                if section == 'user':
                    if key == 'name':
                        email = repo.config.get('user', {}).get('email', '')
                        repo.set_user_config(args.value, email)
                        print(f"设置 user.name = {args.value}")
                    elif key == 'email':
                        name = repo.config.get('user', {}).get('name', '')
                        repo.set_user_config(name, args.value)
                        print(f"设置 user.email = {args.value}")
                    else:
                        print(f"错误: 不支持的配置项: {args.key}")
                        return 1
                else:
                    print(f"错误: 不支持的配置节: {section}")
                    return 1
                
                return 0
            
            elif args.key:
                # 显示配置值
                keys = args.key.split('.')
                if len(keys) != 2:
                    print(f"错误: 无效的配置键格式: {args.key}")
                    return 1
                
                section, key = keys
                value = repo.config.get(section, {}).get(key, '')
                if value:
                    print(f"{args.key} {value}")
                return 0
            
            else:
                print("用法: pygit config [--list] [--get] <key> [<value>]")
                return 1
            
        except Exception as e:
            print(f"配置操作失败: {e}")
            return 1