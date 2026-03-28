#!/usr/bin/env python3
"""
Token Master v3.6 主引擎
目标: 提示词70-80% | 代码85%+

核心策略:
1. 语义分块压缩
2. 上下文感知
3. 领域特定优化
4. 多轮迭代精炼
"""

import sys
import re
import json
from typing import Dict, Tuple, Optional
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'optimizer'))

from ultra_compressor import UltraCompressor


class TokenMasterV36:
    """Token Master v3.6 主引擎"""
    
    VERSION = "3.6.0"
    TARGET_PROMPT_SAVINGS = 0.75  # 75%目标
    TARGET_CODE_SAVINGS = 0.85    # 85%目标
    
    def __init__(self):
        self.compressor = UltraCompressor()
        self.stats = {
            "total_compressions": 0,
            "avg_prompt_savings": 0.0,
            "avg_code_savings": 0.0
        }
    
    def compress_prompt(self, text: str, iterations: int = 3) -> Tuple[str, Dict]:
        """
        压缩提示词 (多轮迭代)
        
        Args:
            text: 原始提示词
            iterations: 迭代次数
        
        Returns:
            (压缩文本, 统计信息)
        """
        current = text
        total_stats = {
            "iterations": [],
            "original_length": len(text),
            "final_length": 0,
            "total_savings": 0.0
        }
        
        for i in range(iterations):
            current, stats = self.compressor.compress(current)
            total_stats["iterations"].append({
                "round": i + 1,
                "length": stats["compressed_length"],
                "savings": stats["savings_percent"]
            })
            
            # 如果这一轮没有明显改进，停止迭代
            if stats["savings_percent"] < 5:
                break
        
        total_stats["final_length"] = len(current)
        total_stats["total_savings"] = (len(text) - len(current)) / len(text)
        total_stats["total_savings_percent"] = total_stats["total_savings"] * 100
        
        # 更新全局统计
        self._update_stats("prompt", total_stats["total_savings"])
        
        return current, total_stats
    
    def compress_code(self, code: str, aggressive: bool = True) -> Tuple[str, Dict]:
        """
        压缩代码
        
        Args:
            code: 原始代码
            aggressive: 是否激进压缩
        
        Returns:
            (压缩代码, 统计信息)
        """
        original = code
        
        # 步骤1: 移除注释
        code = self._remove_comments(code)
        
        # 步骤2: 简化变量名
        code = self._minify_variables(code)
        
        # 步骤3: 压缩空白
        code = self._compress_whitespace(code)
        
        # 步骤4: 代码特定优化
        if aggressive:
            code = self._aggressive_code_optimization(code)
        
        savings = (len(original) - len(code)) / len(original) if original else 0
        
        self._update_stats("code", savings)
        
        return code, {
            "original_length": len(original),
            "compressed_length": len(code),
            "savings_ratio": savings,
            "savings_percent": savings * 100
        }
    
    def _remove_comments(self, code: str) -> str:
        """移除代码注释"""
        # 移除单行注释
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # 移除多行字符串（文档字符串）
        code = re.sub(r'"""[\s\S]*?"""', '', code)
        code = re.sub(r"'''[\s\S]*?'''", '', code)
        return code
    
    def _minify_variables(self, code: str) -> str:
        """简化变量名"""
        # 简单实现：将长变量名替换为短名称
        # 实际应该使用AST分析
        import keyword
        
        # 找到所有标识符
        identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
        
        # 排除关键字和内置函数
        reserved = set(keyword.kwlist) | {'print', 'len', 'range', 'list', 'dict', 'set'}
        identifiers -= reserved
        
        # 按长度排序，先替换长的
        sorted_ids = sorted(identifiers, key=len, reverse=True)
        
        # 生成短名称
        short_names = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        name_map = {}
        
        for i, old_name in enumerate(sorted_ids):
            if len(old_name) <= 2:  # 已经很短了
                continue
            if i < len(short_names):
                name_map[old_name] = short_names[i]
            else:
                # 使用aa, ab, ac等
                name_map[old_name] = short_names[i // len(short_names)] + short_names[i % len(short_names)]
        
        # 执行替换
        for old_name, new_name in name_map.items():
            code = re.sub(r'\b' + old_name + r'\b', new_name, code)
        
        return code
    
    def _compress_whitespace(self, code: str) -> str:
        """压缩空白字符"""
        # 移除行首行尾空白
        lines = [line.strip() for line in code.split('\n')]
        # 移除空行
        lines = [line for line in lines if line]
        # 用分号连接（如果一行多语句）
        return '\n'.join(lines)
    
    def _aggressive_code_optimization(self, code: str) -> str:
        """激进代码优化"""
        # 简化print语句
        code = re.sub(r'print\s*\(\s*["\'](.+?)["\']\s*\)', r'print(\1)', code)
        
        # 简化列表推导
        code = re.sub(r'for\s+(\w+)\s+in\s+(.+?):', r'for \1 in \2:', code)
        
        return code
    
    def _update_stats(self, type_: str, savings: float):
        """更新统计"""
        self.stats["total_compressions"] += 1
        
        if type_ == "prompt":
            # 移动平均
            n = self.stats["total_compressions"]
            self.stats["avg_prompt_savings"] = (
                self.stats["avg_prompt_savings"] * (n - 1) + savings
            ) / n
        else:
            n = self.stats["total_compressions"]
            self.stats["avg_code_savings"] = (
                self.stats["avg_code_savings"] * (n - 1) + savings
            ) / n
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "version": self.VERSION,
            "total_compressions": self.stats["total_compressions"],
            "avg_prompt_savings": f"{self.stats['avg_prompt_savings'] * 100:.1f}%",
            "avg_code_savings": f"{self.stats['avg_code_savings'] * 100:.1f}%",
            "target_prompt": f"{self.TARGET_PROMPT_SAVINGS * 100:.0f}%",
            "target_code": f"{self.TARGET_CODE_SAVINGS * 100:.0f}%"
        }


# CLI入口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description=f"Token Master v3.6")
    parser.add_argument("--prompt", help="要压缩的提示词")
    parser.add_argument("--code", help="要压缩的代码文件")
    parser.add_argument("--stats", action="store_true", help="显示统计")
    
    args = parser.parse_args()
    
    engine = TokenMasterV36()
    
    if args.stats:
        import json as json_lib
        print(json_lib.dumps(engine.get_stats(), indent=2))
    
    elif args.prompt:
        compressed, stats = engine.compress_prompt(args.prompt)
        print(f"原始长度: {stats['original_length']}")
        print(f"压缩后长度: {stats['final_length']}")
        print(f"总压缩率: {stats['total_savings_percent']:.1f}%")
        print(f"\n压缩结果:\n{compressed}")
    
    elif args.code:
        with open(args.code) as f:
            code = f.read()
        compressed, stats = engine.compress_code(code)
        print(f"原始长度: {stats['original_length']}")
        print(f"压缩后长度: {stats['compressed_length']}")
        print(f"压缩率: {stats['savings_percent']:.1f}%")
        print(f"\n压缩结果:\n{compressed[:500]}...")
    
    else:
        # 运行测试
        print(f"🚀 Token Master v{TokenMasterV36.VERSION}")
        print("=" * 50)
        
        # 测试提示词压缩
        test_prompt = """
        请帮我详细分析一下这段代码的性能瓶颈，并提出具体的优化建议。
        需要考虑时间复杂度、空间复杂度以及内存使用情况。
        同时请提供改进后的代码示例。
        """
        
        print("\n📄 提示词压缩测试:")
        compressed, stats = engine.compress_prompt(test_prompt)
        print(f"  原始: {stats['original_length']} 字符")
        print(f"  压缩: {stats['final_length']} 字符")
        print(f"  节省: {stats['total_savings_percent']:.1f}%")
        print(f"  结果: {compressed[:80]}...")
        
        # 测试代码压缩
        test_code = '''
def calculate_statistics(data_list):
    """计算列表的统计信息"""
    total_sum = sum(data_list)
    count = len(data_list)
    average = total_sum / count if count > 0 else 0
    
    # 计算方差
    variance = sum((x - average) ** 2 for x in data_list) / count
    
    return {
        'sum': total_sum,
        'count': count,
        'average': average,
        'variance': variance
    }
        '''
        
        print("\n💻 代码压缩测试:")
        compressed, stats = engine.compress_code(test_code)
        print(f"  原始: {stats['original_length']} 字符")
        print(f"  压缩: {stats['compressed_length']} 字符")
        print(f"  节省: {stats['savings_percent']:.1f}%")
        
        print("\n" + "=" * 50)
        print(json.dumps(engine.get_stats(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
