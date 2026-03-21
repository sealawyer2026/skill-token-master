# 发布说明

## 关联账户配置

GitHub 和 ClawHub 已设置为关联账户：
- **GitHub**: `sealawyer2026` 
- **ClawHub**: `sealawyer2026` (自动从GitHub导入)

## 发布流程

只需推送到 GitHub，ClawHub 会自动同步：

```bash
# 1. 推送标签到GitHub
git tag v2.10.2
git push origin v2.10.2

# 2. ClawHub自动同步 (约5分钟)
# 查看地址: https://clawhub.ai/sealawyer2026/token-economy-master
```

## 一键发布

```bash
python3 publish.py . 2.10.2
```

或对我说：
> "发布 2.10.2 版本"

## 验证发布

- **GitHub Releases**: https://github.com/sealawyer2026/skill-token-master/releases
- **ClawHub页面**: https://clawhub.ai/sealawyer2026/token-economy-master
