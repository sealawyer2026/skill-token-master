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
    """ClawHub发布"""
    print("📦 上传到 ClawHub...")
    
    # 构建curl命令
    files = []
    for f in ["SKILL.md", "README.md", "__main__.py", "__init__.py"]:
        if (Path(skill_path) / f).exists():
            files.append(f"-F 'files=@{f};type=text/markdown'")
    
    # 添加子目录文件
    for pattern in ["analyzer/*.py", "optimizer/*.py", "learner/*.py", "monitor/*.py", "tests/*.py"]:
        for f in Path(skill_path).glob(pattern):
            files.append(f"-F 'files=@{f.relative_to(skill_path)};type=text/x-python'")
    
    payload = json.dumps({
        "slug": SKILL_SLUG,
        "displayName": SKILL_NAME,
        "version": version,
        "changelog": changelog,
        "acceptLicenseTerms": True,
        "tags": ["token", "optimization", "ai"]
    })
    
    cmd = f"""curl -s -X POST \
      -H "Authorization: Bearer {CLAWHUB_TOKEN}" \
      -F 'payload={payload}' \
      {" ".join(files)} \
      https://clawhub.ai/api/v1/skills"""
    
    ok, stdout, stderr = run(cmd, cwd=skill_path)
    
    if ok and '"ok":true' in stdout:
        result = json.loads(stdout)
        print(f"✅ ClawHub上传成功")
        print(f"   Skill ID: {result.get('skillId')}")
        print(f"   Version ID: {result.get('versionId')}")
        return True
    else:
        print(f"❌ ClawHub上传失败: {stdout or stderr}")
        return False

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
    if github_ok and clawhub_ok:
        print("🎉 双平台发布成功！")
    elif github_ok:
        print("⚠️ GitHub成功，ClawHub失败")
    elif clawhub_ok:
        print("⚠️ ClawHub成功，GitHub失败")
    else:
        print("❌ 双平台发布失败")

if __name__ == '__main__':
    main()
