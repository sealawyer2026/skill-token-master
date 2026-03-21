#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def run_tests():
    """运行测试套件"""
    result = subprocess.run(
        ['python3', 'tests/test_master.py'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def run_evaluation():
    """运行深度评测"""
    result = subprocess.run(
        ['python3', 'tests/deep_evaluate.py'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def count_tokens():
    """统计代码Token数"""
    total = 0
    for py_file in Path('.').rglob('*.py'):
        if '__pycache__' not in str(py_file) and 'data' not in str(py_file):
            content = py_file.read_text()
            chinese = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            english = len(content) - chinese
            total += int(chinese / 2 + english / 4)
    return total

def iterate():
    """执行迭代优化"""
    print("="*60)
    print("🔄 Token经济大师 - 迭代优化")
    print("="*60)

    initial_tokens = count_tokens()
    print(f"\n初始代码Token数: {initial_tokens}")

    print("\n1️⃣ 运行基础测试...")
    if run_tests():
        print(" ✅ 基础测试通过")
    else:
        print(" ❌ 基础测试失败")
        return False

    print("\n2️⃣ 运行深度评测...")
    if run_evaluation():
        print(" ✅ 深度评测通过")
    else:
        print(" ❌ 深度评测失败")
        return False

    final_tokens = count_tokens()
    print(f"\n最终代码Token数: {final_tokens}")
    print(f"优化节省: {initial_tokens - final_tokens} tokens ({(initial_tokens - final_tokens)/initial_tokens*100:.1f}%)")

    print("\n" + "="*60)
    print("✅ 迭代优化完成，质量达标！")
    print("="*60)

    return True

if __name__ == '__main__':
    success = iterate()
    sys.exit(0 if success else 1)
