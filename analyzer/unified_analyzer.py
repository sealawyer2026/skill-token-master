#!/usr/bin/env python3
"""统一分析器 - 多维度Token使用分析"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

class UnifiedAnalyzer:
    """统一分析器 - 分析智能体、技能、工作流的Token使用"""

    def __init__(self):
        self.patterns = self._load_detection_patterns()

    def _load_detection_patterns(self):
        """加载检测模式"""
        return {'prompt_waste': [(r'非常|特别|十分|极其', '冗余程度副词'),
                (r'请你|请确保|请保证', '客套用语'),
                (r'详细地|仔细地|认真地', '冗余修饰'),
                (r'重要的|关键的|核心的', '可简化概念'),],
            'code_smells': [(r'import\s+\w+\n', '导入语句'),
                (r'def\s+\w+\([^)]*\):\s*\n\s*pass', '空函数'),
                (r'#.*TODO|#.*FIXME', '待办注释'),],
            'workflow_inefficiency': [(r'"parallel":\s*false', '串行处理'),
                (r'"cache":\s*false', '未启用缓存'),
                (r'"retry":\s*{\s*"max":\s*\d+', '重试配置'),]}

    def analyze(self, target_path: str) -> Dict[str, Any]:
        """全面分析目标"""
        path = Path(target_path)

        if path.is_file():
            return self._analyze_file(path)
        elif path.is_dir():
            return self._analyze_directory(path)

        return {'error': '路径不存在'}

    def _analyze_file(self, path: Path) -> Dict[str, Any]:
        """分析单个文件"""
        content = path.read_text(encoding='utf-8', errors='ignore')

        file_type = self._detect_file_type(path, content)

        if file_type == 'prompt':
            return self._analyze_prompt(content, path)
        elif file_type == 'code':
            return self._analyze_code(content, path)
        elif file_type == 'workflow':
            return self._analyze_workflow(content, path)

        return self._analyze_generic(content, path)

    def _detect_file_type(self, path: Path, content: str) -> str:
        """检测文件类型"""
        suffix = path.suffix.lower()

        if suffix in ['.md', '.txt']:
            return 'prompt'
        elif suffix in ['.py', '.js', '.ts', '.java']:
            return 'code'
        elif suffix in ['.json', '.yaml', '.yml']:
            if 'workflow' in content.lower() or 'steps' in content:
                return 'workflow'
            return 'config'

        return 'generic'

    def _analyze_prompt(self, content: str, path: Path) -> Dict[str, Any]:
        """分析提示词文件"""
        tokens = self._estimate_tokens(content)

        issues = []
        savings = 0

        for pattern, desc in self.patterns['prompt_waste']:
            matches = re.findall(pattern, content)
            if matches:
                count = len(matches)
                saving = count * 2
                savings += saving
                issues.append({'type': '冗余',
                    'description': desc,
                    'count': count,
                    'estimated_saving': saving})

        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 20]
        dupes = len(paragraphs) - len(set(paragraphs))
        if dupes > 0:
            savings += dupes * 10
            issues.append({'type': '重复',
                'description': '重复段落',
                'count': dupes,
                'estimated_saving': dupes * 10})

        return {'type': 'prompt',
            'path': str(path),
            'total_tokens': tokens,
            'issues': issues,
            'estimated_savings': savings,
            'optimization_potential': min(savings / tokens * 100, 80) if tokens > 0 else 0}

    def _analyze_code(self, content: str, path: Path) -> Dict[str, Any]:
        """分析代码文件"""
        tokens = self._estimate_tokens(content)
        lines = content.split('\n')

        issues = []
        savings = 0

        imports = re.findall(r'^(?:import|from)\s+(\w+)', content, re.MULTILINE)
        if len(imports) > 10:
            savings += (len(imports) - 10) * 2
            issues.append({'type': '导入过多',
                'description': '导入语句过多',
                'count': len(imports),
                'estimated_saving': (len(imports) - 10) * 2})

        blank_lines = sum(1 for l in lines if not l.strip())
        if blank_lines > len(lines) * 0.3:
            excess = int(blank_lines - len(lines) * 0.2)
            savings += excess
            issues.append({'type': '空行过多',
                'description': '空行比例过高',
                'count': blank_lines,
                'estimated_saving': excess})

        comments = sum(1 for l in lines if l.strip().startswith('#'))
        if comments > len(lines) * 0.4:
            excess = int((comments - len(lines) * 0.3) * 3)
            savings += excess
            issues.append({'type': '注释过多',
                'description': '注释比例过高',
                'count': comments,
                'estimated_saving': excess})

        code_blocks = [l.strip() for l in lines if len(l.strip()) > 10]
        unique_blocks = set(code_blocks)
        if len(code_blocks) > len(unique_blocks) * 1.5:
            dupes = len(code_blocks) - len(unique_blocks)
            savings += dupes * 5
            issues.append({'type': '重复代码',
                'description': '相似代码块',
                'count': dupes,
                'estimated_saving': dupes * 5})

        return {'type': 'code',
            'path': str(path),
            'total_tokens': tokens,
            'lines': len(lines),
            'issues': issues,
            'estimated_savings': savings,
            'optimization_potential': min(savings / tokens * 100, 70) if tokens > 0 else 0}

    def _analyze_workflow(self, content: str, path: Path) -> Dict[str, Any]:
        """分析工作流文件"""
        try:
            data = json.loads(content)
        except:
            data = {}

        tokens = self._estimate_tokens(content)

        issues = []
        savings = 0

        steps = data.get('steps', [])
        if len(steps) > 5:
            parallelizable = sum(1 for s in steps if not s.get('depends_on'))
            if parallelizable > 2:
                savings += parallelizable * 3
                issues.append({'type': '可并行化',
                    'description': '独立步骤可并行执行',
                    'count': parallelizable,
                    'estimated_saving': parallelizable * 3})

        for step in steps:
            if not step.get('cache', True):
                savings += 5
                issues.append({'type': '未启用缓存',
                    'description': f"步骤 '{step.get('name', 'unknown')}' 未启用缓存",
                    'count': 1,
                    'estimated_saving': 5})

        return {'type': 'workflow',
            'path': str(path),
            'total_tokens': tokens,
            'steps': len(steps),
            'issues': issues,
            'estimated_savings': savings,
            'optimization_potential': min(savings / tokens * 100, 60) if tokens > 0 else 0}

    def _analyze_generic(self, content: str, path: Path) -> Dict[str, Any]:
        """通用文件分析"""
        tokens = self._estimate_tokens(content)
        return {'type': 'generic',
            'path': str(path),
            'total_tokens': tokens,
            'issues': [],
            'estimated_savings': 0,
            'optimization_potential': 0}

    def _analyze_directory(self, path: Path) -> Dict[str, Any]:
        """分析整个目录"""
        total_tokens = 0
        total_savings = 0
        all_issues = []

        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size < 1024 * 1024: # 跳过大于1MB的文件
                try:
                    result = self._analyze_file(file_path)
                    total_tokens += result.get('total_tokens', 0)
                    total_savings += result.get('estimated_savings', 0)
                    all_issues.extend(result.get('issues', []))
                except:
                    pass

        return {'type': 'directory',
            'path': str(path),
            'total_tokens': total_tokens,
            'total_savings': total_savings,
            'files_analyzed': len(all_issues),
            'optimization_potential': min(total_savings / total_tokens * 100, 70) if total_tokens > 0 else 0}

    def _estimate_tokens(self, text: str) -> int:
        """估算Token数量"""
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english = len(text) - chinese
        return int(chinese / 2 + english / 4)

if __name__ == '__main__':
    analyzer = UnifiedAnalyzer()
    import sys
    if len(sys.argv) > 1:
        result = analyzer.analyze(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
