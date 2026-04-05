#!/usr/bin/env python3
"""
Token Master v3.7 主引擎 - Coordinator Pattern + AllowedTools 白名单
目标: 提示词70-80% | 代码85%+

核心架构（参考 DeerFlow Coordinator Pattern）:
1. Coordinator Agent - 任务分解与结果汇总
2. Worker Agents - 并行处理单个文件
3. AllowedTools 白名单 - 精细化工具权限控制
4. 多文件并行压缩支持
"""

import sys
import re
import json
import asyncio
import hashlib
from typing import Dict, Tuple, Optional, List, Set, Callable, Any
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'optimizer'))

from ultra_compressor import UltraCompressor


class ToolPermission(Enum):
    """工具权限级别"""
    ALLOWED = "allowed"           # 明确允许
    DENIED = "denied"             # 明确拒绝
    DEFERRED = "deferred"         # 延迟加载（需要时动态申请）


@dataclass
class CompressionTask:
    """压缩任务定义"""
    task_id: str
    file_path: Optional[str]
    content: str
    content_type: str  # 'prompt' | 'code' | 'text' | 'json'
    priority: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = hashlib.md5(self.content.encode()).hexdigest()[:12]


@dataclass
class CompressionResult:
    """压缩结果"""
    task_id: str
    success: bool
    original_content: str
    compressed_content: str
    compression_stats: Dict
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    processing_time_ms: float = 0.0


@dataclass
class WorkerConfig:
    """Worker 配置"""
    worker_id: str
    allowed_tools: Set[str]  # 白名单工具列表
    max_iterations: int = 3
    aggressive_mode: bool = True
    timeout_seconds: float = 30.0


class AllowedToolsRegistry:
    """
    AllowedTools 白名单注册表
    参考 DeerFlow 的 deferred tool 机制
    """
    
    # 预定义的工具集
    TOOLSETS = {
        "minimal": {"compress", "read_file"},
        "basic": {"compress", "read_file", "write_file", "json"},
        "standard": {"compress", "read_file", "write_file", "json", "analyze"},
        "full": {"compress", "read_file", "write_file", "json", "analyze", "web_search", "fetch"},
        "admin": {"*"},  # 通配符表示所有工具
    }
    
    def __init__(self):
        self._registry: Dict[str, Set[str]] = {}
        self._tool_checkers: Dict[str, Callable] = {}
    
    def register_worker(self, worker_id: str, tools: Set[str]) -> WorkerConfig:
        """注册 Worker 及其允许的工具"""
        # 解析工具集引用
        resolved_tools = self._resolve_tools(tools)
        self._registry[worker_id] = resolved_tools
        
        return WorkerConfig(
            worker_id=worker_id,
            allowed_tools=resolved_tools
        )
    
    def _resolve_tools(self, tools: Set[str]) -> Set[str]:
        """解析工具集引用为具体工具"""
        resolved = set()
        for tool in tools:
            if tool in self.TOOLSETS:
                resolved.update(self.TOOLSETS[tool])
            else:
                resolved.add(tool)
        return resolved
    
    def check_permission(self, worker_id: str, tool_name: str) -> ToolPermission:
        """检查工具权限"""
        if worker_id not in self._registry:
            return ToolPermission.DENIED
        
        allowed = self._registry[worker_id]
        
        # 通配符权限
        if "*" in allowed:
            return ToolPermission.ALLOWED
        
        if tool_name in allowed:
            return ToolPermission.ALLOWED
        
        # 检查是否是延迟加载工具
        if tool_name.startswith("deferred:"):
            base_tool = tool_name.replace("deferred:", "")
            if base_tool in allowed:
                return ToolPermission.DEFERRED
        
        return ToolPermission.DENIED
    
    def require_tool(self, worker_id: str, tool_name: str) -> bool:
        """
        要求使用指定工具，如果不允许则抛出异常
        这是强制的权限检查点
        """
        permission = self.check_permission(worker_id, tool_name)
        
        if permission == ToolPermission.DENIED:
            raise PermissionError(
                f"Worker '{worker_id}' 没有权限使用工具 '{tool_name}'. "
                f"允许的工具: {self._registry.get(worker_id, set())}"
            )
        
        return permission == ToolPermission.ALLOWED
    
    def get_worker_tools(self, worker_id: str) -> Set[str]:
        """获取 Worker 的所有允许工具"""
        return self._registry.get(worker_id, set())
    
    def list_available_toolsets(self) -> Dict[str, List[str]]:
        """列出所有可用的工具集"""
        return {k: list(v) for k, v in self.TOOLSETS.items()}


class CompressionWorker:
    """
    压缩 Worker - 处理单个文件的压缩任务
    类似于 DeerFlow 的 SubAgent
    """
    
    def __init__(self, config: WorkerConfig, registry: AllowedToolsRegistry):
        self.config = config
        self.registry = registry
        self.compressor = UltraCompressor()
        self._tool_usage_log: List[Dict] = []
    
    def _use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        工具调用包装器 - 强制执行白名单检查
        """
        # 强制权限检查
        self.registry.require_tool(self.config.worker_id, tool_name)
        
        # 记录工具使用（不使用 asyncio）
        import time
        self._tool_usage_log.append({
            "tool": tool_name,
            "timestamp": time.time(),
            "args": {k: str(v)[:50] for k, v in kwargs.items()}  # 简要记录参数
        })
        
        # 执行实际工具
        return self._execute_tool(tool_name, **kwargs)
    
    def _execute_tool(self, tool_name: str, **kwargs) -> Any:
        """实际工具执行"""
        tools_map = {
            "compress": self._tool_compress,
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "json": self._tool_json_process,
            "analyze": self._tool_analyze,
        }
        
        if tool_name not in tools_map:
            raise ValueError(f"未知工具: {tool_name}")
        
        return tools_map[tool_name](**kwargs)
    
    def _tool_compress(self, content: str, content_type: str, aggressive: bool = True) -> Tuple[str, Dict]:
        """压缩工具 - 使用 UltraCompressor 进行多轮压缩"""
        current = content
        total_stats = {
            "iterations": [],
            "original_length": len(content),
        }
        
        # 多轮压缩
        for i in range(self.config.max_iterations):
            current, stats = self.compressor.compress(current)
            total_stats["iterations"].append({
                "round": i + 1,
                "length": stats["compressed_length"],
                "savings": stats["savings_percent"]
            })
            # 如果这一轮没有明显改进，停止迭代
            if stats["savings_percent"] < 2:
                break
        
        # 如果是代码且激进模式，应用额外优化
        if content_type == "code" and aggressive:
            current = self._additional_code_optimization(current)
        
        total_stats["final_length"] = len(current)
        total_stats["total_savings"] = (len(content) - len(current)) / len(content) if content else 0
        total_stats["savings_ratio"] = total_stats["total_savings"]
        total_stats["savings_percent"] = total_stats["total_savings"] * 100
        
        return current, total_stats
    
    def _additional_code_optimization(self, code: str) -> str:
        """额外的代码优化（激进模式）"""
        import keyword
        
        # 移除注释
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'"""[\s\S]*?"""', '', code)
        code = re.sub(r"'''[\s\S]*?'''", '', code)
        
        # 简化变量名
        identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
        reserved = set(keyword.kwlist) | {'print', 'len', 'range', 'list', 'dict', 'set', 'str', 'int', 'float'}
        identifiers -= reserved
        
        sorted_ids = sorted(identifiers, key=len, reverse=True)
        short_names = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        name_map = {}
        
        for i, old_name in enumerate(sorted_ids):
            if len(old_name) <= 2:
                continue
            if i < len(short_names):
                name_map[old_name] = short_names[i]
            else:
                name_map[old_name] = short_names[i // len(short_names)] + short_names[i % len(short_names)]
        
        for old_name, new_name in name_map.items():
            code = re.sub(r'\b' + old_name + r'\b', new_name, code)
        
        # 压缩空白
        lines = [line.strip() for line in code.split('\n')]
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    def _tool_read_file(self, path: str) -> str:
        """读取文件工具"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _tool_write_file(self, path: str, content: str) -> bool:
        """写入文件工具"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    def _tool_json_process(self, data: Dict, operation: str = "minify") -> str:
        """JSON 处理工具"""
        if operation == "minify":
            return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _tool_analyze(self, content: str) -> Dict:
        """内容分析工具"""
        return {
            "length": len(content),
            "lines": content.count('\n') + 1,
            "tokens_estimate": len(content) // 4,  # 粗略估算
            "content_type": self._detect_content_type(content)
        }
    
    def _detect_content_type(self, content: str) -> str:
        """检测内容类型"""
        if re.search(r'def\s+\w+|class\s+\w+|import\s+\w+', content):
            return "code"
        elif content.strip().startswith('{'):
            return "json"
        elif len(content) > 100 and content.count(' ') / len(content) > 0.15:
            return "prompt"
        return "text"
    
    def process(self, task: CompressionTask) -> CompressionResult:
        """
        处理单个压缩任务
        这是 Worker 的核心方法
        """
        import time
        start_time = time.time()
        
        try:
            # 步骤1: 分析内容（需要 analyze 权限）
            analysis = self._use_tool("analyze", content=task.content)
            
            # 步骤2: 执行压缩（需要 compress 权限）
            compressed, stats = self._use_tool(
                "compress",
                content=task.content,
                content_type=task.content_type,
                aggressive=self.config.aggressive_mode
            )
            
            # 步骤3: 如果指定了输出路径，写入文件（需要 write_file 权限）
            if task.metadata.get("output_path"):
                self._use_tool("write_file", path=task.metadata["output_path"], content=compressed)
            
            processing_time = (time.time() - start_time) * 1000
            
            return CompressionResult(
                task_id=task.task_id,
                success=True,
                original_content=task.content,
                compressed_content=compressed,
                compression_stats={
                    **stats,
                    "analysis": analysis,
                    "tool_usage_count": len(self._tool_usage_log),
                    "tools_used": [log["tool"] for log in self._tool_usage_log]
                },
                worker_id=self.config.worker_id,
                processing_time_ms=processing_time
            )
            
        except PermissionError as e:
            return CompressionResult(
                task_id=task.task_id,
                success=False,
                original_content=task.content,
                compressed_content=task.content,
                compression_stats={},
                error_message=f"权限错误: {str(e)}",
                worker_id=self.config.worker_id,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return CompressionResult(
                task_id=task.task_id,
                success=False,
                original_content=task.content,
                compressed_content=task.content,
                compression_stats={},
                error_message=f"处理错误: {str(e)}",
                worker_id=self.config.worker_id,
                processing_time_ms=(time.time() - start_time) * 1000
            )


class CoordinatorAgent:
    """
    协调器代理 - 负责任务分解和结果汇总
    参考 DeerFlow Lead Agent 的 Coordinator Pattern
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.registry = AllowedToolsRegistry()
        self.workers: Dict[str, CompressionWorker] = {}
        self.task_history: List[Dict] = []
    
    def create_worker(self, worker_id: str, toolset: str = "standard") -> CompressionWorker:
        """
        创建 Worker 并分配工具权限
        
        Args:
            worker_id: Worker 唯一标识
            toolset: 工具集名称 (minimal/basic/standard/full/admin)
        """
        tools = self.registry.TOOLSETS.get(toolset, self.registry.TOOLSETS["standard"])
        config = self.registry.register_worker(worker_id, tools)
        worker = CompressionWorker(config, self.registry)
        self.workers[worker_id] = worker
        return worker
    
    def decompose_task(self, files: List[Dict]) -> List[CompressionTask]:
        """
        任务分解 - 将文件列表分解为独立的压缩任务
        
        Args:
            files: [{"path": str, "content": str, "type": str}, ...]
        
        Returns:
            List[CompressionTask]
        """
        tasks = []
        for idx, file_info in enumerate(files):
            task = CompressionTask(
                task_id=f"task_{idx}_{hashlib.md5(file_info['content'].encode()).hexdigest()[:8]}",
                file_path=file_info.get("path"),
                content=file_info["content"],
                content_type=file_info.get("type", "text"),
                priority=file_info.get("priority", 0),
                metadata=file_info.get("metadata", {})
            )
            tasks.append(task)
        
        # 记录任务分解
        self.task_history.append({
            "action": "decompose",
            "input_count": len(files),
            "output_tasks": len(tasks),
            "task_ids": [t.task_id for t in tasks]
        })
        
        return tasks
    
    def execute_parallel(self, tasks: List[CompressionTask], toolset: str = "standard") -> List[CompressionResult]:
        """
        并行执行任务 - 每个任务分配独立的 Worker
        
        参考 DeerFlow 的并发限制策略:
        - 最多 max_workers 个并发
        - 超额任务分批次执行
        """
        results = []
        
        # 分批处理（类似于 DeerFlow 的 max_concurrent_subagents）
        batch_size = self.max_workers
        
        for batch_idx in range(0, len(tasks), batch_size):
            batch = tasks[batch_idx:batch_idx + batch_size]
            batch_results = self._execute_batch(batch, toolset, batch_idx)
            results.extend(batch_results)
        
        # 记录执行历史
        self.task_history.append({
            "action": "execute_parallel",
            "total_tasks": len(tasks),
            "batches": (len(tasks) + batch_size - 1) // batch_size,
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success)
        })
        
        return results
    
    def _execute_batch(self, tasks: List[CompressionTask], toolset: str, batch_idx: int) -> List[CompressionResult]:
        """执行一批任务"""
        results = []
        
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            # 为每个任务创建独立的 Worker
            futures = {}
            for i, task in enumerate(tasks):
                worker_id = f"worker_batch{batch_idx}_{i}"
                worker = self.create_worker(worker_id, toolset)
                future = executor.submit(worker.process, task)
                futures[future] = task
            
            # 收集结果
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(CompressionResult(
                        task_id=task.task_id,
                        success=False,
                        original_content=task.content,
                        compressed_content=task.content,
                        compression_stats={},
                        error_message=f"执行异常: {str(e)}"
                    ))
        
        return results
    
    def synthesize_results(self, results: List[CompressionResult]) -> Dict:
        """
        结果汇总 - 将多个 Worker 的结果整合为统一输出
        """
        if not results:
            return {"error": "没有结果可以汇总"}
        
        total_original = sum(len(r.original_content) for r in results)
        total_compressed = sum(len(r.compressed_content) for r in results)
        
        synthesis = {
            "summary": {
                "total_files": len(results),
                "successful": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "total_original_size": total_original,
                "total_compressed_size": total_compressed,
                "overall_savings_ratio": (total_original - total_compressed) / total_original if total_original > 0 else 0,
                "total_processing_time_ms": sum(r.processing_time_ms for r in results)
            },
            "details": []
        }
        
        for result in results:
            detail = {
                "task_id": result.task_id,
                "success": result.success,
                "worker_id": result.worker_id,
                "original_length": len(result.original_content),
                "compressed_length": len(result.compressed_content),
                "processing_time_ms": result.processing_time_ms,
            }
            
            if result.success:
                stats = result.compression_stats
                detail.update({
                    "savings_ratio": stats.get("total_savings", stats.get("savings_ratio", 0)),
                    "tools_used": stats.get("tools_used", []),
                })
            else:
                detail["error"] = result.error_message
            
            synthesis["details"].append(detail)
        
        return synthesis
    
    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.task_history.copy()


class TokenMasterV37:
    """
    Token Master v3.7 主引擎
    新增: Coordinator Pattern + AllowedTools 白名单
    """
    
    VERSION = "3.7.0"
    TARGET_PROMPT_SAVINGS = 0.75
    TARGET_CODE_SAVINGS = 0.85
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.coordinator = CoordinatorAgent(max_workers=max_workers)
        self.registry = self.coordinator.registry
        self.stats = {
            "total_sessions": 0,
            "total_files_processed": 0,
            "avg_savings_ratio": 0.0,
            "permission_denials": 0
        }
    
    def compress_single(self, content: str, content_type: str = "text", 
                       toolset: str = "standard") -> Tuple[str, Dict]:
        """
        压缩单个内容（向后兼容）
        
        Args:
            content: 原始内容
            content_type: 内容类型 (prompt/code/text/json)
            toolset: 使用的工具集
        """
        task = CompressionTask(
            task_id="single_task",
            file_path=None,
            content=content,
            content_type=content_type
        )
        
        results = self.coordinator.execute_parallel([task], toolset)
        result = results[0]
        
        if result.success:
            self._update_stats(result.compression_stats.get("total_savings", 0))
            return result.compressed_content, result.compression_stats
        else:
            raise RuntimeError(f"压缩失败: {result.error_message}")
    
    def compress_multiple(self, files: List[Dict], toolset: str = "standard") -> Dict:
        """
        并行压缩多个文件
        
        Args:
            files: 文件列表 [{"path": str, "content": str, "type": str, "priority": int}, ...]
            toolset: 使用的工具集
        
        Returns:
            汇总结果
        """
        self.stats["total_sessions"] += 1
        
        # 步骤1: 任务分解
        tasks = self.coordinator.decompose_task(files)
        
        # 步骤2: 并行执行
        results = self.coordinator.execute_parallel(tasks, toolset)
        
        # 步骤3: 结果汇总
        synthesis = self.coordinator.synthesize_results(results)
        
        # 更新统计
        self.stats["total_files_processed"] += len(files)
        if synthesis["summary"]["overall_savings_ratio"] > 0:
            self._update_stats(synthesis["summary"]["overall_savings_ratio"])
        
        return synthesis
    
    def compress_prompt(self, text: str, iterations: int = 3) -> Tuple[str, Dict]:
        """压缩提示词（向后兼容 v3.6）"""
        return self.compress_single(text, "prompt", "standard")
    
    def compress_code(self, code: str, aggressive: bool = True) -> Tuple[str, Dict]:
        """压缩代码（向后兼容 v3.6）"""
        toolset = "full" if aggressive else "standard"
        return self.compress_single(code, "code", toolset)
    
    def _update_stats(self, savings_ratio: float):
        """更新统计"""
        n = self.stats["total_files_processed"]
        if n == 0:
            self.stats["avg_savings_ratio"] = savings_ratio
        else:
            self.stats["avg_savings_ratio"] = (
                self.stats["avg_savings_ratio"] * (n - 1) + savings_ratio
            ) / n
    
    def get_worker_permissions(self, worker_id: str) -> Set[str]:
        """获取 Worker 的权限列表"""
        return self.registry.get_worker_tools(worker_id)
    
    def list_toolsets(self) -> Dict[str, List[str]]:
        """列出所有可用工具集"""
        return self.registry.list_available_toolsets()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "version": self.VERSION,
            "max_workers": self.max_workers,
            "total_sessions": self.stats["total_sessions"],
            "total_files_processed": self.stats["total_files_processed"],
            "avg_savings_ratio": f"{self.stats['avg_savings_ratio'] * 100:.1f}%",
            "target_prompt": f"{self.TARGET_PROMPT_SAVINGS * 100:.0f}%",
            "target_code": f"{self.TARGET_CODE_SAVINGS * 100:.0f}%",
            "available_toolsets": list(self.registry.TOOLSETS.keys()),
            "execution_history": self.coordinator.get_execution_history()
        }


# ==================== CLI 入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description=f"Token Master v3.7 - Coordinator Pattern + AllowedTools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 压缩单个提示词
  python v37_engine.py --prompt "请帮我分析这段代码..."
  
  # 压缩单个文件
  python v37_engine.py --file script.py --type code
  
  # 并行压缩多个文件
  python v37_engine.py --files file1.py file2.py file3.py --workers 3
  
  # 使用不同的工具集
  python v37_engine.py --file data.json --toolset minimal
        """
    )
    
    parser.add_argument("--prompt", help="要压缩的提示词文本")
    parser.add_argument("--file", help="要压缩的单个文件路径")
    parser.add_argument("--files", nargs="+", help="要并行压缩的多个文件路径")
    parser.add_argument("--type", default="text", 
                       choices=["prompt", "code", "text", "json"],
                       help="内容类型 (默认: text)")
    parser.add_argument("--toolset", default="standard",
                       choices=["minimal", "basic", "standard", "full", "admin"],
                       help="工具集权限级别 (默认: standard)")
    parser.add_argument("--workers", type=int, default=4,
                       help="最大并行 Worker 数量 (默认: 4)")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--list-toolsets", action="store_true", help="列出可用工具集")
    
    args = parser.parse_args()
    
    engine = TokenMasterV37(max_workers=args.workers)
    
    if args.list_toolsets:
        print("=" * 60)
        print("🛠️  可用工具集 (AllowedTools)")
        print("=" * 60)
        for name, tools in engine.list_toolsets().items():
            print(f"\n{name}:")
            for tool in sorted(tools):
                print(f"  - {tool}")
        return
    
    if args.stats:
        print(json.dumps(engine.get_stats(), indent=2, ensure_ascii=False))
        return
    
    if args.prompt:
        print(f"🚀 Token Master v{TokenMasterV37.VERSION} - 单文件压缩")
        print("=" * 60)
        
        compressed, stats = engine.compress_prompt(args.prompt)
        
        print(f"\n📊 压缩统计:")
        print(f"  原始长度: {stats.get('original_length', len(args.prompt))} 字符")
        print(f"  压缩后长度: {len(compressed)} 字符")
        print(f"  压缩率: {stats.get('total_savings', stats.get('savings_ratio', 0)) * 100:.1f}%")
        print(f"  使用工具: {', '.join(stats.get('tools_used', ['compress']))}")
        
        print(f"\n📝 压缩结果:\n{compressed[:200]}...")
    
    elif args.file:
        print(f"🚀 Token Master v{TokenMasterV37.VERSION} - 单文件压缩")
        print("=" * 60)
        
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compressed, stats = engine.compress_single(content, args.type, args.toolset)
        
        print(f"\n📊 压缩统计:")
        print(f"  文件: {args.file}")
        print(f"  类型: {args.type}")
        print(f"  工具集: {args.toolset}")
        print(f"  原始长度: {len(content)} 字符")
        print(f"  压缩后长度: {len(compressed)} 字符")
        print(f"  压缩率: {stats.get('total_savings', stats.get('savings_ratio', 0)) * 100:.1f}%")
        
        print(f"\n📝 压缩结果预览:\n{compressed[:300]}...")
    
    elif args.files:
        print(f"🚀 Token Master v{TokenMasterV37.VERSION} - 多文件并行压缩")
        print(f"🔄 使用 {args.workers} 个 Worker")
        print("=" * 60)
        
        files = []
        for path in args.files:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 根据扩展名推断类型
                ext = Path(path).suffix.lower()
                type_map = {'.py': 'code', '.js': 'code', '.json': 'json', 
                           '.md': 'prompt', '.txt': 'text'}
                content_type = type_map.get(ext, 'text')
                
                files.append({
                    "path": path,
                    "content": content,
                    "type": content_type
                })
            except Exception as e:
                print(f"❌ 读取文件失败 {path}: {e}")
        
        if not files:
            print("没有可处理的文件")
            return
        
        results = engine.compress_multiple(files, args.toolset)
        
        print(f"\n📊 汇总结果:")
        summary = results["summary"]
        print(f"  处理文件数: {summary['total_files']}")
        print(f"  成功: {summary['successful']} | 失败: {summary['failed']}")
        print(f"  原始总大小: {summary['total_original_size']} 字符")
        print(f"  压缩后总大小: {summary['total_compressed_size']} 字符")
        print(f"  总体压缩率: {summary['overall_savings_ratio'] * 100:.1f}%")
        print(f"  总处理时间: {summary['total_processing_time_ms']:.0f}ms")
        
        print(f"\n📋 详细信息:")
        for detail in results["details"]:
            status = "✅" if detail["success"] else "❌"
            print(f"  {status} {detail['task_id']}: "
                  f"{detail['original_length']} → {detail['compressed_length']} "
                  f"({detail.get('savings_ratio', 0) * 100:.1f}%)")
    
    else:
        # 运行完整演示
        print(f"🚀 Token Master v{TokenMasterV37.VERSION}")
        print("=" * 60)
        print("\n🎯 新增特性:")
        print("  1. Coordinator Pattern - 协调器代理模式")
        print("  2. AllowedTools 白名单机制")
        print("  3. 多文件并行压缩支持")
        print("  4. Worker 级权限控制")
        
        print("\n🛠️ 可用工具集:")
        for name, tools in engine.list_toolsets().items():
            print(f"  {name}: {', '.join(sorted(tools))}")
        
        print("\n" + "=" * 60)
        print("运行测试...")
        print("=" * 60)
        
        # 测试单文件压缩
        test_prompt = """
        请帮我详细分析这段代码的性能瓶颈，并提出具体的优化建议。
        需要考虑时间复杂度、空间复杂度以及内存使用情况。
        同时请提供改进后的代码示例。
        """
        
        print("\n📄 单文件压缩测试:")
        compressed, stats = engine.compress_prompt(test_prompt)
        print(f"  原始: {len(test_prompt)} 字符")
        print(f"  压缩: {len(compressed)} 字符")
        print(f"  节省: {stats.get('total_savings', 0) * 100:.1f}%")
        
        # 测试多文件并行压缩
        print("\n📁 多文件并行压缩测试:")
        test_files = [
            {
                "path": "test1.py",
                "content": '''
def calculate_statistics(data_list):
    """计算列表的统计信息"""
    total_sum = sum(data_list)
    count = len(data_list)
    average = total_sum / count if count > 0 else 0
    variance = sum((x - average) ** 2 for x in data_list) / count
    return {'sum': total_sum, 'count': count, 'average': average, 'variance': variance}
                ''',
                "type": "code"
            },
            {
                "path": "test2.json",
                "content": json.dumps({
                    "name": "test",
                    "items": [{"id": i, "value": f"item_{i}"} for i in range(10)]
                }, indent=2),
                "type": "json"
            },
            {
                "path": "test3.txt",
                "content": "This is a simple text file with some content that could be compressed.",
                "type": "text"
            }
        ]
        
        results = engine.compress_multiple(test_files, "standard")
        summary = results["summary"]
        print(f"  处理文件数: {summary['total_files']}")
        print(f"  成功: {summary['successful']}")
        print(f"  总体压缩率: {summary['overall_savings_ratio'] * 100:.1f}%")
        
        print("\n" + "=" * 60)
        print(json.dumps(engine.get_stats(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
