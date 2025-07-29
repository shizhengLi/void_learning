# Python Git管理系统

基于Merkle Tree原理实现的简化版Git管理系统，用于学习和研究Merkle Tree在版本控制中的应用。

## 项目结构

```
merkle_tree/
├── src/
│   ├── objects/          # Git对象类型定义
│   ├── core/             # 核心功能实现
│   ├── commands/         # 命令行接口
│   └── utils/            # 工具函数
├── tests/                # 单元测试
├── docs/                 # 文档
├── examples/             # 示例代码
└── README.md
```

## 功能特性

- ✅ 完整的Merkle Tree实现
- ✅ Git对象模型（Blob、Tree、Commit）
- ✅ 版本控制基本功能
- ✅ 高效的哈希计算
- ✅ 数据完整性验证
- ✅ 历史版本管理
- ✅ 变更检测和比较

## 快速开始

### 安装依赖
```bash
#pip install -r requirements.txt
```

### 初始化仓库
```bash
python -m pygit init
```

### 添加文件
```bash
python -m pygit add filename.txt
```

### 提交更改
```bash
python -m pygit commit -m "Initial commit"
```

### 查看历史
```bash
python -m pygit log
```

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

## 开发状态

🚧 项目开发中，敬请期待！