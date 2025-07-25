# Void 学习笔记

*[English](README.md) | 中文*

本仓库包含我对 [Void Editor](https://voideditor.com) 项目的学习笔记和研究材料，重点关注AI代理实现和架构。

## 仓库结构

- **void/** - 原始 [Void Editor](https://github.com/voideditor/void) 仓库的Git子模块
- **learning_notes/** - 我个人关于Void的AI代理系统的笔记和学习材料
- **code_agent_implementation/** - 基于LangChain实现的AI代码编辑器代理，受Void架构启发的完整实现

## 目的

本仓库作为我学习Void编辑器AI代理实现的个人学习日志。项目包含理论分析和实际实现两个部分：

### 学习与分析
- 系统架构研究
- 代理核心实现研究
- 代码理解机制
- 终端集成分析
- 编辑和变更应用系统
- 性能优化策略
- 工具系统实现

### 实际实现
`code_agent_implementation/` 目录包含一个使用LangChain构建的功能完整的AI代码编辑器代理，具备以下特性：
- 文件系统工具（搜索、读取、编辑、写入）
- 终端工具（命令执行、持久终端）
- 上下文管理和对话历史
- 带审批系统的安全特性
- 多种操作模式（标准、详细、安全）
- 演示模式用于展示功能

## 原始项目

原始Void Editor项目作为子模块包含在内。所有原始代码属于Void Editor团队，并受其许可条款约束。

## 联系方式

如有关于这些学习材料的任何问题，请联系我：[shizhengcs@gmail.com] 