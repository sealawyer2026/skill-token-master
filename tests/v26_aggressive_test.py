#!/usr/bin/env python3
"""第6轮效果验证"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from optimizer.smart_optimizer import SmartOptimizer

optimizer = SmartOptimizer()

# 激进测试代码
test_code_aggressive = '''
def process_data(data_list):
    """
    这是一个非常重要的处理函数
    用于处理数据列表
    """
    # 检查结果是否为空
    if len(data_list) == 0:
        return None
    
    # 遍历处理每一个元素
    result = []
    for item in data_list:
        # 检查是否有效
        if item == True:
            result.append(item)
        elif item == False:
            continue
        else:
            pass
    
    # 返回结果
    if len(result) > 0:
        return result
    else:
        return None


def check_value(x):
    """检查值"""
    if x:
        return True
    else:
        return False


def another_check(y):
    """另一个检查"""
    if y:
        return False
    return True
'''

print("="*60)
print("🚀 第6轮激进优化测试")
print("="*60)

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(test_code_aggressive)
    f.flush()
    
    result = optimizer.optimize(f.name, {'type': 'code'}, [], auto_fix=False)
    
    print(f"\n原始Token: {result['original_tokens']}")
    print(f"优化后: {result['optimized_tokens']}")
    print(f"节省: {result['saving_percentage']}%")
    
    if result.get('optimized_content'):
        print("\n优化后代码:")
        print("-"*40)
        print(result['optimized_content'])
