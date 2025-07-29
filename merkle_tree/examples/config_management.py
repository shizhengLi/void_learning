#!/usr/bin/env python3
"""
配置管理示例

演示PyGit的配置功能：
1. 设置用户配置
2. 列出所有配置
3. 获取特定配置
4. 修改配置
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pygit import PyGitCLI


def config_management_demo():
    """演示配置管理"""
    print("=== PyGit 配置管理演示 ===\n")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        print(f"工作目录: {temp_dir}")
        
        # 创建CLI实例
        cli = PyGitCLI()
        
        # 1. 初始化仓库
        print("1. 初始化仓库...")
        cli.run(['init'])
        print()
        
        # 2. 查看初始配置
        print("2. 查看初始配置...")
        cli.run(['config', '--list'])
        print()
        
        # 3. 设置用户配置
        print("3. 设置用户配置...")
        configs = [
            ('user.name', 'John Doe'),
            ('user.email', 'john.doe@example.com'),
        ]
        
        for key, value in configs:
            cli.run(['config', key, value])
            print(f"  设置 {key} = {value}")
        print()
        
        # 4. 查看配置
        print("4. 查看所有配置...")
        cli.run(['config', '--list'])
        print()
        
        # 5. 获取特定配置
        print("5. 获取特定配置...")
        for key in ['user.name', 'user.email']:
            cli.run(['config', key])
        print()
        
        # 6. 修改配置
        print("6. 修改配置...")
        cli.run(['config', 'user.name', 'Jane Doe'])
        print("  修改 user.name = Jane Doe")
        print()
        
        # 7. 验证修改
        print("7. 验证修改...")
        cli.run(['config', 'user.name'])
        print()
        
        # 8. 使用 --get 选项
        print("8. 使用 --get 选项...")
        cli.run(['config', '--get', 'user.name'])
        cli.run(['config', '--get', 'user.email'])
        print()
        
        # 9. 尝试获取不存在的配置
        print("9. 获取不存在的配置...")
        cli.run(['config', 'user.invalid'])
        print()
        
        # 10. 最终配置状态
        print("10. 最终配置状态...")
        cli.run(['config', '--list'])
        print()
        
        print("=== 配置管理演示完成 ===")


if __name__ == '__main__':
    config_management_demo()