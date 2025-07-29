# PyGit 使用示例

这个目录包含了PyGit版本控制系统的各种使用示例。

## 示例列表

### 1. 基础工作流程 (`basic_workflow.py`)
演示PyGit的基本使用流程：
- 初始化仓库
- 配置用户信息
- 添加文件到暂存区
- 提交更改
- 查看状态和历史
- 创建标签

运行示例：
```bash
python basic_workflow.py
```

### 2. 配置管理 (`config_management.py`)
演示PyGit的配置功能：
- 设置用户配置
- 列出所有配置
- 获取特定配置
- 修改配置

运行示例：
```bash
python config_management.py
```

### 3. 标签管理 (`tag_management.py`)
演示PyGit的标签功能：
- 创建轻量标签
- 创建带注释的标签
- 列出标签
- 标签版本管理

运行示例：
```bash
python tag_management.py
```

### 4. 分支管理 (`branch_management.py`)
演示分支管理的概念：
- 创建分支
- 在不同分支上工作
- 分支合并概念
- 标签和版本控制

运行示例：
```bash
python branch_management.py
```

### 5. Merkle Tree演示 (`merkle_tree_demo.py`)
深入演示Merkle Tree的工作原理：
- 创建文件和目录结构
- 构建Merkle Tree
- 展示树结构
- 演示哈希计算
- 在PyGit中的应用

运行示例：
```bash
python merkle_tree_demo.py
```

## 运行示例

所有示例都是独立的，可以直接运行：

```bash
# 进入examples目录
cd examples

# 运行任何示例
python basic_workflow.py
python config_management.py
python tag_management.py
python branch_management.py
python merkle_tree_demo.py
```

## 示例特点

1. **独立性**：每个示例都是独立的，不需要额外的设置
2. **临时目录**：所有示例都在临时目录中运行，不会影响现有文件
3. **完整演示**：展示了从初始化到完整工作流程的各个方面
4. **详细输出**：提供了详细的操作说明和输出结果
5. **错误处理**：包含了基本的错误处理和状态检查

## 学习建议

建议按以下顺序学习：

1. 先运行 `basic_workflow.py` 了解基本操作
2. 然后运行 `config_management.py` 学习配置管理
3. 接着运行 `tag_management.py` 了解版本标签
4. 运行 `branch_management.py` 理解分支概念
5. 最后运行 `merkle_tree_demo.py` 深入理解底层原理

## 扩展示例

你可以基于这些示例创建更多的使用场景：

- 协作开发模拟
- 大型项目管理
- 复杂的合并操作
- 钩子和自动化
- 自定义工作流程

## 注意事项

- 所有示例都在临时目录中运行，完成后会自动清理
- 示例中的PyGit命令与实际Git命令保持一致
- 某些高级功能（如分支切换）可能需要更多的底层实现支持