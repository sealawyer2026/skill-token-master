#!/usr/bin/env python3
"""
多轮迭代评测脚本
记录每轮迭代的效果提升
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def run_evaluation():
    """运行评测并解析结果"""
    result = subprocess.run(
        ['python3', 'tests/deep_evaluate.py'],
        capture_output=True,
        text=True
    )
    
    # 解析结果
    output = result.stdout
    
    # 提取关键数据
    prompt_saving = None
    code_saving = None
    
    for line in output.split('\n'):
        if '平均节省:' in line and '测试1' not in line:
            try:
                prompt_saving = float(line.split(':')[1].strip().replace('%', ''))
            except:
                pass
        if '代码压缩:' in line and '节省' in line:
            try:
                code_saving = float(line.split('节省')[1].split('%')[0].strip())
            except:
                pass
    
    return {
        'success': result.returncode == 0,
        'prompt_saving': prompt_saving,
        'code_saving': code_saving,
        'output': output
    }


def main():
    print("="*70)
    print("🔄 Token经济大师 - 多轮迭代评测")
    print("="*70)
    
    # 当前版本基线
    print("\n📊 当前版本基线 (v2.2.0)")
    print("-"*70)
    
    result = run_evaluation()
    if result['success']:
        print(f"  提示词优化: {result['prompt_saving']:.1f}%")
        print(f"  代码优化: {result['code_saving']:.1f}%")
        print(f"  状态: ✅ 通过")
    else:
        print(f"  状态: ❌ 失败")
        return
    
    print("\n" + "="*70)
    print("📋 迭代计划")
    print("="*70)
    print("""
  第3轮: 工作流优化增强
    - 目标: 工作流节省从30%提升到40%
    - 方法: 优化JSON结构，合并重复步骤
    
  第4轮: 智能压缩算法
    - 目标: 增加语义压缩，保留含义下极致压缩
    - 方法: 同义词替换，句子重组
    
  第5轮: 性能与稳定性
    - 目标: 优化速度<0.5ms，100%测试通过
    - 方法: 算法优化，缓存机制
""")
    
    print("="*70)
    print("✅ 基线评测完成，准备开始迭代")
    print("="*70)


if __name__ == '__main__':
    main()
