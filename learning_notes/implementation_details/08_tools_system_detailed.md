# 工具系统详解

## 概述

Void的Agent功能的核心是其强大而灵活的工具系统，它允许AI与编辑器、文件系统、终端和其他系统组件进行交互。本文档详细解析Void的工具系统架构，包括工具注册机制、调用流程和实现细节，揭示Agent如何通过各种工具完成复杂任务。

工具系统的主要组成部分包括：

1. 工具定义和类型系统
2. 工具注册机制
3. 工具调用流程
4. 安全审批机制
5. 内置工具集
6. 工具执行环境

## 工具定义与类型系统

Void实现了严格的类型化工具系统，确保每个工具的参数和返回值都有明确的类型定义：

```typescript
// 工具名称类型
export type BuiltinToolName =
  | 'read_file'
  | 'write_file'
  | 'list_directory'
  | 'search_pathnames_only'
  | 'search_for_files'
  | 'search_in_file'
  | 'run_command'
  | 'run_persistent_command'
  | 'open_persistent_terminal'
  | 'kill_persistent_terminal'
  | 'edit_file'
  | 'create_search_replace_blocks';

// 工具参数类型映射
export type BuiltinToolCallParams = {
  'read_file': { uri: URI; start_line?: number; end_line?: number };
  'write_file': { uri: URI; content: string };
  'list_directory': { uri: URI };
  'search_pathnames_only': { query: string; include_pattern: string | null; page_number: number };
  'search_for_files': { query: string; is_regex: boolean; search_in_folder: URI | null; page_number: number };
  'search_in_file': { uri: URI; query: string; is_regex: boolean };
  'run_command': { command: string; cwd: string | null; terminal_id: string };
  'run_persistent_command': { command: string; persistent_terminal_id: string };
  'open_persistent_terminal': { cwd: string | null };
  'kill_persistent_terminal': { persistent_terminal_id: string };
  'edit_file': { uri: URI; search_replace_blocks: string };
  'create_search_replace_blocks': { uri: URI; description: string };
};

// 工具返回值类型映射
export type BuiltinToolResultType = {
  'read_file': { content: string };
  'write_file': { success: boolean };
  'list_directory': { items: ShallowDirectoryItem[] };
  'search_pathnames_only': { uris: URI[]; has_next_page: boolean };
  'search_for_files': { uris: URI[]; has_next_page: boolean };
  'search_in_file': { lines: number[] };
  'run_command': { result: string; resolve_reason: TerminalResolveReason };
  'run_persistent_command': { result: string; resolve_reason: TerminalResolveReason };
  'open_persistent_terminal': { persistent_terminal_id: string };
  'kill_persistent_terminal': { success: boolean };
  'edit_file': { success: boolean };
  'create_search_replace_blocks': { blocks: string };
};
```

工具定义包含名称、描述和参数架构，便于LLM理解如何使用它们：

```typescript
// 工具定义类型
export interface ToolDef {
  name: string;
  description: string;
  parameters: {
    [key: string]: {
      type: string;
      description: string;
      enum?: string[];
    };
  };
}

// 工具定义示例
const readFileTool: ToolDef = {
  name: 'read_file',
  description: 'Read the contents of a file',
  parameters: {
    uri: {
      type: 'string',
      description: 'The URI of the file to read'
    },
    start_line: {
      type: 'number',
      description: 'Optional starting line (1-indexed)'
    },
    end_line: {
      type: 'number',
      description: 'Optional ending line (1-indexed)'
    }
  }
};
```

## 工具注册机制

Void实现了灵活的工具注册机制，使系统能够动态管理可用工具：

```typescript
export interface IToolsService {
  // 调用工具
  callTool<T extends BuiltinToolName>(
    toolName: T,
    params: BuiltinToolCallParams[T]
  ): Promise<BuiltinToolResultType[T]>;
  
  // 注册自定义工具
  registerCustomTool(toolDef: CustomToolDef): void;
  
  // 取消注册工具
  unregisterCustomTool(toolName: string): void;
  
  // 获取工具定义
  getToolDefinitions(): ToolDef[];
  
  // 检查工具是否可用
  isToolAvailable(toolName: string): boolean;
}
```

工具服务实现：

```typescript
export class ToolsService implements IToolsService {
  // 内置工具映射
  private readonly builtinToolMap: {
    [T in BuiltinToolName]: {
      prepareParams: (params: RawToolParamsObj) => BuiltinToolCallParams[T];
      execute: (params: BuiltinToolCallParams[T]) => Promise<BuiltinToolResultType[T]>;
      formatResult?: (params: BuiltinToolCallParams[T], result: BuiltinToolResultType[T]) => string;
    };
  };
  
  // 自定义工具映射
  private readonly customTools: Map<string, CustomTool> = new Map();
  
  constructor(
    @IVoidFileService private readonly voidFileService: IVoidFileService,
    @ITerminalToolService private readonly terminalToolService: ITerminalToolService,
    @ISearchService private readonly searchService: ISearchService,
    @IEditCodeService private readonly editCodeService: IEditCodeService,
    @IApprovalService private readonly approvalService: IApprovalService
  ) {
    // 初始化内置工具映射
    this.builtinToolMap = {
      'read_file': {
        prepareParams: this.prepareReadFileParams,
        execute: this.executeReadFile.bind(this)
      },
      // ...其他工具定义
    };
  }
  
  // 调用工具
  async callTool<T extends BuiltinToolName>(
    toolName: T,
    params: BuiltinToolCallParams[T]
  ): Promise<BuiltinToolResultType[T]> {
    // 检查工具是否存在
    if (!this.builtinToolMap[toolName]) {
      throw new Error(`Tool ${toolName} not found`);
    }
    
    // 执行工具
    const tool = this.builtinToolMap[toolName];
    return tool.execute(params);
  }
  
  // 注册自定义工具
  registerCustomTool(toolDef: CustomToolDef): void {
    if (this.customTools.has(toolDef.name) || this.builtinToolMap[toolDef.name as BuiltinToolName]) {
      throw new Error(`Tool ${toolDef.name} already exists`);
    }
    
    this.customTools.set(toolDef.name, {
      def: toolDef,
      execute: toolDef.execute
    });
  }
  
  // 取消注册工具
  unregisterCustomTool(toolName: string): void {
    this.customTools.delete(toolName);
  }
  
  // 获取所有工具定义
  getToolDefinitions(): ToolDef[] {
    // 获取内置工具定义
    const builtinDefs = Object.keys(this.builtinToolMap).map(name => 
      builtinToolDefs[name as BuiltinToolName]
    );
    
    // 获取自定义工具定义
    const customDefs = Array.from(this.customTools.values()).map(tool => tool.def);
    
    // 合并并返回
    return [...builtinDefs, ...customDefs];
  }
  
  // 检查工具是否可用
  isToolAvailable(toolName: string): boolean {
    return (
      !!this.builtinToolMap[toolName as BuiltinToolName] ||
      this.customTools.has(toolName)
    );
  }
  
  // ...工具实现
}
```

## 工具调用流程

Void实现了完整的工具调用流程，从LLM的工具调用请求到执行结果返回：

```typescript
// 工具调用流程
async function processToolCall(
  toolCall: { name: string; parameters: any },
  context: AgentContext
): Promise<ToolCallResult> {
  try {
    // 1. 解析工具调用
    const { name, parameters } = toolCall;
    
    // 2. 验证工具
    if (!toolsService.isToolAvailable(name)) {
      throw new Error(`Tool ${name} is not available`);
    }
    
    // 3. 验证参数
    const toolDef = builtinToolDefs[name as BuiltinToolName];
    validateToolParameters(parameters, toolDef.parameters);
    
    // 4. 检查是否需要审批
    const approvalType = approvalTypeOfBuiltinToolName[name as BuiltinToolName];
    if (approvalType) {
      const approved = await requestApproval(name, parameters, approvalType);
      if (!approved) {
        return {
          error: `Tool call to ${name} was rejected by the user`
        };
      }
    }
    
    // 5. 准备参数
    const preparedParams = toolsService.builtinToolMap[name as BuiltinToolName].prepareParams(parameters);
    
    // 6. 执行工具
    const result = await toolsService.callTool(name as BuiltinToolName, preparedParams);
    
    // 7. 格式化结果
    const formatFn = toolsService.builtinToolMap[name as BuiltinToolName].formatResult;
    const formattedResult = formatFn ? formatFn(preparedParams, result) : JSON.stringify(result);
    
    // 8. 返回结果
    return {
      result: formattedResult
    };
  } catch (error) {
    // 处理错误
    return {
      error: error.message
    };
  }
}
```

### 工具参数验证

Void实现了严格的工具参数验证，确保传递给工具的参数符合预期：

```typescript
function validateToolParameters(
  params: any,
  paramSchema: ToolDef['parameters']
): void {
  // 检查必需参数
  for (const [paramName, paramDef] of Object.entries(paramSchema)) {
    // 如果参数是必需的但未提供
    if (!paramDef.optional && (params[paramName] === undefined || params[paramName] === null)) {
      throw new Error(`Missing required parameter: ${paramName}`);
    }
    
    // 如果参数已提供，验证类型
    if (params[paramName] !== undefined && params[paramName] !== null) {
      const paramValue = params[paramName];
      
      // 类型检查
      switch (paramDef.type) {
        case 'string':
          if (typeof paramValue !== 'string') {
            throw new Error(`Parameter ${paramName} must be a string`);
          }
          break;
        case 'number':
          if (typeof paramValue !== 'number') {
            throw new Error(`Parameter ${paramName} must be a number`);
          }
          break;
        case 'boolean':
          if (typeof paramValue !== 'boolean') {
            throw new Error(`Parameter ${paramName} must be a boolean`);
          }
          break;
        case 'array':
          if (!Array.isArray(paramValue)) {
            throw new Error(`Parameter ${paramName} must be an array`);
          }
          break;
        case 'object':
          if (typeof paramValue !== 'object' || paramValue === null || Array.isArray(paramValue)) {
            throw new Error(`Parameter ${paramName} must be an object`);
          }
          break;
      }
      
      // 枚举值检查
      if (paramDef.enum && !paramDef.enum.includes(paramValue)) {
        throw new Error(`Parameter ${paramName} must be one of: ${paramDef.enum.join(', ')}`);
      }
    }
  }
}
```

## 工具审批机制

为保证安全，Void实现了工具调用审批机制：

```typescript
// 工具审批类型
export type ToolApprovalType = 'edits' | 'terminal' | 'MCP tools';

// 工具审批配置
export const approvalTypeOfBuiltinToolName: Partial<{ [T in BuiltinToolName]?: ToolApprovalType }> = {
  'write_file': 'edits',
  'edit_file': 'edits',
  'run_command': 'terminal',
  'run_persistent_command': 'terminal',
  'open_persistent_terminal': 'terminal',
  'kill_persistent_terminal': 'terminal',
};

// 工具审批实现
async function requestApproval(
  toolName: string,
  params: any,
  approvalType: ToolApprovalType
): Promise<boolean> {
  // 创建审批项
  const approvalItem: ApprovalItem = {
    id: generateUuid(),
    type: approvalType,
    title: `Tool call: ${toolName}`,
    description: formatToolDescription(toolName, params),
    details: {
      toolName,
      params
    },
    createdAt: Date.now()
  };
  
  // 请求审批
  const result = await approvalService.requestApproval({
    item: approvalItem
  });
  
  return result.approved;
}
```

## 内置工具实现

Void实现了丰富的内置工具集，下面详细介绍几个核心工具的实现：

### 文件读取工具

```typescript
// 读取文件参数准备
prepareReadFileParams(params: RawToolParamsObj): BuiltinToolCallParams['read_file'] {
  const { uri: uriStr, start_line, end_line } = params;
  
  // 验证并解析URI
  const uri = validateUri(uriStr);
  
  // 解析起始行和结束行
  const startLine = start_line !== undefined ? Number(start_line) : undefined;
  const endLine = end_line !== undefined ? Number(end_line) : undefined;
  
  // 验证行号
  if (startLine !== undefined && (isNaN(startLine) || startLine < 1)) {
    throw new Error('Invalid start_line: must be a positive integer');
  }
  
  if (endLine !== undefined && (isNaN(endLine) || endLine < 1)) {
    throw new Error('Invalid end_line: must be a positive integer');
  }
  
  if (startLine !== undefined && endLine !== undefined && startLine > endLine) {
    throw new Error('start_line must be less than or equal to end_line');
  }
  
  return { uri, start_line: startLine, end_line: endLine };
}

// 读取文件执行
async executeReadFile(params: BuiltinToolCallParams['read_file']): Promise<BuiltinToolResultType['read_file']> {
  const { uri, start_line, end_line } = params;
  
  // 读取文件内容
  const content = await this.voidFileService.readFile(uri);
  
  // 如果未指定行范围，返回整个文件
  if (start_line === undefined && end_line === undefined) {
    return { content };
  }
  
  // 提取指定行范围
  const lines = content.split('\n');
  const start = start_line !== undefined ? start_line - 1 : 0;
  const end = end_line !== undefined ? end_line - 1 : lines.length - 1;
  
  // 确保范围有效
  if (start < 0 || end >= lines.length) {
    throw new Error(`Line range out of bounds. File has ${lines.length} lines.`);
  }
  
  // 返回指定行范围的内容
  return {
    content: lines.slice(start, end + 1).join('\n')
  };
}
```

### 终端命令执行工具

```typescript
// 执行命令参数准备
prepareRunCommandParams(params: RawToolParamsObj): BuiltinToolCallParams['run_command'] {
  const { command: commandUnknown, cwd: cwdUnknown, terminal_id: terminalIdUnknown } = params;
  
  // 验证命令
  if (!commandUnknown || typeof commandUnknown !== 'string') {
    throw new Error('Command must be a non-empty string');
  }
  const command = commandUnknown.trim();
  
  // 验证工作目录
  let cwd: string | null = null;
  if (cwdUnknown) {
    if (typeof cwdUnknown !== 'string') {
      throw new Error('CWD must be a string');
    }
    cwd = cwdUnknown;
  }
  
  // 验证终端ID
  const terminalId = terminalIdUnknown ? String(terminalIdUnknown) : generateUuid();
  
  return { command, cwd, terminal_id: terminalId };
}

// 执行命令
async executeRunCommand(params: BuiltinToolCallParams['run_command']): Promise<BuiltinToolResultType['run_command']> {
  const { command, cwd, terminal_id } = params;
  
  // 执行命令
  const { resPromise, interrupt } = await this.terminalToolService.runCommand(
    command, 
    { type: 'temporary', cwd, terminalId: terminal_id }
  );
  
  // 设置超时中断
  const timeoutId = setTimeout(() => interrupt(), MAX_TERMINAL_COMMAND_TIME);
  
  try {
    // 等待命令完成
    const result = await resPromise;
    
    return {
      result: result.result,
      resolve_reason: result.resolveReason
    };
  } finally {
    clearTimeout(timeoutId);
  }
}
```

### 代码编辑工具

```typescript
// 编辑文件参数准备
prepareEditFileParams(params: RawToolParamsObj): BuiltinToolCallParams['edit_file'] {
  const { uri: uriStr, search_replace_blocks } = params;
  
  // 验证URI
  const uri = validateUri(uriStr);
  
  // 验证搜索替换块
  if (!search_replace_blocks || typeof search_replace_blocks !== 'string') {
    throw new Error('search_replace_blocks must be a non-empty string');
  }
  
  return { uri, search_replace_blocks };
}

// 编辑文件执行
async executeEditFile(params: BuiltinToolCallParams['edit_file']): Promise<BuiltinToolResultType['edit_file']> {
  const { uri, search_replace_blocks } = params;
  
  // 应用编辑
  await this.editCodeService.editFile({
    uri,
    searchReplaceBlocks: search_replace_blocks,
    applyMethod: 'fast'
  });
  
  return { success: true };
}
```

### 搜索工具

```typescript
// 搜索文件参数准备
prepareSearchForFilesParams(params: RawToolParamsObj): BuiltinToolCallParams['search_for_files'] {
  const { 
    query, 
    is_regex: isRegexUnknown, 
    search_in_folder: searchInFolderUnknown,
    page_number: pageNumberUnknown 
  } = params;
  
  // 验证查询
  if (!query || typeof query !== 'string') {
    throw new Error('Query must be a non-empty string');
  }
  
  // 验证正则标志
  const isRegex = isRegexUnknown === true || isRegexUnknown === 'true';
  
  // 验证搜索文件夹
  let searchInFolder: URI | null = null;
  if (searchInFolderUnknown) {
    try {
      searchInFolder = validateUri(searchInFolderUnknown);
    } catch (e) {
      throw new Error(`Invalid search_in_folder: ${e.message}`);
    }
  }
  
  // 验证页码
  const pageNumber = pageNumberUnknown !== undefined ? Number(pageNumberUnknown) : 1;
  if (isNaN(pageNumber) || pageNumber < 1) {
    throw new Error('page_number must be a positive integer');
  }
  
  return { 
    query, 
    is_regex: isRegex, 
    search_in_folder: searchInFolder,
    page_number: pageNumber
  };
}

// 搜索文件执行
async executeSearchForFiles(params: BuiltinToolCallParams['search_for_files']): Promise<BuiltinToolResultType['search_for_files']> {
  const { query, is_regex, search_in_folder, page_number } = params;
  
  // 计算偏移量
  const offset = (page_number - 1) * MAX_SEARCH_RESULTS_PER_PAGE;
  
  // 执行搜索
  const results = await this.searchService.searchContent({
    query,
    isRegex: is_regex,
    includePattern: search_in_folder ? `${search_in_folder.fsPath}/**` : undefined,
    maxResults: MAX_SEARCH_RESULTS_PER_PAGE + 1, // 多获取一个结果以检查是否有下一页
    offset
  });
  
  // 检查是否有下一页
  const hasNextPage = results.length > MAX_SEARCH_RESULTS_PER_PAGE;
  if (hasNextPage) {
    results.pop(); // 移除额外的结果
  }
  
  // 提取URI
  const uris = results.map(result => result.uri);
  
  return {
    uris,
    has_next_page: hasNextPage
  };
}
```

## 工具格式化

Void对工具结果进行格式化，使LLM能更好地理解和使用结果：

```typescript
// 格式化终端命令结果
formatRunCommandResult(params: BuiltinToolCallParams['run_command'], result: BuiltinToolResultType['run_command']): string {
  const { result: output, resolve_reason } = result;
  
  // 处理超时情况
  if (resolve_reason.type === 'timeout') {
    return `${output}\n\n[Command timed out after ${MAX_TERMINAL_COMMAND_TIME / 1000} seconds]`;
  }
  
  // 处理完成情况
  return `${output}\n\n[Command completed with exit code: ${resolve_reason.exitCode}]`;
}

// 格式化文件读取结果
formatReadFileResult(params: BuiltinToolCallParams['read_file'], result: BuiltinToolResultType['read_file']): string {
  const { uri, start_line, end_line } = params;
  const { content } = result;
  
  // 构建文件信息
  const fileInfo = `File: ${uri.fsPath}`;
  const lineInfo = start_line !== undefined || end_line !== undefined
    ? `Lines: ${start_line || 1}-${end_line || 'end'}`
    : '';
  
  // 构建头部
  const header = [fileInfo, lineInfo].filter(Boolean).join(' | ');
  
  // 返回格式化结果
  return `${header}\n\n${content}`;
}

// 格式化搜索结果
formatSearchForFilesResult(params: BuiltinToolCallParams['search_for_files'], result: BuiltinToolResultType['search_for_files']): string {
  const { uris, has_next_page } = result;
  
  // 如果没有结果
  if (uris.length === 0) {
    return 'No files found matching the search criteria.';
  }
  
  // 构建结果列表
  const fileList = uris
    .map((uri, index) => `${index + 1}. ${uri.fsPath}`)
    .join('\n');
  
  // 添加分页信息
  const pageInfo = has_next_page
    ? `\n\nThere are more results available. Use page_number: ${params.page_number + 1} to see the next page.`
    : '';
  
  // 返回格式化结果
  return `Found ${uris.length} files matching query "${params.query}":\n\n${fileList}${pageInfo}`;
}
```

## 工具执行环境

Void为工具执行提供了安全的环境，包括错误处理、超时控制和资源限制：

```typescript
// 工具执行包装器
async function safeToolExecution<T>(
  execution: () => Promise<T>,
  toolName: string,
  params: any
): Promise<T> {
  try {
    // 开始执行计时
    const startTime = performance.now();
    
    // 设置超时
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Tool execution timed out after ${MAX_TOOL_EXECUTION_TIME}ms`));
      }, MAX_TOOL_EXECUTION_TIME);
    });
    
    // 竞争执行和超时
    const result = await Promise.race([execution(), timeoutPromise]);
    
    // 记录执行时间
    const executionTime = performance.now() - startTime;
    console.log(`Tool ${toolName} executed in ${executionTime}ms`);
    
    return result;
  } catch (error) {
    // 记录错误
    console.error(`Error executing tool ${toolName}:`, error);
    
    // 重新抛出
    throw new Error(`Failed to execute tool ${toolName}: ${error.message}`);
  }
}
```

### 资源限制

```typescript
// 资源限制常量
const MAX_TOOL_EXECUTION_TIME = 30000; // 30秒
const MAX_TERMINAL_COMMAND_TIME = 60000; // 60秒
const MAX_SEARCH_RESULTS_PER_PAGE = 50; // 每页50个结果
const MAX_FILE_READ_SIZE = 1024 * 1024; // 1MB
const MAX_FILE_WRITE_SIZE = 1024 * 1024; // 1MB
const MAX_CONCURRENT_TOOL_EXECUTIONS = 5; // 最多5个并发执行

// 限制并发工具执行
class ConcurrencyLimiter {
  private currentExecutions = 0;
  private queue: Array<() => void> = [];
  
  async acquire(): Promise<() => void> {
    // 如果未达到并发限制，直接授权
    if (this.currentExecutions < MAX_CONCURRENT_TOOL_EXECUTIONS) {
      this.currentExecutions++;
      return this.createRelease();
    }
    
    // 否则等待
    return new Promise<() => void>(resolve => {
      this.queue.push(() => {
        this.currentExecutions++;
        resolve(this.createRelease());
      });
    });
  }
  
  private createRelease(): () => void {
    return () => {
      this.currentExecutions--;
      
      // 处理队列
      if (this.queue.length > 0) {
        const next = this.queue.shift();
        next();
      }
    };
  }
}
```

## MCP工具扩展

Void实现了Model Context Protocol (MCP) 工具扩展，允许动态扩展工具集：

```typescript
// MCP工具类型
export interface MCPTool {
  name: string;
  description: string;
  parameters: {
    [key: string]: {
      type: string;
      description: string;
      enum?: string[];
    };
  };
  execute: (params: any) => Promise<any>;
}

// MCP工具服务
export interface IMCPService {
  // 注册MCP工具
  registerMCPTool(tool: MCPTool): void;
  
  // 取消注册MCP工具
  unregisterMCPTool(toolName: string): void;
  
  // 调用MCP工具
  callMCPTool(params: { name: string; args: any }): Promise<any>;
  
  // 获取所有MCP工具
  getMCPTools(): MCPTool[];
}

// MCP工具服务实现
export class MCPService implements IMCPService {
  private readonly mcpTools = new Map<string, MCPTool>();
  
  // 注册MCP工具
  registerMCPTool(tool: MCPTool): void {
    if (this.mcpTools.has(tool.name)) {
      throw new Error(`MCP tool ${tool.name} already exists`);
    }
    
    this.mcpTools.set(tool.name, tool);
  }
  
  // 取消注册MCP工具
  unregisterMCPTool(toolName: string): void {
    this.mcpTools.delete(toolName);
  }
  
  // 调用MCP工具
  async callMCPTool(params: { name: string; args: any }): Promise<any> {
    const { name, args } = params;
    
    // 获取工具
    const tool = this.mcpTools.get(name);
    if (!tool) {
      throw new Error(`MCP tool ${name} not found`);
    }
    
    // 执行工具
    return tool.execute(args);
  }
  
  // 获取所有MCP工具
  getMCPTools(): MCPTool[] {
    return Array.from(this.mcpTools.values());
  }
}
```

## 工具用法示例

以下是在Agent系统中使用工具的示例：

```typescript
// 在Agent系统中使用工具
async function performTask(task: string): Promise<void> {
  // 1. 列出项目文件
  const projectFiles = await toolsService.callTool('list_directory', {
    uri: workspaceRootUri
  });
  
  // 2. 搜索相关文件
  const searchResults = await toolsService.callTool('search_for_files', {
    query: 'function calculateTotal',
    is_regex: false,
    search_in_folder: null,
    page_number: 1
  });
  
  // 3. 读取文件内容
  if (searchResults.uris.length > 0) {
    const fileContent = await toolsService.callTool('read_file', {
      uri: searchResults.uris[0]
    });
    
    // 4. 编辑文件
    await toolsService.callTool('edit_file', {
      uri: searchResults.uris[0],
      search_replace_blocks: `<<<<<<< ORIGINAL
function calculateTotal(items) {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price;
  }
  return total;
}
=======
function calculateTotal(items) {
  return items.reduce((total, item) => total + item.price, 0);
}
>>>>>>> UPDATED`
    });
    
    // 5. 运行命令
    await toolsService.callTool('run_command', {
      command: 'npm test',
      cwd: workspaceRootUri.fsPath,
      terminal_id: generateUuid()
    });
  }
}
```

## 工具系统扩展

Void的工具系统支持自定义扩展，使开发者能够添加新工具：

```typescript
// 自定义工具定义
interface CustomToolDef extends ToolDef {
  execute: (params: any) => Promise<any>;
}

// 注册自定义工具
function registerCustomTool(toolDef: CustomToolDef): void {
  toolsService.registerCustomTool(toolDef);
}

// 示例: 注册自定义工具
registerCustomTool({
  name: 'analyze_code_complexity',
  description: 'Analyze the complexity of the given code',
  parameters: {
    uri: {
      type: 'string',
      description: 'The URI of the file to analyze'
    },
    metrics: {
      type: 'array',
      description: 'Metrics to calculate (e.g. "cyclomatic", "cognitive")'
    }
  },
  async execute(params) {
    const { uri, metrics } = params;
    
    // 读取文件
    const fileContent = await voidFileService.readFile(URI.parse(uri));
    
    // 分析复杂度
    const results = {};
    for (const metric of metrics) {
      results[metric] = calculateComplexity(fileContent, metric);
    }
    
    return results;
  }
});
```

## 总结

Void的工具系统是Agent功能的核心支柱，通过精心设计的类型系统、工具注册机制和安全执行环境，使AI能够安全高效地与代码库、文件系统和终端交互。主要特点包括：

1. **严格的类型系统**：确保工具参数和返回值的类型安全
2. **动态工具注册**：支持内置工具和自定义工具的灵活管理
3. **安全审批机制**：保护系统安全，防止未授权操作
4. **丰富的内置工具集**：提供全面的文件、搜索、终端和编辑功能
5. **资源限制和错误处理**：确保工具执行的稳定性和可靠性

这些功能共同确保了Agent能够通过工具系统执行各种复杂任务，从代码分析到修改，从文件操作到命令执行，为开发者提供强大的AI辅助能力。 