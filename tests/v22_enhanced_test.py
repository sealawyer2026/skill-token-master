#!/usr/bin/env python3
"""v2.2 增强效果测试"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from optimizer.smart_optimizer import SmartOptimizer

print("="*60)
print("🆚 v2.2 增强效果对比")
print("="*60)

optimizer = SmartOptimizer()

# 测试更复杂的提示词
test_prompts = [
    {
        'name': '复杂冗余句式',
        'input': '''请你仔细地、认真地分析一下，我们是否可以考虑一下这个方案，
并且你能不能深入地研究研究一下这个问题，详细地检查一下每一个细节。''',
    },
    {
        'name': '多重客套',
        'input': '''请你帮忙看看，请确保质量，请保证准确性，请仔细检查每一个地方，
非常感谢你的帮助，麻烦你了。''',
    },
    {
        'name': '重复概念',
        'input': '''这是一个非常重要的、特别关键的核心问题，
我们需要全面地、充分地、彻底地分析一下。''',
    },
    {
        'name': '口语化冗余',
        'input': '''能不能搞一个方案出来，弄一下这个数据，
看看情况怎么样，想想怎么处理。''',
    }
]

print("\n📋 提示词优化测试")
print("-"*60)

total_original = 0
total_optimized = 0

for case in test_prompts:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(case['input'])
        f.flush()
        
        result = optimizer.optimize(f.name, {'type': 'prompt'}, [], auto_fix=False)
        
        original = result['original_tokens']
        saved = result['saving_percentage']
        
        total_original += original
        total_optimized += result['optimized_tokens']
        
        print(f"\n  {case['name']}:")
        print(f"    原始: {original} tokens")
        print(f"    节省: {saved}%")

avg_saving = (1 - total_optimized/total_original) * 100
print(f"\n  📊 平均节省: {avg_saving:.1f}%")

# 测试代码优化增强
test_code = '''def process_data(data_list):
    """处理数据函数"""
    # 检查结果是否为空
    if data_list == None:
        return None
    
    # 遍历处理每一个元素
    result = []
    for item in data_list:
        # 检查是否有效
        if item == True:
            result.append(item)
        elif item == False:
            continue
    
    return result


class DataProcessor:
    """数据处理器类"""
    
    def __init__(self):
        # 初始化数据
        self.data = []
    
    def add(self, item):
        # 添加元素
        if item != None:
            self.data.append(item)
'''

print("\n\n📋 代码优化测试")
print("-"*60)

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(test_code)
    f.flush()
    
    result = optimizer.optimize(f.name, {'type': 'code'}, [], auto_fix=False)
    
    print(f"\n  原始: {result['original_tokens']} tokens")
    print(f"  优化后: {result['optimized_tokens']} tokens")
    print(f"  节省: {result['saving_percentage']}%")
    
    print("\n  优化后代码预览:")
    if result.get('optimized_content'):
        lines = result['optimized_content'].split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"    {line}")

print("\n" + "="*60)
print("✅ v2.2 增强效果测试完成")
print("="*60)
