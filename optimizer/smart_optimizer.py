#!/usr/bin/env python3
"""智能优化器 v2.1 - 增强版，提升压缩率"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any


class SmartOptimizer:
    """智能优化器 - 执行实际的Token优化操作 (v2.1 增强版)"""
    
    def __init__(self):
        self.optimization_log = []
        # v2.1 新增：更全面的优化规则
        self.prompt_rules = [
            # 程度副词
            (r'非常|特别|十分|极其|格外', ''),
            # 客套用语
            (r'请你|请确保|请保证|请仔细|请认真', ''),
            (r'^请', '', re.MULTILINE),
            # 修饰词
            (r'详细地|仔细地|认真地|全面地|深入地', ''),
            # 概念词简化
            (r'非常重要的|特别重要的', '关键'),
            (r'重要的|关键的|核心的', '核心'),
            (r'是不是|能否|可不可以', '是否'),
            (r'以及|还有|并且', '和'),
            # 冗余短语
            (r'所有的|全部的', '所有'),
            (r'每一个|每一处', '每个'),
            (r'进行一个|做一个', '进行'),
            (r'完成一个', '完成'),
            # 重复词汇
            (r'分析分析|研究研究|看看', '分析'),
            (r'考虑一下|想一想', '考虑'),
            (r'处理一下|弄一下', '处理'),
        ]
    
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
        """优化提示词 - v2.1 增强版"""
        # v2.1: 按顺序应用所有规则
        for rule in self.prompt_rules:
            if len(rule) == 3:
                pattern, repl, flags = rule
                content = re.sub(pattern, repl, content, flags=flags)
            else:
                pattern, repl = rule
                content = re.sub(pattern, repl, content)
        
        # 压缩列表格式
        content = re.sub(r'^[•\-\*]\s+', '- ', content, flags=re.MULTILINE)
        
        # 合并连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 移除行尾空格
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # v2.1: 检测并简化重复句子
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
        
        return content.strip()
    
    def _optimize_code(self, content: str, patterns: List) -> str:
        """优化代码 - v2.1 增强版"""
        lines = content.split('\n')
        optimized_lines = []
        
        prev_blank = False
        in_multiline_string = False
        
        for line in lines:
            stripped = line.rstrip()
            
            # v2.1 fix: 更准确地检测多行字符串
            triple_double = stripped.count('"""')
            triple_single = stripped.count("'''")
            
            # 如果行内有奇数个"""或'''，则切换状态
            if triple_double % 2 == 1 or triple_single % 2 == 1:
                in_multiline_string = not in_multiline_string
                if in_multiline_string:
                    continue  # 进入文档字符串，跳过开始行
                else:
                    continue  # 退出文档字符串，跳过结束行
            
            if in_multiline_string:
                continue  # 在文档字符串内部，跳过
            
            # 跳过连续空行 (最多保留1个)
            if not stripped:
                if not prev_blank:
                    optimized_lines.append('')
                    prev_blank = True
                continue
            prev_blank = False
            
            # v2.1 fix: 移除所有注释行（包括有缩进的）
            # 使用 lstrip 移除前导空格后检查
            content_stripped = stripped.lstrip()
            if content_stripped.startswith('#'):
                # 检查是否是 shebang 或编码声明
                if not any(content_stripped.startswith(x) for x in ['#!/', '# -*-']):
                    continue
            
            # v2.1: 简化空格
            # 将多个空格替换为单个（保留缩进）
            indent = len(line) - len(line.lstrip())
            content_part = line.lstrip()
            # 简化中间的空格
            content_part = re.sub(r'\s+', ' ', content_part)
            line = ' ' * indent + content_part
            
            optimized_lines.append(line.rstrip())
        
        content = '\n'.join(optimized_lines)
        
        # v2.1: 更多代码简化
        # 简化 return None
        content = re.sub(r'return\s+None\s*$', 'return', content, flags=re.MULTILINE)
        # 简化 if x == True: → if x:
        content = re.sub(r'if\s+(\w+)\s*==\s*True\s*:', r'if \1:', content)
        # 简化 if x == False: → if not x:
        content = re.sub(r'if\s+(\w+)\s*==\s*False\s*:', r'if not \1:', content)
        # 简化列表/字典的空格
        content = re.sub(r'\[\s+', '[', content)
        content = re.sub(r'\s+\]', ']', content)
        content = re.sub(r'\{\s+', '{', content)
        content = re.sub(r'\s+\}', '}', content)
        
        # 合并连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip() + '\n'
    
    def _optimize_workflow(self, content: str, patterns: List) -> str:
        """优化工作流"""
        try:
            data = json.loads(content)
        except:
            return content
        
        # 启用所有步骤的缓存
        if 'steps' in data:
            for step in data['steps']:
                step['cache'] = True
                # 如果没有依赖，标记为可并行
                if 'depends_on' not in step or not step['depends_on']:
                    step['parallel'] = True
        
        # 压缩JSON（移除多余空格）
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    def _optimize_directory(self, path: Path, analysis: Dict, patterns: List, auto_fix: bool) -> Dict[str, Any]:
        """优化整个目录"""
        total_original = 0
        total_optimized = 0
        files_processed = 0
        
        for file_path in path.rglob('*'):
            if file_path.is_file():
                try:
                    # 重新分析每个文件
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
