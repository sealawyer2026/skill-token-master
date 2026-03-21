#!/usr/bin/env python3
"""智能优化器 v2.7 - 代码突破版"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any


class SmartOptimizer:
    """智能优化器 - 执行实际的Token优化操作 (v2.10 终极优化版)"""
    
    def __init__(self):
        self.optimization_log = []
        self._cache = {}
        self._compiled_rules = None
        self._init_rules()
    
    def _init_rules(self):
        """初始化并预编译规则"""
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
            # v2.6 单字替换
            (r'因为|由于|鉴于', '因'),
            (r'所以|因此|于是', '故'),
            (r'但是|然而|可是', '但'),
            (r'如果|假如|若是', '若'),
            (r'必须|务必|一定', '须'),
            (r'可以|能够|可能', '可'),
            (r'需要|要求|需求', '需'),
            (r'应该|应当|应', '应'),
            (r'已经|已然|业已', '已'),
            (r'正在|现在|当前', '正'),
            (r'将要|快要|即将', '将'),
            (r'完成|结束|完结', '毕'),
            (r'开始|着手|启动', '始'),
            (r'结果|结局|成果', '果'),
            (r'问题|疑问|难题', '题'),
            (r'方法|方式|办法', '法'),
            (r'情况|情形|状况', '况'),
            (r'内容|内含|包含', '容'),
            (r'信息|消息|资讯', '息'),
            (r'数据|资料|材料', '数'),
            # v2.8 极简压缩
            (r'我们|咱们', '吾'),
            (r'你们|您们', '汝'),
            (r'他们|她们|它们', '其'),
            (r'这个|那个', '此'),
            (r'这里|那里', '此'),
            (r'这样|那样', '如此'),
            (r'什么', '何'),
            (r'怎么', '怎'),
            (r'为什么', '为何'),
            (r'怎么样', '如何'),
            (r'现在', '今'),
            (r'以前|从前', '昔'),
            (r'以后|之后', '后'),
            (r'当时', '当时'),
            (r'到处|处处', '遍'),
            (r'非常|十分|很', '甚'),
            (r'也许|或许|可能', '或'),
            (r'肯定|一定|必须', '必'),
            (r'不要|别', '勿'),
            (r'没有|无', '无'),
            (r'和|与|同', '及'),
            (r'的|之', '之'),
            (r'在|于', '于'),
            (r'对|对于', '对'),
            (r'把|将', '将'),
            (r'被|叫|让', '受'),
            (r'从|自', '自'),
            (r'向|往', '向'),
            (r'为|为了', '为'),
            (r'给|送', '予'),
            (r'说|讲|谈', '曰'),
            (r'看|瞧|望', '视'),
            (r'听|闻', '闻'),
            (r'想|思考', '思'),
            (r'走|行|跑', '行'),
            (r'来|到', '至'),
            (r'做|干|搞', '作'),
            (r'用|使用', '用'),
            (r'有|拥有', '具'),
            (r'是|为', '乃'),
            (r'好|棒|优秀', '佳'),
            (r'坏|差|糟糕', '劣'),
            (r'大|巨大', '巨'),
            (r'小|微小', '微'),
            (r'多|许多', '众'),
            (r'少|很少', '寡'),
            (r'快|迅速', '疾'),
            (r'慢|缓慢', '缓'),
            (r'高|很高', '昂'),
            (r'低|很低', '卑'),
            (r'新|崭新', '崭'),
            (r'旧|陈旧', '陈'),
            (r'长|很长', '冗'),
            (r'短|很短', '短'),
            (r'远|遥远', '遥'),
            (r'近|接近', '近'),
            (r'开|打开', '启'),
            (r'关|关闭', '闭'),
            (r'进|进入', '入'),
            (r'出|出去', '出'),
            (r'上|上面', '上'),
            (r'下|下面', '下'),
            (r'前|前面', '前'),
            (r'后|后面', '后'),
            (r'左|左边', '左'),
            (r'右|右边', '右'),
            (r'东|东方', '东'),
            (r'西|西方', '西'),
            (r'南|南方', '南'),
            (r'北|北方', '北'),
            (r'中|中间', '中'),
            (r'内|里面', '内'),
            (r'外|外面', '外'),
        ]
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
        """优化提示词"""
        cache_key = hash(content)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        for compiled_pattern, repl in self._compiled_rules:
            content = compiled_pattern.sub(repl, content)
        
        content = re.sub(r'^[•\-\*]\s+', '- ', content, flags=re.MULTILINE)
        
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        merged_paragraphs = []
        
        for p in paragraphs:
            if len(p) < 20 and merged_paragraphs:
                merged_paragraphs[-1] += '，' + p
            else:
                merged_paragraphs.append(p)
        
        content = '\n\n'.join(merged_paragraphs)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
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
        
        content = re.sub(r'，\s*，', '，', content)
        content = re.sub(r'。\s*。', '。', content)
        content = re.sub(r'，\s*。', '。', content)
        content = re.sub(r'\s*的\s*', '的', content)
        content = re.sub(r'\s*了\s*', '了', content)
        content = re.sub(r'\s*是\s*', '是', content)
        content = re.sub(r'\s*有\s*', '有', content)
        
        result = content.strip()
        
        if len(self._cache) < 1000:
            self._cache[cache_key] = result
        
        return result
    
    def _optimize_code(self, content: str, patterns: List) -> str:
        """优化代码 - v2.7 代码突破版"""
        # v2.7: 先删除所有docstring
        content = re.sub(r'"""[\s\S]*?"""', '', content)
        content = re.sub(r"'''[\s\S]*?'''", '', content)
        
        lines = content.split('\n')
        optimized_lines = []
        
        prev_blank = False
        
        for line in lines:
            stripped = line.rstrip()
            
            if not stripped:
                if not prev_blank:
                    optimized_lines.append('')
                    prev_blank = True
                continue
            prev_blank = False
            
            content_stripped = stripped.lstrip()
            # v2.7: 删除所有注释
            if content_stripped.startswith('#'):
                if not any(content_stripped.startswith(x) for x in ['#!/', '# -*-']):
                    continue
            
            # v2.7: 删除行内注释
            if '#' in content_stripped:
                content_stripped = content_stripped.split('#')[0].rstrip()
            
            indent = len(line) - len(line.lstrip())
            content_part = content_stripped
            content_part = re.sub(r'\s+', ' ', content_part)
            
            # 布尔简化
            content_part = re.sub(r'if\s+(\w+)\s*==\s*True\s*:', r'if \1:', content_part)
            content_part = re.sub(r'if\s+(\w+)\s*==\s*False\s*:', r'if not \1:', content_part)
            content_part = re.sub(r'if\s+(\w+)\s*!=\s*True\s*:', r'if not \1:', content_part)
            content_part = re.sub(r'if\s+(\w+)\s*!=\s*False\s*:', r'if \1:', content_part)
            content_part = re.sub(r'return\s+None\s*$', 'return', content_part)
            content_part = re.sub(r'==\s*None', 'is None', content_part)
            content_part = re.sub(r'!=\s*None', 'is not None', content_part)
            
            # v2.7: len优化
            content_part = re.sub(r'len\((\w+)\)\s*\>\s*0', r'\1', content_part)
            content_part = re.sub(r'len\((\w+)\)\s*==\s*0', r'not \1', content_part)
            content_part = re.sub(r'not\s+not\s+', '', content_part)
            
            # v2.7: 赋值简化
            content_part = re.sub(r'=\s+', '=', content_part)
            content_part = re.sub(r'\s+=', '=', content_part)
            
            # v2.7: 运算符空格
            content_part = re.sub(r'\+\s+', '+', content_part)
            content_part = re.sub(r'-\s+', '-', content_part)
            content_part = re.sub(r'\*\s+', '*', content_part)
            content_part = re.sub(r'/\s+', '/', content_part)
            content_part = re.sub(r'%\s+', '%', content_part)
            
            # 括号优化
            content_part = re.sub(r'\(\s+', '(', content_part)
            content_part = re.sub(r'\s+\)', ')', content_part)
            content_part = re.sub(r'\[\s+', '[', content_part)
            content_part = re.sub(r'\s+\]', ']', content_part)
            content_part = re.sub(r'\{\s+', '{', content_part)
            content_part = re.sub(r'\s+\}', '}', content_part)
            content_part = re.sub(r',\s+', ',', content_part)
            
            # v2.7: 比较运算符
            content_part = re.sub(r'\s*\>\s*', '>', content_part)
            content_part = re.sub(r'\s*\<\s*', '<', content_part)
            content_part = re.sub(r'\s*\>=\s*', '>=', content_part)
            content_part = re.sub(r'\s*\<=\s*', '<=', content_part)
            content_part = re.sub(r'\s*==\s*', '==', content_part)
            content_part = re.sub(r'\s*!=\s*', '!=', content_part)
            
            line = ' ' * indent + content_part
            optimized_lines.append(line.rstrip())
        
        content = '\n'.join(optimized_lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip() + '\n'
    
    def _optimize_workflow(self, content: str, patterns: List) -> str:
        """优化工作流 - v2.9 增强版"""
        try:
            data = json.loads(content)
        except:
            # 尝试YAML格式
            try:
                import yaml
                data = yaml.safe_load(content)
            except:
                return content
        
        if not isinstance(data, dict):
            return content
        
        # 键名缩写映射
        key_abbreviations = {
            'configuration': 'cfg',
            'parameters': 'params',
            'description': 'desc',
            'environment': 'env',
            'development': 'dev',
            'production': 'prod',
            'application': 'app',
            'database': 'db',
            'username': 'user',
            'password': 'pwd',
            'hostname': 'host',
            'port': 'port',
            'timeout': 'to',
            'retry': 'retry',
            'enable': 'on',
            'disable': 'off',
            'enabled': 'on',
            'disabled': 'off',
            'maximum': 'max',
            'minimum': 'min',
            'current': 'cur',
            'previous': 'prev',
            'next': 'next',
            'index': 'idx',
            'count': 'cnt',
            'number': 'num',
            'total': 'tot',
            'average': 'avg',
            'temporary': 'tmp',
            'variable': 'var',
            'function': 'fn',
            'callback': 'cb',
            'error': 'err',
            'message': 'msg',
            'response': 'res',
            'request': 'req',
            'content': 'ct',
            'default': 'def',
            'optional': 'opt',
            'required': 'req',
            'readonly': 'ro',
            'writeable': 'rw',
        }
        
        def abbreviate_keys(obj):
            if isinstance(obj, dict):
                new_obj = {}
                for k, v in obj.items():
                    new_key = key_abbreviations.get(k, k)
                    new_obj[new_key] = abbreviate_keys(v)
                return new_obj
            elif isinstance(obj, list):
                return [abbreviate_keys(item) for item in obj]
            return obj
        
        data = abbreviate_keys(data)
        
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
                
                # v2.9: 删除默认值
                if 'timeout' in step and step['timeout'] in [30, 30000, 60]:
                    del step['timeout']
                if 'retry' in step and step['retry'] == 3:
                    del step['retry']
                
                if prev_step and step.get('type') == prev_step.get('type'):
                    if 'config' in step and 'config' in prev_step:
                        prev_step['config'].update(step['config'])
                        continue
                
                optimized_steps.append(step)
                prev_step = step
            
            data['steps'] = optimized_steps
        
        # 删除全局默认值
        if 'version' in data and data['version'] in ['1.0', '2.0']:
            del data['version']
        if 'timeout' in data and data['timeout'] in [30, 30000, 60]:
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
