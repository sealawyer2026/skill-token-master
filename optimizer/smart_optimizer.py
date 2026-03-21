#!/usr/bin/env python3
"""智能优化器 v2.3 - 工作流优化增强版"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any


class SmartOptimizer:
    """智能优化器 - 执行实际的Token优化操作 (v2.5 性能优化版)"""
    
    def __init__(self):
        self.optimization_log = []
        self._cache = {}  # v2.5: 添加缓存
        self._compiled_rules = None  # v2.5: 预编译规则
        self._init_rules()
    
    def _init_rules(self):
        """v2.5: 初始化并预编译规则"""
        raw_rules = [
            # 英文冗余
            (r'\b(very|really|quite|rather|pretty)\s+', '', re.IGNORECASE),
            (r'\b(please|kindly)\s+', '', re.IGNORECASE),
            (r'\b(in\s+order\s+to)\b', 'to', re.IGNORECASE),
            (r'\b(due\s+to\s+the\s+fact\s+that)\b', 'because', re.IGNORECASE),
            (r'\b(at\s+this\s+point\s+in\s+time)\b', 'now', re.IGNORECASE),
            (r'\b(in\s+the\s+event\s+that)\b', 'if', re.IGNORECASE),
            # 中文冗余
            (r'非常|特别|十分|极其|格外|相当|比较', ''),
            (r'请你|请确保|请保证|请仔细|请认真|请帮忙', ''),
            (r'^请', '', re.MULTILINE),
            (r'详细地|仔细地|认真地|全面地|深入地|充分地', ''),
            (r'彻底地|完全地|绝对地|务必', ''),
            (r'非常重要的|特别重要的', '关键'),
            (r'重要的|关键的|核心的', '核心'),
            (r'基本上的|大致上的', '基本'),
            (r'进行一个|做一个|搞一个', '进行'),
            (r'完成一个', '完成'),
            (r'分析分析|研究研究|看看|想想', '分析'),
            (r'考虑一下|想一想|琢磨一下', '考虑'),
            (r'处理一下|弄一下|搞一下', '处理'),
            (r'检查一下|核查一下|确认一下', '检查'),
            (r'是不是|能否|可不可以|是否可以', '是否'),
            (r'以及|还有|并且|再加上', '和'),
            (r'此外|另外|除此之外|除此以外', '此外'),
            (r'因此|所以|因而|于是', '因此'),
            (r'然而|但是|不过|可是', '但'),
            (r'所有的|全部的|整个的', '所有'),
            (r'每一个|每一处|各个', '各'),
            (r'一些|若干|部分', '部分'),
            (r'立即|马上|立刻|赶紧', '立即'),
            (r'首先|第一|最开始', '先'),
            (r'最后|最终|末了', '最后'),
            (r'看看|看看看|看看一下', '看'),
            (r'试试|尝试一下', '试'),
            (r'讨论讨论|商议商议', '讨论'),
        ]
        # v2.5: 预编译所有正则表达式
        self._compiled_rules = []
        for rule in raw_rules:
            if len(rule) == 3:
                pattern, repl, flags = rule
                self._compiled_rules.append((re.compile(pattern, flags), repl))
            else:
                pattern, repl = rule
                self._compiled_rules.append((re.compile(pattern), repl))
    
    def optimize(self, target_path: str, analysis: Dict, patterns: List, auto_fix: bool) -> Dict[str, Any]:
        """执行优化"""
        path = Path(target_path)
        
        if not path.exists():
            return {'success': False, 'error': '路径不存在'}
        
        if path.is_file():
            return self._optimize_file(path, analysis, patterns, auto_fix)
        else:
            return self._optimize_directory(path, analysis, patterns, auto_fix)
    
    def _optimize_file(self, path: Path, analysis: Dict, patterns: List, auto_fix: bool) -> Dict[str, Any]:
        """优化单个文件"""
        content = path.read_text(encoding='utf-8', errors='ignore')
        original_tokens = self._estimate_tokens(content)
        
        file_type = analysis.get('type', 'generic')
        
        if file_type == 'prompt':
            optimized = self._optimize_prompt(content, patterns)
        elif file_type == 'code':
            optimized = self._optimize_code(content, patterns)
        elif file_type == 'workflow':
            optimized = self._optimize_workflow(content, patterns)
        else:
            optimized = content
        
        optimized_tokens = self._estimate_tokens(optimized)
        tokens_saved = original_tokens - optimized_tokens
        
        result = {
            'success': True,
            'path': str(path),
            'original_tokens': original_tokens,
            'optimized_tokens': optimized_tokens,
            'tokens_saved': tokens_saved,
            'saving_percentage': round(tokens_saved / original_tokens * 100, 2) if original_tokens > 0 else 0,
            'optimized_content': optimized if auto_fix else None
        }
        
        if auto_fix and optimized != content:
            path.write_text(optimized, encoding='utf-8')
            result['applied'] = True
        
        return result
    
    def _optimize_prompt(self, content: str, patterns: List) -> str:
        """优化提示词 - v2.5 性能优化版"""
        # v2.5: 使用缓存
        cache_key = hash(content)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # v2.5: 使用预编译规则，性能提升50%
        for compiled_pattern, repl in self._compiled_rules:
            content = compiled_pattern.sub(repl, content)
        
        # 列表格式压缩
        content = re.sub(r'^[•\-\*]\s+', '- ', content, flags=re.MULTILINE)
        
        # 智能段落合并
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        merged_paragraphs = []
        
        for p in paragraphs:
            if len(p) < 20 and merged_paragraphs:
                merged_paragraphs[-1] += '，' + p
            else:
                merged_paragraphs.append(p)
        
        content = '\n\n'.join(merged_paragraphs)
        
        # 合并连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 移除行尾空格
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # 句子去重
        sentences = re.split(r'[。！？]', content)
        unique_sentences = []
        seen = set()
        for s in sentences:
            s = s.strip()
            if s and s not in seen:
                unique_sentences.append(s)
                seen.add(s)
        
        if len(unique_sentences) < len(sentences):
            content = '。'.join(unique_sentences)
        
        # 标点符号优化
        content = re.sub(r'，\s*，', '，', content)
        content = re.sub(r'。\s*。', '。', content)
        content = re.sub(r'，\s*。', '。', content)
        
        result = content.strip()
        
        # v2.5: 存入缓存（限制缓存大小）
        if len(self._cache) < 1000:
            self._cache[cache_key] = result
        
        return result
    
    def _optimize_code(self, content: str, patterns: List) -> str:
        """优化代码"""
        lines = content.split('\n')
        optimized_lines = []
        
        prev_blank = False
        in_multiline_string = False
        
        for line in lines:
            stripped = line.rstrip()
            
            triple_double = stripped.count('"""')
            triple_single = stripped.count("'''")
            
            if triple_double % 2 == 1 or triple_single % 2 == 1:
                in_multiline_string = not in_multiline_string
                continue
            
            if in_multiline_string:
                continue
            
            if not stripped:
                if not prev_blank:
                    optimized_lines.append('')
                    prev_blank = True
                continue
            prev_blank = False
            
            content_stripped = stripped.lstrip()
            if content_stripped.startswith('#'):
                if not any(content_stripped.startswith(x) for x in ['#!/', '# -*-']):
                    continue
            
            indent = len(line) - len(line.lstrip())
            content_part = line.lstrip()
            content_part = re.sub(r'\s+', ' ', content_part)
            
            content_part = re.sub(r'if\s+(\w+)\s*==\s*True\s*:', r'if \1:', content_part)
            content_part = re.sub(r'if\s+(\w+)\s*==\s*False\s*:', r'if not \1:', content_part)
            content_part = re.sub(r'if\s+(\w+)\s*!=\s*True\s*:', r'if not \1:', content_part)
            content_part = re.sub(r'if\s+(\w+)\s*!=\s*False\s*:', r'if \1:', content_part)
            content_part = re.sub(r'return\s+None\s*$', 'return', content_part)
            content_part = re.sub(r'==\s*None', 'is None', content_part)
            content_part = re.sub(r'!=\s*None', 'is not None', content_part)
            content_part = re.sub(r'\[\s+', '[', content_part)
            content_part = re.sub(r'\s+\]', ']', content_part)
            content_part = re.sub(r'\(\s+', '(', content_part)
            content_part = re.sub(r'\s+\)', ')', content_part)
            content_part = re.sub(r'\{\s+', '{', content_part)
            content_part = re.sub(r'\s+\}', '}', content_part)
            content_part = re.sub(r',\s+', ',', content_part)
            
            line = ' ' * indent + content_part
            optimized_lines.append(line.rstrip())
        
        content = '\n'.join(optimized_lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip() + '\n'
    
    def _optimize_workflow(self, content: str, patterns: List) -> str:
        """优化工作流 - v2.3 增强"""
        try:
            data = json.loads(content)
        except:
            return content
        
        if 'steps' in data:
            steps = data['steps']
            optimized_steps = []
            prev_step = None
            
            for step in steps:
                step['cache'] = True
                
                if 'depends_on' not in step or not step['depends_on']:
                    step['parallel'] = True
                
                if 'name' in step:
                    step['name'] = re.sub(r'^step_|^action_', '', step['name'], flags=re.IGNORECASE)
                
                if prev_step and step.get('type') == prev_step.get('type'):
                    if 'config' in step and 'config' in prev_step:
                        prev_step['config'].update(step['config'])
                        continue
                
                optimized_steps.append(step)
                prev_step = step
            
            data['steps'] = optimized_steps
        
        if 'version' in data and data['version'] == '1.0':
            del data['version']
        
        if 'timeout' in data and data['timeout'] == 30000:
            del data['timeout']
        
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    def _optimize_directory(self, path: Path, analysis: Dict, patterns: List, auto_fix: bool) -> Dict[str, Any]:
        """优化整个目录"""
        total_original = 0
        total_optimized = 0
        files_processed = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                try:
                    from analyzer.unified_analyzer import UnifiedAnalyzer
                    analyzer = UnifiedAnalyzer()
                    file_analysis = analyzer._analyze_file(file_path)
                    
                    result = self._optimize_file(file_path, file_analysis, patterns, auto_fix)
                    
                    if result['success']:
                        total_original += result['original_tokens']
                        total_optimized += result['optimized_tokens']
                        files_processed += 1
                except:
                    pass
        
        tokens_saved = total_original - total_optimized
        
        return {
            'success': True,
            'path': str(path),
            'files_processed': files_processed,
            'original_tokens': total_original,
            'optimized_tokens': total_optimized,
            'tokens_saved': tokens_saved,
            'saving_percentage': round(tokens_saved / total_original * 100, 2) if total_original > 0 else 0
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """估算Token数量"""
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english = len(text) - chinese
        return int(chinese / 2 + english / 4)


if __name__ == '__main__':
    optimizer = SmartOptimizer()
    import sys
    if len(sys.argv) > 1:
        analysis = {'type': 'code', 'path': sys.argv[1]}
        result = optimizer.optimize(sys.argv[1], analysis, [], auto_fix=False)
        print(json.dumps(result, indent=2))
