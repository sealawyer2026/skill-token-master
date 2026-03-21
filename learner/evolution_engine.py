#!/usr/bin/env python3
"""进化引擎 - 自我学习、持续进化的核心系统"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class EvolutionEngine:
    """进化引擎 - 让技能越用越智能"""

    def __init__(self, data_dir='./data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.cases_file = self.data_dir / 'optimization_cases.json'
        self.patterns_file = self.data_dir / 'learned_patterns.json'
        self.stats_file = self.data_dir / 'evolution_stats.json'

        self.cases = self._load_cases()
        self.patterns = self._load_patterns()
        self.stats = self._load_stats()

    def _load_cases(self) -> List[Dict]:
        """加载优化案例"""
        if self.cases_file.exists():
            with open(self.cases_file) as f:
                return json.load(f)
        return []

    def _load_patterns(self) -> Dict:
        """加载学习到的模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file) as f:
                return json.load(f)
        return {'prompt_patterns': [],
            'code_patterns': [],
            'workflow_patterns': []}

    def _load_stats(self) -> Dict:
        """加载统计信息"""
        if self.stats_file.exists():
            with open(self.stats_file) as f:
                return json.load(f)
        return {'total_optimizations': 0,
            'total_tokens_saved': 0,
            'evolution_count': 0,
            'created_at': datetime.now().isoformat()}

    def _save_all(self):
        """保存所有数据"""
        with open(self.cases_file, 'w') as f:
            json.dump(self.cases, f, indent=2, ensure_ascii=False)
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def learn_from_optimization(self, analysis: Dict, result: Dict):
        """从优化结果中学习"""
        case = {'id': hashlib.md5(f"{datetime.now()}".encode()).hexdigest()[:12],
            'timestamp': datetime.now().isoformat(),
            'file_type': analysis.get('type', 'unknown'),
            'original_tokens': result.get('original_tokens', 0),
            'optimized_tokens': result.get('optimized_tokens', 0),
            'tokens_saved': result.get('tokens_saved', 0),
            'saving_percentage': result.get('saving_percentage', 0),
            'issues': analysis.get('issues', [])}

        self.cases.append(case)

        self.stats['total_optimizations'] += 1
        self.stats['total_tokens_saved'] += case['tokens_saved']

        if self.stats['total_optimizations'] % 100 == 0:
            self.evolve()

        self._save_all()

        return case['id']

    def get_best_practices(self, file_type: str) -> List[Dict]:
        """获取针对特定文件类型的最佳实践"""
        if not self.cases:
            return []

        type_cases = [c for c in self.cases if c['file_type'] == file_type]

        if not type_cases:
            return []

        sorted_cases = sorted(type_cases, key=lambda x: x.get('saving_percentage', 0), reverse=True)

        best_practices = []
        for case in sorted_cases[:5]: # 取前5个最佳案例
            for issue in case.get('issues', []):
                if issue not in best_practices:
                    best_practices.append(issue)

        return best_practices[:10] # 最多返回10条

    def evolve(self) -> Dict[str, Any]:
        """触发自我进化"""
        print("🧬 开始自我进化...")

        if len(self.cases) < 10:
            return {'status': 'insufficient_data', 'message': '需要至少10个案例才能进化'}

        successful_cases = [c for c in self.cases if c.get('saving_percentage', 0) > 30]

        pattern_frequency = {}
        for case in successful_cases:
            for issue in case.get('issues', []):
                pattern_type = issue.get('type', 'unknown')
                pattern_frequency[pattern_type] = pattern_frequency.get(pattern_type, 0) + 1

        new_patterns = {'most_effective': sorted(pattern_frequency.items(), key=lambda x: x[1], reverse=True)[:5],
            'average_saving': sum(c.get('saving_percentage', 0) for c in successful_cases) / len(successful_cases) if successful_cases else 0,
            'evolved_at': datetime.now().isoformat()}

        self.patterns['evolved_patterns'] = new_patterns
        self.stats['evolution_count'] += 1

        self._save_all()

        print(f"✅ 进化完成！已学习 {len(successful_cases)} 个成功案例")
        print(f"📊 最有效的优化模式: {new_patterns['most_effective'][:3]}")

        return {'status': 'success',
            'evolution_count': self.stats['evolution_count'],
            'patterns_learned': len(new_patterns['most_effective']),
            'average_saving': new_patterns['average_saving']}

    def get_learning_report(self) -> Dict[str, Any]:
        """生成学习报告"""
        if not self.cases:
            return {'status': 'no_data', 'message': '还没有学习数据'}

        file_types = {}
        for case in self.cases:
            ft = case.get('file_type', 'unknown')
            if ft not in file_types:
                file_types[ft] = {'count': 0, 'total_saved': 0}
            file_types[ft]['count'] += 1
            file_types[ft]['total_saved'] += case.get('tokens_saved', 0)

        return {'status': 'ok',
            'total_cases': len(self.cases),
            'total_optimizations': self.stats['total_optimizations'],
            'total_tokens_saved': self.stats['total_tokens_saved'],
            'evolution_count': self.stats['evolution_count'],
            'file_type_stats': file_types,
            'best_saving_case': max(self.cases, key=lambda x: x.get('saving_percentage', 0)) if self.cases else None}

if __name__ == '__main__':
    engine = EvolutionEngine()

    for i in range(5):
        engine.learn_from_optimization(
            {'type': 'prompt', 'issues': [{'type': '冗余'}]},
            {'original_tokens': 100, 'optimized_tokens': 60, 'tokens_saved': 40, 'saving_percentage': 40}
        )

    print(json.dumps(engine.get_learning_report(), indent=2, ensure_ascii=False))
