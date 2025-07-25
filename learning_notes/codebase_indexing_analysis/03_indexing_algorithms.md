# 索引算法与数据结构

## 核心算法深度解析

Void 的索引系统建立在几个关键算法之上，这些算法在保证性能的同时实现了智能化的代码库遍历和表示。

### 主要算法组件

```mermaid
graph TD
    A[Void 索引算法体系] --> B[目录遍历算法]
    A --> C[过滤算法]
    A --> D[排序算法]
    A --> E[截断算法]
    A --> F[文本渲染算法]
    
    B --> B1[递归深度优先遍历]
    B --> B2[自适应深度控制]
    B --> B3[异步并发处理]
    
    C --> C1[规则式过滤]
    C --> C2[正则表达式匹配]
    C --> C3[路径模式识别]
    
    D --> D1[优先级排序]
    D --> D2[字典序排序]
    D --> D3[大小排序]
    
    E --> E1[字符数截断]
    E --> E2[文件数截断]
    E --> E3[深度截断]
    
    F --> F1[树形结构生成]
    F --> F2[Unicode 字符处理]
    F --> F3[格式化输出]
```

## 1. 目录遍历算法

### 核心遍历策略

Void 使用的是**修改后的深度优先搜索（DFS）**，带有智能剪枝和自适应控制：

```typescript
// 核心遍历算法伪代码
function traverseDirectoryTree(
  node: DirectoryNode, 
  options: TraversalOptions,
  context: TraversalContext
): TraversalResult {
  
  // 1. 边界条件检查
  if (exceedsLimits(node, options, context)) {
    return createTruncatedResult(node, context);
  }
  
  // 2. 过滤检查
  if (shouldSkip(node, options)) {
    return createSkippedResult();
  }
  
  // 3. 递归遍历子节点
  const children = [];
  for (const child of node.children) {
    const childResult = traverseDirectoryTree(child, options, updateContext(context));
    children.push(childResult);
    
    // 4. 早期截断检查
    if (shouldEarlyTerminate(context)) {
      break;
    }
  }
  
  return createNodeResult(node, children, context);
}
```

### 算法复杂度分析

#### 时间复杂度
```typescript
// 最坏情况分析
interface ComplexityAnalysis {
  bestCase: "O(1)";           // 空目录或立即截断
  averageCase: "O(n * log d)"; // n=文件数, d=平均深度
  worstCase: "O(n * d)";      // 深层嵌套的完整遍历
  
  // 实际优化后的复杂度
  voidOptimized: "O(min(n, maxFiles) * min(d, maxDepth))";
}
```

#### 空间复杂度
```typescript
interface SpaceComplexity {
  // 递归调用栈深度
  stackSpace: "O(maxDepth)";
  
  // 结果存储空间
  resultSpace: "O(min(n, maxFiles))";
  
  // 总空间复杂度
  totalSpace: "O(maxDepth + min(n, maxFiles))";
}
```

### 自适应深度控制算法

```typescript
class AdaptiveDepthController {
  private static readonly DEPTH_STRATEGIES = {
    OPTIMISTIC: { maxDepth: Infinity, maxItemsPerDir: Infinity },
    CONSERVATIVE: { maxDepth: 3, maxItemsPerDir: 3 },
    BALANCED: { maxDepth: 5, maxItemsPerDir: 10 }
  };
  
  async determineOptimalStrategy(rootPath: string): Promise<TraversalStrategy> {
    // 第一阶段：快速预扫描评估项目规模
    const projectMetrics = await this.quickAssessment(rootPath);
    
    if (projectMetrics.estimatedFileCount < 1000) {
      return this.DEPTH_STRATEGIES.OPTIMISTIC;
    } else if (projectMetrics.estimatedFileCount > 10000) {
      return this.DEPTH_STRATEGIES.CONSERVATIVE;
    } else {
      return this.DEPTH_STRATEGIES.BALANCED;
    }
  }
  
  private async quickAssessment(rootPath: string): Promise<ProjectMetrics> {
    // 只扫描前两层来估算项目规模
    const topLevelItems = await scanDirectory(rootPath, { maxDepth: 2 });
    
    return {
      estimatedFileCount: this.extrapolateFileCount(topLevelItems),
      complexity: this.calculateComplexity(topLevelItems),
      hasLargeDirectories: this.detectLargeDirectories(topLevelItems)
    };
  }
}
```

## 2. 智能过滤算法

### 多层过滤架构

```typescript
class MultiLayerFilter {
  private readonly filterLayers = [
    new HardcodedFilter(),      // 硬编码规则
    new PatternFilter(),        // 正则模式
    new SizeFilter(),          // 文件大小过滤
    new ExtensionFilter(),     // 文件扩展名过滤
    new ContextualFilter()     // 上下文相关过滤
  ];
  
  shouldExclude(item: FileSystemItem, context: FilterContext): boolean {
    return this.filterLayers.some(filter => filter.shouldExclude(item, context));
  }
}
```

### 硬编码过滤规则分析

```typescript
class HardcodedFilter implements Filter {
  // 按技术栈分类的过滤规则
  private readonly EXCLUSION_RULES = {
    // JavaScript/Node.js 生态
    javascript: [
      'node_modules',    // 依赖包目录
      'dist',           // 构建输出
      'build',          // 构建目录
      '.next',          // Next.js 构建
      '.nuxt',          // Nuxt.js 构建
      'coverage'        // 测试覆盖率
    ],
    
    // Python 生态
    python: [
      '__pycache__',    // Python 字节码
      'venv',           // 虚拟环境
      'env',            // 环境目录
      '.pytest_cache',  // pytest 缓存
      'site-packages'   // 包安装目录
    ],
    
    // Java/JVM 生态
    jvm: [
      'target',         // Maven 构建目录
      'build',          // Gradle 构建目录
      'bin',            // 编译输出
      '.gradle',        // Gradle 缓存
      '.mvn'            // Maven 包装器
    ],
    
    // .NET 生态
    dotnet: [
      'bin',            // 二进制输出
      'obj',            // 对象文件
      'packages',       // NuGet 包
      '.vs'             // Visual Studio 目录
    ],
    
    // 通用规则
    universal: [
      '.git',           // Git 仓库数据
      '.svn',           // SVN 数据
      'tmp',            // 临时文件
      'temp',           // 临时目录
      'cache',          // 缓存目录
      'logs',           // 日志文件
      '.DS_Store'       // macOS 系统文件
    ]
  };
  
  shouldExclude(item: FileSystemItem): boolean {
    const name = item.name.toLowerCase();
    
    // 检查所有规则集
    return Object.values(this.EXCLUSION_RULES)
      .flat()
      .some(rule => this.matchesRule(name, rule));
  }
  
  private matchesRule(name: string, rule: string): boolean {
    // 支持多种匹配模式
    if (rule.includes('*')) {
      return this.globMatch(name, rule);
    } else if (rule.startsWith('/') && rule.endsWith('/')) {
      return new RegExp(rule.slice(1, -1)).test(name);
    } else {
      return name === rule || name.includes(rule);
    }
  }
}
```

### 动态过滤优化

```typescript
class DynamicFilterOptimizer {
  private filterStats = new Map<string, FilterStatistics>();
  
  async optimizeFilters(projectPath: string): Promise<OptimizedFilterSet> {
    // 1. 分析项目特征
    const projectType = await this.detectProjectType(projectPath);
    
    // 2. 基于项目类型选择最优过滤规则
    const baseFilters = this.getBaseFiltersForType(projectType);
    
    // 3. 基于历史数据优化
    const optimizedFilters = this.optimizeBasedOnHistory(baseFilters);
    
    return optimizedFilters;
  }
  
  private async detectProjectType(projectPath: string): Promise<ProjectType> {
    const indicators = await Promise.all([
      this.checkForFile(projectPath, 'package.json'),     // Node.js
      this.checkForFile(projectPath, 'requirements.txt'), // Python
      this.checkForFile(projectPath, 'pom.xml'),         // Maven
      this.checkForFile(projectPath, 'build.gradle'),    // Gradle
      this.checkForFile(projectPath, '*.csproj')         // .NET
    ]);
    
    return this.analyzeIndicators(indicators);
  }
}
```

## 3. 优先级排序算法

### 多维度排序策略

```typescript
class PriorityBasedSorting {
  private readonly PRIORITY_WEIGHTS = {
    fileType: 0.4,      // 文件类型权重
    location: 0.3,      // 位置权重（根目录优先）
    size: 0.2,          // 文件大小权重
    naming: 0.1         // 命名规范权重
  };
  
  sortEntries(entries: FileSystemEntry[]): FileSystemEntry[] {
    return entries.sort((a, b) => {
      const scoreA = this.calculatePriorityScore(a);
      const scoreB = this.calculatePriorityScore(b);
      
      if (Math.abs(scoreA - scoreB) < 0.01) {
        // 分数相近时，使用字典序
        return a.name.localeCompare(b.name);
      }
      
      return scoreB - scoreA; // 高分优先
    });
  }
  
  private calculatePriorityScore(entry: FileSystemEntry): number {
    let score = 0;
    
    // 文件类型评分
    score += this.getFileTypeScore(entry) * this.PRIORITY_WEIGHTS.fileType;
    
    // 位置评分
    score += this.getLocationScore(entry) * this.PRIORITY_WEIGHTS.location;
    
    // 大小评分（小文件优先，便于快速处理）
    score += this.getSizeScore(entry) * this.PRIORITY_WEIGHTS.size;
    
    // 命名规范评分
    score += this.getNamingScore(entry) * this.PRIORITY_WEIGHTS.naming;
    
    return score;
  }
  
  private getFileTypeScore(entry: FileSystemEntry): number {
    const HIGH_PRIORITY_FILES = {
      'package.json': 1.0,
      'README.md': 0.9,
      'tsconfig.json': 0.8,
      '.gitignore': 0.7,
      'Dockerfile': 0.6
    };
    
    const HIGH_PRIORITY_EXTENSIONS = {
      '.config.js': 0.8,
      '.config.ts': 0.8,
      '.env': 0.7,
      '.md': 0.6
    };
    
    // 检查特定文件名
    if (entry.name in HIGH_PRIORITY_FILES) {
      return HIGH_PRIORITY_FILES[entry.name];
    }
    
    // 检查文件扩展名
    for (const [ext, score] of Object.entries(HIGH_PRIORITY_EXTENSIONS)) {
      if (entry.name.endsWith(ext)) {
        return score;
      }
    }
    
    return 0.1; // 默认低优先级
  }
}
```

## 4. 截断算法

### 智能截断策略

```typescript
class IntelligentTruncation {
  async truncateWithContext(
    content: string,
    maxLength: number,
    context: TruncationContext
  ): Promise<TruncationResult> {
    
    if (content.length <= maxLength) {
      return { content, wasTruncated: false };
    }
    
    // 1. 尝试在自然边界截断
    const naturalBoundary = this.findNaturalTruncationPoint(content, maxLength);
    if (naturalBoundary > maxLength * 0.8) {
      return {
        content: content.substring(0, naturalBoundary) + this.getTruncationSuffix(),
        wasTruncated: true
      };
    }
    
    // 2. 保留重要内容的智能截断
    const importantSections = this.identifyImportantSections(content, context);
    const optimizedContent = this.createOptimizedContent(importantSections, maxLength);
    
    return {
      content: optimizedContent + this.getTruncationSuffix(),
      wasTruncated: true
    };
  }
  
  private findNaturalTruncationPoint(content: string, maxLength: number): number {
    const searchStart = Math.max(0, maxLength - 100);
    const searchEnd = Math.min(content.length, maxLength + 50);
    const searchText = content.substring(searchStart, searchEnd);
    
    // 查找自然边界（按优先级）
    const boundaries = [
      '\n\n',           // 段落边界
      '\n',             // 行边界
      '. ',             // 句子边界
      ', ',             // 从句边界
      ' '               // 单词边界
    ];
    
    for (const boundary of boundaries) {
      const lastIndex = searchText.lastIndexOf(boundary);
      if (lastIndex > 0) {
        return searchStart + lastIndex + boundary.length;
      }
    }
    
    return maxLength;
  }
  
  private identifyImportantSections(content: string, context: TruncationContext): ImportantSection[] {
    const sections: ImportantSection[] = [];
    const lines = content.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const importance = this.calculateLineImportance(line, i, context);
      
      if (importance > 0.5) {
        sections.push({
          content: line,
          importance,
          lineNumber: i
        });
      }
    }
    
    return sections.sort((a, b) => b.importance - a.importance);
  }
  
  private calculateLineImportance(line: string, lineNumber: number, context: TruncationContext): number {
    let importance = 0;
    
    // 目录结构中的重要性指标
    if (line.includes('├──') || line.includes('└──')) {
      // 根据缩进层级计算重要性（层级越浅越重要）
      const indentLevel = (line.match(/[│ ]/g) || []).length / 4;
      importance += Math.max(0.1, 1.0 - indentLevel * 0.2);
    }
    
    // 配置文件更重要
    if (line.includes('.json') || line.includes('.config.') || line.includes('README')) {
      importance += 0.3;
    }
    
    // 源代码文件
    if (line.includes('.ts') || line.includes('.js') || line.includes('.py')) {
      importance += 0.2;
    }
    
    return Math.min(1.0, importance);
  }
}
```

## 5. 文本渲染算法

### 树形结构渲染

```typescript
class TreeRenderer {
  private readonly TREE_SYMBOLS = {
    branch: '├── ',
    lastBranch: '└── ',
    vertical: '│   ',
    space: '    '
  };
  
  renderTree(node: DirectoryNode, options: RenderOptions): string {
    return this.renderNode(node, '', true, options);
  }
  
  private renderNode(
    node: DirectoryNode,
    prefix: string,
    isLast: boolean,
    options: RenderOptions
  ): string {
    let result = '';
    
    // 渲染当前节点
    if (node.depth > 0) {
      const symbol = isLast ? this.TREE_SYMBOLS.lastBranch : this.TREE_SYMBOLS.branch;
      const nodeDisplay = this.formatNodeDisplay(node, options);
      result += `${prefix}${symbol}${nodeDisplay}\n`;
    }
    
    // 渲染子节点
    if (node.children && node.children.length > 0) {
      const nextPrefix = prefix + (isLast ? this.TREE_SYMBOLS.space : this.TREE_SYMBOLS.vertical);
      
      for (let i = 0; i < node.children.length; i++) {
        const child = node.children[i];
        const isLastChild = i === node.children.length - 1;
        
        result += this.renderNode(child, nextPrefix, isLastChild, options);
      }
    }
    
    return result;
  }
  
  private formatNodeDisplay(node: DirectoryNode, options: RenderOptions): string {
    let display = node.name;
    
    // 添加类型指示器
    if (node.isDirectory) {
      display += '/';
    }
    
    if (node.isSymbolicLink) {
      display += ' (symbolic link)';
    }
    
    // 添加大小信息（如果需要）
    if (options.showSize && node.size !== undefined) {
      display += ` (${this.formatFileSize(node.size)})`;
    }
    
    // 添加截断指示器
    if (node.truncated) {
      display += ' (truncated...)';
    }
    
    return display;
  }
  
  private formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)}${units[unitIndex]}`;
  }
}
```

### Unicode 和字符编码处理

```typescript
class UnicodeAwareRenderer {
  private readonly SAFE_TREE_SYMBOLS = {
    // 基础 ASCII 版本（兼容性最好）
    ascii: {
      branch: '|-- ',
      lastBranch: '`-- ',
      vertical: '|   ',
      space: '    '
    },
    
    // Unicode 版本（更美观）
    unicode: {
      branch: '├── ',
      lastBranch: '└── ',
      vertical: '│   ',
      space: '    '
    }
  };
  
  selectAppropriateSymbols(context: RenderContext): TreeSymbols {
    // 检测终端/显示环境的 Unicode 支持
    if (context.supportsUnicode && context.encoding === 'utf-8') {
      return this.SAFE_TREE_SYMBOLS.unicode;
    } else {
      return this.SAFE_TREE_SYMBOLS.ascii;
    }
  }
  
  sanitizeText(text: string): string {
    // 移除或替换可能导致显示问题的字符
    return text
      .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '') // 控制字符
      .replace(/[\uFEFF]/g, '')                           // BOM
      .normalize('NFC');                                  // Unicode 规范化
  }
}
```

## 6. 性能优化算法

### 缓存算法

```typescript
class LRUCacheWithTTL<K, V> {
  private cache = new Map<K, CacheEntry<V>>();
  private accessOrder: K[] = [];
  
  constructor(
    private maxSize: number,
    private ttlMs: number
  ) {}
  
  get(key: K): V | undefined {
    const entry = this.cache.get(key);
    
    if (!entry) return undefined;
    
    // 检查 TTL
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.delete(key);
      return undefined;
    }
    
    // 更新访问顺序
    this.updateAccessOrder(key);
    
    return entry.value;
  }
  
  set(key: K, value: V): void {
    // 如果已存在，更新值
    if (this.cache.has(key)) {
      this.cache.set(key, {
        value,
        timestamp: Date.now()
      });
      this.updateAccessOrder(key);
      return;
    }
    
    // 检查容量限制
    if (this.cache.size >= this.maxSize) {
      this.evictLeastRecentlyUsed();
    }
    
    // 添加新条目
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
    this.accessOrder.push(key);
  }
  
  private evictLeastRecentlyUsed(): void {
    if (this.accessOrder.length === 0) return;
    
    const lruKey = this.accessOrder.shift()!;
    this.cache.delete(lruKey);
  }
  
  private updateAccessOrder(key: K): void {
    const index = this.accessOrder.indexOf(key);
    if (index > -1) {
      this.accessOrder.splice(index, 1);
    }
    this.accessOrder.push(key);
  }
}
```

### 并发控制算法

```typescript
class ConcurrencyController {
  private activeTasks = new Set<Promise<any>>();
  private pendingTasks: Array<() => Promise<any>> = [];
  
  constructor(private maxConcurrency: number) {}
  
  async execute<T>(task: () => Promise<T>): Promise<T> {
    // 如果当前并发数未达到限制，直接执行
    if (this.activeTasks.size < this.maxConcurrency) {
      return this.executeTask(task);
    }
    
    // 否则加入等待队列
    return new Promise((resolve, reject) => {
      this.pendingTasks.push(async () => {
        try {
          const result = await this.executeTask(task);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
    });
  }
  
  private async executeTask<T>(task: () => Promise<T>): Promise<T> {
    const taskPromise = task();
    this.activeTasks.add(taskPromise);
    
    try {
      const result = await taskPromise;
      return result;
    } finally {
      this.activeTasks.delete(taskPromise);
      this.processNextTask();
    }
  }
  
  private processNextTask(): void {
    if (this.pendingTasks.length > 0 && this.activeTasks.size < this.maxConcurrency) {
      const nextTask = this.pendingTasks.shift()!;
      nextTask();
    }
  }
}
```

## 小结

Void 的索引算法体系展现了现代软件系统设计的精妙之处：

### 算法设计亮点

1. **自适应策略**：根据项目规模动态调整遍历深度和限制
2. **多层过滤**：从硬编码规则到动态优化的渐进式过滤
3. **智能排序**：多维度权重的优先级算法
4. **上下文感知截断**：保留重要信息的智能截断
5. **高效渲染**：Unicode 感知的树形结构渲染

### 性能特征

- **时间复杂度**：O(min(n, maxFiles) × min(d, maxDepth))
- **空间复杂度**：O(maxDepth + min(n, maxFiles))
- **实际响应时间**：< 100ms（中等规模项目）
- **内存占用**：< 50MB（包含缓存）

### 工程价值

这些算法不仅解决了 Void 的具体需求，更为类似系统的设计提供了宝贵的参考。特别是在**大厂技术面试**中，这种系统级的算法设计思路和优化策略经常成为考查重点。

下一章我们将分析这些算法在大型代码库中的实际表现和处理策略。 