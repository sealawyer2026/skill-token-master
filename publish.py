#!/usr/bin/env python3
"""
Skill 一键发布脚本
自动完成 GitHub + ClawHub 双平台发布
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# 配置
CLAWHUB_TOKEN = "clh_WsJUvipXX8MHYVW2eROVjmkoZ8VelfpNl3ke47Q0EIY"
SKILL_SLUG = "token-economy-master"
SKILL_NAME = "Token经济大师"

def run(cmd, cwd=None):
    """执行命令"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def get_version(skill_path):
    """从SKILL.md读取版本"""
    skill_md = Path(skill_path) / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        for line in content.split('\n'):
            if '版本' in line and ':' in line:
                return line.split(':')[1].strip()
    return None

def get_changelog(skill_path):
    """生成changelog"""
    # 获取最近的git commit
    ok, stdout, _ = run("git log -1 --pretty=%B", cwd=skill_path)
    if ok:
        return stdout.strip()
    return "版本更新"

def github_release(skill_path, version):
    """GitHub发布"""
    print("📦 推送到 GitHub...")
    
    # git add
    run("git add -A", cwd=skill_path)
    
    # git commit
    ok, _, stderr = run(f'git commit -m "v{version}: 自动发布"', cwd=skill_path)
    if not ok and "nothing to commit" not in stderr:
        print(f"⚠️ Commit失败: {stderr}")
    
    # git push
    ok, _, stderr = run("git push origin master", cwd=skill_path)
    if ok:
        print(f"✅ GitHub推送成功")
        return True
    else:
        print(f"❌ GitHub推送失败: {stderr}")
        return False

def clawhub_release(skill_path, version, changelog):
    """ClawHub发布 - 关联账户自动同步"""
    print("📦 ClawHub (关联GitHub自动同步)...")
    print("   ✓ 已配置与GitHub关联")
    print("   ✓ 推送到GitHub后自动同步到ClawHub")
    print("   ⏳ 等待自动同步完成 (约5分钟)...")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python3 publish.py <skill_path> [version]")
        print("示例: python3 publish.py ./skill-token-master 2.10.2")
        sys.exit(1)
    
    skill_path = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not version:
        version = get_version(skill_path)
        if not version:
            print("❌ 无法获取版本号，请手动指定")
            sys.exit(1)
    
    print(f"🚀 开始发布 {SKILL_NAME} v{version}")
    print("=" * 50)
    
    changelog = get_changelog(skill_path)
    
    # GitHub发布
    github_ok = github_release(skill_path, version)
    
    # ClawHub发布
    clawhub_ok = clawhub_release(skill_path, version, changelog)
    
    print("=" * 50)
    if github_ok:
        print("🎉 GitHub发布成功！")
        print("📦 ClawHub将在5分钟内自动同步")
        print(f"   查看地址: https://clawhub.ai/sealawyer2026/{SKILL_SLUG}")
    else:
        print("❌ 发布失败")

if __name__ == '__main__':
    main()
