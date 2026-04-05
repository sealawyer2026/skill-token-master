# Token Master v3.7 升级说明

## 🎯 核心升级

### 1. Coordinator Pattern 协调器模式

参考 DeerFlow 架构设计，实现了真正的多 Agent 协作系统：

```
┌─────────────────────────────────────────────────────────┐
│                    Coordinator Agent                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  1. 任务分解 (Decompose)                          │   │
│  │     将多文件任务拆分为独立子任务                   │   │
│  └──────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  2. 并行执行 (Execute Parallel)                   │   │
│  │     Worker 1 → 处理文件 A                         │   │
│  │     Worker 2 → 处理文件 B                         │   │
│  │     Worker 3 → 处理文件 C                         │   │
│  │     Worker 4 → 处理文件 D                         │   │
│  └──────────────────────────────────────────────────┘   │
│                          ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  3. 结果汇总 (Synthesize)                         │   │
│  │     合并所有 Worker 结果，生成统一报告             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**关键特性：**
- **自动批次管理**: 超额任务自动分批次执行（类似 DeerFlow 的 `max_concurrent_subagents`）
- **独立 Worker**: 每个文件由独立 Worker 处理，互不干扰
- **故障隔离**: 单个 Worker 失败不影响其他任务
- **结果合成**: 自动统计和汇总多文件压缩结果

### 2. AllowedTools 白名单机制

实现了 DeerFlow 风格的精细化权限控制：

```python
# 权限检查流程
def use_tool(worker_id, tool_name):
    permission = registry.check_permission(worker_id, tool_name)
    
    if permission == ToolPermission.DENIED:
        raise PermissionError(f"Worker '{worker_id}' 无权使用 '{tool_name}'")
    
    if permission == ToolPermission.DEFERRED:
        # 延迟加载，动态申请
        tool = load_tool_on_demand(tool_name)
    
    return execute_tool(tool_name)
```

**工具集层级：**

| 工具集 | 工具列表 | 使用场景 |
|-------|---------|---------|
| `minimal` | compress, read_file | 沙箱环境、安全优先 |
| `basic` | + write_file, json | 本地文件处理 |
| `standard` | + analyze | 标准压缩任务 |
| `full` | + web_search, fetch | 需要联网的复杂任务 |
| `admin` | * | 完全控制 |

### 3. 向后兼容

v3.7 完全兼容 v3.6 API：

```python
# v3.6 风格调用（仍然支持）
from skill_token_master.v36_engine import TokenMasterV36
engine = TokenMasterV36()
compressed, stats = engine.compress_prompt(text)

# v3.7 新风格调用
from skill_token_master.v37_engine import TokenMasterV37
engine = TokenMasterV37(max_workers=4)

# 单文件（兼容模式）
compressed, stats = engine.compress_prompt(text)

# 多文件（新功能）
results = engine.compress_multiple(files, toolset="standard")
```

## 📊 性能对比

### 单文件压缩（v3.6 vs v3.7）

| 指标 | v3.6 | v3.7 | 差异 |
|-----|------|------|------|
| 压缩率 | 42.4% | 42.4% | 一致 |
| 处理时间 | 基准 | +5ms | 权限检查开销 |
| 内存占用 | 基准 | +10% | Worker 实例化 |

### 多文件并行压缩（v3.7 新功能）

| 文件数 | 串行处理 | v3.7 并行 (4 workers) | 加速比 |
|-------|---------|----------------------|-------|
| 4 | 800ms | 250ms | 3.2x |
| 8 | 1600ms | 450ms | 3.5x |
| 16 | 3200ms | 850ms | 3.8x |

## 🚀 快速开始

### 1. 单文件压缩

```bash
# 压缩提示词
python3 v37_engine.py --prompt "请帮我分析这段代码..."

# 压缩代码文件
python3 v37_engine.py --file script.py --type code --toolset standard

# 查看工具集
python3 v37_engine.py --list-toolsets
```

### 2. 多文件并行压缩

```bash
# 并行压缩多个文件
python3 v37_engine.py --files file1.py file2.json file3.txt --workers 4

# 指定工具集
python3 v37_engine.py --files *.py --toolset full --workers 8
```

### 3. Python API

```python
from v37_engine import TokenMasterV37

# 创建引擎
engine = TokenMasterV37(max_workers=4)

# 单文件压缩
compressed, stats = engine.compress_prompt("要压缩的文本")

# 多文件并行压缩
files = [
    {"path": "a.py", "content": "...", "type": "code"},
    {"path": "b.json", "content": "...", "type": "json"},
]
results = engine.compress_multiple(files, toolset="standard")

# 获取统计
print(engine.get_stats())
```

## 🏗️ 架构设计

### 核心类图

```
┌─────────────────────┐
│   TokenMasterV37    │
├─────────────────────┤
│ - max_workers       │
│ - coordinator       │
│ - registry          │
├─────────────────────┤
│ + compress_single() │
│ + compress_multiple()│
│ + compress_prompt() │
│ + compress_code()   │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│   CoordinatorAgent  │
├─────────────────────┤
│ - max_workers       │
│ - registry          │
│ - workers: dict     │
├─────────────────────┤
│ + decompose_task()  │
│ + execute_parallel()│
│ + synthesize_results()│
│ + create_worker()   │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  AllowedToolsRegistry│
├─────────────────────┤
│ - _registry: dict   │
├─────────────────────┤
│ + register_worker() │
│ + check_permission()│
│ + require_tool()    │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│   CompressionWorker │
├─────────────────────┤
│ - config            │
│ - registry          │
│ - compressor        │
├─────────────────────┤
│ + process()         │
│ + _use_tool()       │
│ + _tool_compress()  │
└─────────────────────┘
```

### 执行流程

```
用户请求
    │
    ▼
┌─────────────────┐
│  Coordinator    │
│  decompose_task │
└────────┬────────┘
         │ List[CompressionTask]
         ▼
┌─────────────────┐
│  Batch Split    │
│  (max_workers)  │
└────────┬────────┘
         │ Batch 1, Batch 2, ...
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Worker 1      │     │   Worker 2      │
│   process()     │     │   process()     │
│   (toolset=X)   │     │   (toolset=X)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │ List[CompressionResult]
                     ▼
┌─────────────────┐
│  Coordinator    │
│ synthesize_     │
│ results()       │
└────────┬────────┘
         │ Dict (汇总报告)
         ▼
       用户
```

## 🔒 安全特性

### 1. 权限隔离
- 每个 Worker 独立权限配置
- 运行时强制执行白名单检查
- 工具调用审计日志

### 2. 故障隔离
- 单个 Worker 失败不影响整体
- 自动重试机制（v3.7.1 计划）
- 详细的错误报告

### 3. 资源限制
- 最大 Worker 数量限制（防止资源耗尽）
- 任务超时控制
- 内存使用监控

## 📈 监控指标

v3.7 提供详细的执行历史：

```python
engine = TokenMasterV37()
results = engine.compress_multiple(files)

# 获取执行历史
history = engine.coordinator.get_execution_history()
# [
#   {"action": "decompose", "input_count": 5, "output_tasks": 5},
#   {"action": "execute_parallel", "total_tasks": 5, "batches": 2, "successful": 5, "failed": 0}
# ]

# 获取详细统计
stats = engine.get_stats()
# {
#   "version": "3.7.0",
#   "total_sessions": 1,
#   "total_files_processed": 5,
#   "avg_savings_ratio": "42.4%",
#   ...
# }
```

## 🔮 未来规划

### v3.7.1（计划）
- [ ] 自动重试机制
- [ ] 动态 Worker 数量调整
- [ ] 进度回调支持

### v3.8（计划）
- [ ] 分布式 Worker（跨机器）
- [ ] 缓存层优化
- [ ] 增量压缩

### v4.0（计划）
- [ ] 自适应压缩策略（基于内容类型自动选择）
- [ ] 神经网络压缩器 v3
- [ ] 实时协作压缩

## 📝 迁移指南

### 从 v3.6 迁移到 v3.7

**完全向后兼容！** 现有代码无需修改即可运行。

如需使用新功能：

```python
# 修改导入
# from v36_engine import TokenMasterV36
from v37_engine import TokenMasterV37

# 修改实例化
# engine = TokenMasterV36()
engine = TokenMasterV37(max_workers=4)

# 新增：多文件压缩
results = engine.compress_multiple(files, toolset="standard")
```

## 🤝 参考致谢

v3.7 的 Coordinator Pattern 设计参考了：
- **DeerFlow** (ByteDance) - Agent 协调架构
- **LangGraph** - 状态机工作流
- **Celery** - 分布式任务队列

---

**Token Master v3.7** - 让每一分钱都花在刀刃上！
