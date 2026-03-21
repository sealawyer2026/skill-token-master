#!/usr/bin/env python3
"""深度评测脚本 - 全面测试Token经济大师"""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.unified_analyzer import UnifiedAnalyzer
from optimizer.smart_optimizer import SmartOptimizer
from learner.evolution_engine import EvolutionEngine

class DeepEvaluator:
    """深度评测器"""

    def __init__(self):
        self.results = []

    def test_prompt_optimization(self):
        """测试提示词优化效果"""
        print("\n📋 测试1: 提示词优化效果")
        print("-" * 50)

        test_cases = [{'name': '冗余修饰词',
                'input': '请你非常仔细地分析这个特别重要的合同条款，确保你能够全面地理解每一个细节。',
                'expected_saving': 30},
            {'name': '客套用语',
                'input': '请你帮我完成这个任务，请确保质量，请保证准确性，非常感谢。',
                'expected_saving': 25},
            {'name': '重复内容',
                'input': '这是一个重要的任务。这是一个重要的任务。请认真完成。',
                'expected_saving': 20}]

        optimizer = SmartOptimizer()
        total_saving = 0

        for case in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(case['input'])
                f.flush()

                analysis = {'type': 'prompt'}
                result = optimizer.optimize(f.name, analysis, [], auto_fix=False)

                saving = result.get('saving_percentage', 0)
                total_saving += saving

                status = '✅' if saving >= case['expected_saving'] else '⚠️'
                print(f" {status} {case['name']}: 节省 {saving}% (预期 ≥{case['expected_saving']}%)")

        avg_saving = total_saving / len(test_cases)
        print(f"\n 平均节省: {avg_saving:.1f}%")
        return avg_saving >= 25

    def test_code_optimization(self):
        """测试代码优化效果"""
        print("\n📋 测试2: 代码优化效果")
        print("-" * 50)
        
        test_code = '''def example_function():
    # 这是一个很重要的函数
    # 需要仔细处理
    # 参数: 无
    # 返回: int
    
    result = 0
    
    # 循环处理 - 计算0到9的和
    for i in range(10):
        result += i
        
    return result
    
    
def another_function():
    \"\"\"这是一个空函数\"\"\"\n    pass
    
def check_value(x):
    # 检查x是否为True
    if x == True:
        return True
    if x == False:
        return False
    return None
'''
        
        optimizer = SmartOptimizer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            f.flush()

            analysis = {'type': 'code'}
            result = optimizer.optimize(f.name, analysis, [], auto_fix=False)

            saving = result.get('saving_percentage', 0)
            status = '✅' if saving >= 20 else '⚠️'
            print(f" {status} 代码压缩: 节省 {saving}% (预期 ≥20%)")

            return saving >= 20

    def test_learning_evolution(self):
        """测试学习进化能力"""
        print("\n📋 测试3: 学习进化能力")
        print("-" * 50)

        with tempfile.TemporaryDirectory() as tmpdir:
            learner = EvolutionEngine(data_dir=tmpdir)

            print(" 模拟100次优化...")
            for i in range(100):
                learner.learn_from_optimization(
                    {'type': 'prompt', 'issues': [{'type': '冗余'}]},
                    {'original_tokens': 100 + i % 50,
                        'optimized_tokens': 60 + i % 30,
                        'tokens_saved': 40 + i % 20,
                        'saving_percentage': 40 + i % 10}
                )

            print(" 触发自我进化...")
            evolution_result = learner.evolve()

            success = evolution_result.get('status') == 'success'
            status = '✅' if success else '❌'
            print(f" {status} 进化成功: {evolution_result.get('patterns_learned', 0)} 个模式")

            report = learner.get_learning_report()
            print(f" 📊 学习统计:")
            print(f" - 总案例: {report['total_cases']}")
            print(f" - 总节省: {report['total_tokens_saved']} tokens")
            print(f" - 进化次数: {report['evolution_count']}")

            return success and report['total_cases'] == 100

    def test_performance(self):
        """测试性能"""
        print("\n📋 测试4: 性能测试")
        print("-" * 50)

        analyzer = UnifiedAnalyzer()
        optimizer = SmartOptimizer()

        test_content = "这是一个测试内容。" * 100

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(test_content)
            f.flush()

            start = time.time()
            analyzer.analyze(f.name)
            analyze_time = time.time() - start

            start = time.time()
            optimizer.optimize(f.name, {'type': 'prompt'}, [], auto_fix=False)
            optimize_time = time.time() - start

            print(f" ✅ 分析速度: {analyze_time*1000:.1f}ms")
            print(f" ✅ 优化速度: {optimize_time*1000:.1f}ms")

            return analyze_time < 1.0 and optimize_time < 1.0

    def run_all_tests(self):
        """运行所有评测"""
        print("="*60)
        print("🔬 Token经济大师 - 深度评测")
        print("="*60)

        results = {'提示词优化': self.test_prompt_optimization(),
            '代码优化': self.test_code_optimization(),
            '学习进化': self.test_learning_evolution(),
            '性能测试': self.test_performance()}

        print("\n" + "="*60)
        print("📊 评测总结")
        print("="*60)

        passed = sum(results.values())
        total = len(results)

        for test, result in results.items():
            status = '✅ 通过' if result else '❌ 失败'
            print(f" {test}: {status}")

        print(f"\n 总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")

        if passed == total:
            print("\n🎉 所有评测通过！技能质量优秀")
            return True
        else:
            print(f"\n⚠️ 有 {total-passed} 项需要改进")
            return False

if __name__ == '__main__':
    evaluator = DeepEvaluator()
    success = evaluator.run_all_tests()
    sys.exit(0 if success else 1)
