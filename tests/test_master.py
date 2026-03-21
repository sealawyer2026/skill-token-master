#!/usr/bin/env python3
"""测试套件"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.unified_analyzer import UnifiedAnalyzer
from optimizer.smart_optimizer import SmartOptimizer
from learner.evolution_engine import EvolutionEngine

def test_analyzer():
    """测试分析器"""
    print("🧪 测试分析器...")

    analyzer = UnifiedAnalyzer()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("请你非常仔细地完成这个非常重要的任务，确保你能够全面地理解。")
        f.flush()
        result = analyzer.analyze(f.name)
        assert result['type'] == 'prompt'
        assert result['total_tokens'] > 0
        print(" ✅ 提示词分析通过")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test():\n pass\n")
        f.flush()
        result = analyzer.analyze(f.name)
        assert result['type'] == 'code'
        print(" ✅ 代码分析通过")

    print("✅ 分析器测试全部通过\n")

def test_optimizer():
    """测试优化器"""
    print("🧪 测试优化器...")

    optimizer = SmartOptimizer()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        original = "请你非常仔细地完成这个非常重要的任务。"
        f.write(original)
        f.flush()

        analysis = {'type': 'prompt'}
        result = optimizer.optimize(f.name, analysis, [], auto_fix=False)

        assert result['success']
        assert result['tokens_saved'] >= 0
        print(" ✅ 提示词优化通过")

    print("✅ 优化器测试全部通过\n")

def test_learner():
    """测试学习系统"""
    print("🧪 测试学习系统...")

    with tempfile.TemporaryDirectory() as tmpdir:
        learner = EvolutionEngine(data_dir=tmpdir)

        case_id = learner.learn_from_optimization(
            {'type': 'prompt', 'issues': []},
            {'original_tokens': 100, 'optimized_tokens': 60, 'tokens_saved': 40, 'saving_percentage': 40}
        )
        assert case_id
        print(" ✅ 学习功能通过")

        practices = learner.get_best_practices('prompt')
        assert isinstance(practices, list)
        print(" ✅ 最佳实践获取通过")

        report = learner.get_learning_report()
        assert report['total_cases'] >= 1
        print(" ✅ 学习报告通过")

    print("✅ 学习系统测试全部通过\n")

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("🚀 Token经济大师 - 测试套件")
    print("="*60 + "\n")

    try:
        test_analyzer()
        test_optimizer()
        test_learner()

        print("="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
