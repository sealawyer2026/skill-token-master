#!/usr/bin/env python3
"""智能优化器 - 基于分析结果执行多维度优化"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any


class SmartOptimizer:
    """智能优化器 - 执行实际的Token优化操作"""
    
    def __init__(self):
        self.optimization_log = []
    
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
        """优化提示词"""
        original = content
        
        # 1. 移除冗余程度副词
        content = re.sub(r'非常|特别|十分|极其', '', content)
        
        # 2. 简化客套用语
        content = re.sub(r'请你|请确保|请保证', '', content)
        content = re.sub(r'^请', '', content, flags=re.MULTILINE)
        
        # 3. 简化修饰词
        content = re.sub(r'详细地|仔细地|认真地', '', content)
        
        # 4. 简化概念词
        content = re.sub(r'非常重要的|特别重要的', '关键', content)
        content = re.sub(r'重要的|关键的|核心的', '核心', content)
        
        # 5. 压缩列表格式
        content = re.sub(r'^[•\-\*]\s+', '- ', content, flags=re.MULTILINE)
        
        # 6. 合并连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 7. 移除行尾空格
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        return content.strip()
    
    def _optimize_code(self, content: str, patterns: List) -> str:
        """优化代码"""
        lines = content.split('\n')
        optimized_lines = []
        
        prev_blank = False
        for line in lines:
            stripped = line.rstrip()
            
            # 跳过连续空行
            if not stripped:
                if not prev_blank:
                    optimized_lines.append('')
                    prev_blank = True
                continue
            prev_blank = False
            
            # 移除行尾注释（保留行内注释）
            if stripped.startswith('#') and not stripped.startswith('#!'):
                continue
            
            optimized_lines.append(stripped)
        
        content = '\n'.join(optimized_lines)
        
        # 合并连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 简化简单表达式
        content = re.sub(r'return None', 'return', content)
        
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
