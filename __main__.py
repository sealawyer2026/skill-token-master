#!/usr/bin/env python3
"""Token经济大师 - 智能分析与优化系统"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyzer.unified_analyzer import UnifiedAnalyzer
from optimizer.smart_optimizer import SmartOptimizer
from learner.evolution_engine import EvolutionEngine
from monitor.intelligent_monitor import IntelligentMonitor

class TokenEconomyMaster:
    """Token经济大师主类 - 一站式Token优化解决方案"""

    VERSION = "2.0.0"

    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.analyzer = UnifiedAnalyzer()
        self.optimizer = SmartOptimizer()
        self.learner = EvolutionEngine()
        self.monitor = IntelligentMonitor()

    def _load_config(self, path):
        """加载配置文件"""
        import json
        default = {"optimization_level": "smart",
            "preserve_semantics": True,
            "auto_evolve": True,
            "safety_checks": True}
        if path and Path(path).exists():
            with open(path) as f:
                return {**default, **json.load(f)}
        return default

    def analyze(self, target_path):
        """全面分析目标项目的Token使用情况"""
        print(f"🔍 正在分析: {target_path}")
        return self.analyzer.analyze(target_path)

    def optimize(self, target_path, auto_fix=False):
        """智能优化目标项目"""
        print(f"⚡ 正在优化: {target_path}")

        analysis = self.analyzer.analyze(target_path)

        patterns = self.learner.get_best_practices(analysis['type'])

        result = self.optimizer.optimize(target_path, analysis, patterns, auto_fix)

        if result['success']:
            self.learner.learn_from_optimization(analysis, result)

        return result

    def evolve(self):
        """触发自我进化"""
        print("🧬 开始自我进化...")
        return self.learner.evolve()

    def monitor_mode(self, target_path):
        """启动实时监控模式"""
        print(f"👁️ 启动监控: {target_path}")
        self.monitor.start_watching(target_path)

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Token经济大师')
    parser.add_argument('command', choices=['analyze', 'optimize', 'evolve', 'monitor'])
    parser.add_argument('target', nargs='?', help='目标路径')
    parser.add_argument('--auto-fix', action='store_true', help='自动修复')
    parser.add_argument('--config', help='配置文件路径')

    args = parser.parse_args()

    master = TokenEconomyMaster(args.config)

    if args.command == 'analyze' and args.target:
        result = master.analyze(args.target)
        print(f"\n📊 分析结果:")
        print(f" 总Token数: {result.get('total_tokens', 0):,}")
        print(f" 可优化空间: {result.get('optimization_potential', 0)}%")

    elif args.command == 'optimize' and args.target:
        result = master.optimize(args.target, args.auto_fix)
        print(f"\n⚡ 优化结果:")
        print(f" 节省Token: {result.get('tokens_saved', 0):,}")
        print(f" 节省比例: {result.get('saving_percentage', 0)}%")

    elif args.command == 'evolve':
        master.evolve()

    elif args.command == 'monitor' and args.target:
        master.monitor_mode(args.target)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
