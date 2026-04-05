#!/usr/bin/env python3
"""
Token Master v3.7 功能测试脚本
验证所有核心功能正常工作
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'optimizer'))

from v37_engine import (
    TokenMasterV37, 
    CoordinatorAgent, 
    CompressionWorker,
    CompressionTask,
    AllowedToolsRegistry,
    ToolPermission
)


def test_allowed_tools_registry():
    """测试 AllowedTools 白名单机制"""
    print("\n" + "="*60)
    print("🧪 测试 1: AllowedTools 白名单机制")
    print("="*60)
    
    registry = AllowedToolsRegistry()
    
    # 测试注册 Worker
    config = registry.register_worker("test_worker", {"standard"})
    print(f"✅ Worker 注册成功: {config.worker_id}")
    print(f"   允许工具: {sorted(config.allowed_tools)}")
    
    # 测试权限检查
    assert registry.check_permission("test_worker", "compress") == ToolPermission.ALLOWED
    assert registry.check_permission("test_worker", "analyze") == ToolPermission.ALLOWED
    assert registry.check_permission("test_worker", "web_search") == ToolPermission.DENIED
    print("✅ 权限检查正常")
    
    # 测试 require_tool
    try:
        registry.require_tool("test_worker", "compress")
        print("✅ require_tool (允许) 正常")
    except PermissionError:
        print("❌ require_tool (允许) 异常")
        return False
    
    try:
        registry.require_tool("test_worker", "unauthorized_tool")
        print("❌ require_tool (拒绝) 应该抛出异常")
        return False
    except PermissionError as e:
        print(f"✅ require_tool (拒绝) 正常抛出异常: {str(e)[:50]}...")
    
    # 测试 admin 权限
    admin_config = registry.register_worker("admin_worker", {"admin"})
    assert registry.check_permission("admin_worker", "any_tool") == ToolPermission.ALLOWED
    print("✅ Admin 通配符权限正常")
    
    print("\n✅ AllowedTools 测试全部通过!")
    return True


def test_compression_worker():
    """测试 CompressionWorker"""
    print("\n" + "="*60)
    print("🧪 测试 2: CompressionWorker")
    print("="*60)
    
    registry = AllowedToolsRegistry()
    config = registry.register_worker("worker_1", {"standard"})
    worker = CompressionWorker(config, registry)
    
    # 测试任务处理
    task = CompressionTask(
        task_id="test_task_1",
        file_path=None,
        content="这是一个测试内容，用于验证压缩功能是否正常工作。",
        content_type="text"
    )
    
    result = worker.process(task)
    
    assert result.success, f"任务处理失败: {result.error_message}"
    assert result.task_id == "test_task_1"
    assert len(result.compressed_content) < len(result.original_content)
    assert result.worker_id == "worker_1"
    
    print(f"✅ 任务处理成功")
    print(f"   原始长度: {len(result.original_content)}")
    print(f"   压缩后: {len(result.compressed_content)}")
    print(f"   压缩率: {result.compression_stats.get('savings_ratio', 0)*100:.1f}%")
    print(f"   处理时间: {result.processing_time_ms:.1f}ms")
    print(f"   使用工具: {result.compression_stats.get('tools_used', [])}")
    
    print("\n✅ CompressionWorker 测试全部通过!")
    return True


def test_coordinator_agent():
    """测试 CoordinatorAgent"""
    print("\n" + "="*60)
    print("🧪 测试 3: CoordinatorAgent")
    print("="*60)
    
    coordinator = CoordinatorAgent(max_workers=2)
    
    # 测试任务分解
    files = [
        {"path": "file1.py", "content": "def hello(): print('hello')", "type": "code"},
        {"path": "file2.txt", "content": "这是一个测试文本内容", "type": "text"},
    ]
    
    tasks = coordinator.decompose_task(files)
    assert len(tasks) == 2
    print(f"✅ 任务分解成功: {len(tasks)} 个任务")
    
    # 测试并行执行
    results = coordinator.execute_parallel(tasks, toolset="standard")
    assert len(results) == 2
    success_count = sum(1 for r in results if r.success)
    print(f"✅ 并行执行成功: {success_count}/{len(results)} 个任务成功")
    
    # 测试结果汇总
    synthesis = coordinator.synthesize_results(results)
    assert "summary" in synthesis
    assert "details" in synthesis
    print(f"✅ 结果汇总成功")
    print(f"   总体压缩率: {synthesis['summary']['overall_savings_ratio']*100:.1f}%")
    print(f"   总处理时间: {synthesis['summary']['total_processing_time_ms']:.1f}ms")
    
    # 测试执行历史
    history = coordinator.get_execution_history()
    assert len(history) >= 2
    print(f"✅ 执行历史记录: {len(history)} 条记录")
    
    print("\n✅ CoordinatorAgent 测试全部通过!")
    return True


def test_token_master_v37():
    """测试 TokenMasterV37 主引擎"""
    print("\n" + "="*60)
    print("🧪 测试 4: TokenMasterV37 主引擎")
    print("="*60)
    
    engine = TokenMasterV37(max_workers=3)
    
    # 测试单文件压缩（向后兼容）
    print("\n📄 测试单文件压缩...")
    test_prompt = "请帮我详细分析这段代码的性能瓶颈和优化建议。"
    compressed, stats = engine.compress_prompt(test_prompt)
    
    assert len(compressed) < len(test_prompt)
    assert "savings_ratio" in stats or "total_savings" in stats
    print(f"✅ 单文件压缩成功")
    print(f"   原始: {len(test_prompt)} → 压缩: {len(compressed)}")
    print(f"   压缩率: {stats.get('total_savings', stats.get('savings_ratio', 0))*100:.1f}%")
    
    # 测试多文件并行压缩
    print("\n📁 测试多文件并行压缩...")
    files = [
        {"path": "test1.py", "content": "def calc(x): return x * 2", "type": "code"},
        {"path": "test2.json", "content": '{"key": "value", "num": 123}', "type": "json"},
        {"path": "test3.txt", "content": "简单文本内容用于测试压缩功能", "type": "text"},
    ]
    
    results = engine.compress_multiple(files, toolset="standard")
    
    assert results["summary"]["total_files"] == 3
    assert results["summary"]["successful"] == 3
    print(f"✅ 多文件并行压缩成功")
    print(f"   处理文件: {results['summary']['total_files']}")
    print(f"   成功: {results['summary']['successful']}")
    print(f"   总体压缩率: {results['summary']['overall_savings_ratio']*100:.1f}%")
    
    # 测试工具集列表
    print("\n🛠️ 测试工具集列表...")
    toolsets = engine.list_toolsets()
    assert "minimal" in toolsets
    assert "standard" in toolsets
    assert "admin" in toolsets
    print(f"✅ 工具集列表正常: {list(toolsets.keys())}")
    
    # 测试统计信息
    print("\n📊 测试统计信息...")
    stats = engine.get_stats()
    assert stats["version"] == "3.7.0"
    assert stats["max_workers"] == 3
    print(f"✅ 统计信息正常")
    print(f"   版本: {stats['version']}")
    print(f"   最大 Workers: {stats['max_workers']}")
    print(f"   处理文件数: {stats['total_files_processed']}")
    
    print("\n✅ TokenMasterV37 测试全部通过!")
    return True


def test_batch_processing():
    """测试大批量处理（批次分割）"""
    print("\n" + "="*60)
    print("🧪 测试 5: 大批量处理（批次分割）")
    print("="*60)
    
    # 创建只有 2 个 worker 的引擎，测试批次分割
    engine = TokenMasterV37(max_workers=2)
    
    # 创建 5 个文件（超过 max_workers，应该分 3 批）
    files = [
        {"path": f"file_{i}.txt", "content": f"内容 {i} " * 20, "type": "text"}
        for i in range(5)
    ]
    
    results = engine.compress_multiple(files, toolset="standard")
    
    assert results["summary"]["total_files"] == 5
    assert results["summary"]["successful"] == 5
    
    # 检查执行历史，应该有分批次记录
    history = engine.coordinator.get_execution_history()
    batch_executions = [h for h in history if h["action"] == "execute_parallel"]
    
    print(f"✅ 大批量处理成功")
    print(f"   总文件: {results['summary']['total_files']}")
    print(f"   执行批次记录: {len(batch_executions)} 次")
    
    if batch_executions:
        last_batch = batch_executions[-1]
        print(f"   最后一次执行: {last_batch.get('total_tasks')} 任务, "
              f"{last_batch.get('batches')} 批次")
    
    print("\n✅ 大批量处理测试全部通过!")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("   Token Master v3.7 功能测试")
    print("🚀" * 30)
    
    tests = [
        ("AllowedTools 白名单", test_allowed_tools_registry),
        ("CompressionWorker", test_compression_worker),
        ("CoordinatorAgent", test_coordinator_agent),
        ("TokenMasterV37 主引擎", test_token_master_v37),
        ("大批量处理", test_batch_processing),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ {name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有测试通过! Token Master v3.7 运行正常!")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 个测试未通过，请检查实现")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
