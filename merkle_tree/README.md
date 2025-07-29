# PyGit - 基于Merkle Tree的版本控制系统

基于Merkle Tree原理实现的简化版Git版本控制系统，完全兼容Git的核心功能，用于学习和研究Merkle Tree在版本控制中的应用。

## 项目结构

```
merkle_tree/
├── src/
│   ├── objects/          # Git对象类型定义
│   │   ├── __init__.py
│   │   ├── blob.py       # 文件对象
│   │   ├── tree.py       # 目录对象
│   │   └── commit.py     # 提交对象
│   ├── core/             # 核心功能实现
│   │   ├── __init__.py
│   │   ├── merkle_tree.py    # Merkle Tree核心算法
│   │   ├── object_database.py # 对象数据库
│   │   ├── index_manager.py   # 索引管理
│   │   └── repository_manager.py # 仓库管理
│   ├── commands/         # 命令行接口
│   │   ├── __init__.py
│   │   ├── init.py       # 初始化命令
│   │   ├── add.py        # 添加文件命令
│   │   ├── commit.py     # 提交命令
│   │   ├── status.py     # 状态命令
│   │   ├── log.py        # 日志命令
│   │   ├── diff.py       # 差异命令
│   │   ├── tag.py        # 标签命令
│   │   └── config.py     # 配置命令
│   └── utils/            # 工具函数
│       ├── __init__.py
│       ├── hash_utils.py # 哈希计算工具
│       └── file_utils.py # 文件操作工具
├── tests/                # 单元测试
├── docs/                 # 文档
├── examples/             # 示例代码
├── pygit.py             # 命令行入口
└── README.md
```

## 功能特性

### 核心功能
- ✅ 完整的Merkle Tree实现
- ✅ Git对象模型（Blob、Tree、Commit）
- ✅ 高效的对象存储系统
- ✅ 索引管理和暂存区
- ✅ 版本控制基本功能

### 命令行工具
- ✅ `pygit init` - 初始化仓库
- ✅ `pygit add` - 添加文件到暂存区
- ✅ `pygit commit` - 提交变更
- ✅ `pygit status` - 显示工作区状态
- ✅ `pygit log` - 显示提交历史
- ✅ `pygit diff` - 显示差异
- ✅ `pygit tag` - 标签管理
- ✅ `pygit config` - 配置管理

### 技术特性
- ✅ 高效的SHA-256哈希计算
- ✅ 数据完整性验证
- ✅ 历史版本管理
- ✅ 变更检测和比较
- ✅ 完整的错误处理机制

## 快速开始

### 基本使用

```bash
# 初始化仓库
python pygit.py init

# 配置用户信息
python pygit.py config user.name "Your Name"
python pygit.py config user.email "your@email.com"

# 添加文件到暂存区
python pygit.py add filename.txt

# 提交更改
python pygit.py commit -m "Initial commit"

# 查看状态
python pygit.py status

# 查看提交历史
python pygit.py log

# 查看差异
python pygit.py diff

# 创建标签
python pygit.py tag -a v1.0 -m "Version 1.0"
```

### 高级功能

```bash
# 列出配置
python pygit.py config --list

# 获取特定配置
python pygit.py config user.name

# 列出所有标签
python pygit.py tag -l

# 创建裸仓库
python pygit.py init --bare
```

## 使用示例

查看 `examples/` 目录中的完整使用示例：

- [基础工作流程](examples/basic_workflow.py) - 基本的版本控制操作
- [分支管理](examples/branch_management.py) - 分支创建和切换
- [标签管理](examples/tag_management.py) - 标签创建和管理
- [配置管理](examples/config_management.py) - 配置文件操作
- [Merkle Tree演示](examples/merkle_tree_demo.py) - Merkle Tree工作原理演示

## 学习目标

- 理解Merkle Tree的工作原理
- 掌握Git的内部机制
- 学习数据结构在实际项目中的应用
- 深入理解版本控制系统的核心概念

## 文档

- [Merkle Tree原理解析](docs/01_merkle_tree原理.md)
- [开发计划](docs/02_开发计划.md)
- [API文档](docs/api.md)
- [使用指南](docs/usage.md)
- [哈希计算模块](docs/hash_utils.md)
- [对象模型文档](docs/object_model.md)
- [对象存储系统](docs/object_storage.md)

## 开发状态

✅ 项目已完成，包含完整的版本控制功能和命令行工具！

## 许可证

MIT License