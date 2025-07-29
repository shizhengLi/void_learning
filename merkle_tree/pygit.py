#!/usr/bin/env python3
"""
PyGit 命令行工具

基于Merkle Tree原理实现的简化版Git版本控制系统
"""

import sys
import os
import argparse
from pathlib import Path

# 添加路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.commands import (
    InitCommand,
    AddCommand,
    CommitCommand,
    StatusCommand,
    LogCommand,
    DiffCommand,
    TagCommand,
    ConfigCommand
)
from src.core.repository_manager import Repository


class PyGitCLI:
    """PyGit命令行接口"""
    
    def __init__(self):
        self.commands = {
            'init': InitCommand(),
            'add': AddCommand(),
            'commit': CommitCommand(),
            'status': StatusCommand(),
            'log': LogCommand(),
            'diff': DiffCommand(),
            'tag': TagCommand(),
            'config': ConfigCommand()
        }
        
        self.parser = self.create_parser()
    
    def create_parser(self):
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(
            prog='pygit',
            description='基于Merkle Tree的版本控制系统'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='PyGit 0.1.0'
        )
        
        # 创建子命令
        subparsers = parser.add_subparsers(
            dest='command',
            help='可用命令',
            metavar='COMMAND'
        )
        
        # 注册所有命令
        for command in self.commands.values():
            command.create_parser(subparsers)
        
        return parser
    
        
    def run(self, args=None):
        """运行命令行工具"""
        if args is None:
            args = sys.argv[1:]
        
        # 如果没有参数，显示帮助
        if not args:
            self.parser.print_help()
            return 1
        
        # 解析命令
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        # 执行命令
        command = self.commands.get(parsed_args.command)
        if command:
            return command.execute(parsed_args)
        else:
            print(f"未知命令: {parsed_args.command}")
            return 1


def main():
    """主函数"""
    cli = PyGitCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()