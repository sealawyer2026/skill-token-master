# Token经济大师

**智能Token优化系统 - 越用越聪明**

## 🚀 安装

```bash
# 克隆仓库
git clone https://github.com/sealawyer2026/skill-token-master.git
cd skill-token-master

# 安装依赖
pip install -e .
```

## 📖 使用

### 命令行

```bash
# 分析项目
python3 -m token_master analyze ./my-project/

# 优化项目
python3 -m token_master optimize ./my-project/ --auto-fix

# 自我进化
python3 -m token_master evolve

# 实时监控
python3 -m token_master monitor ./my-project/
```

### Python API

```python
from token_master import TokenEconomyMaster

master = TokenEconomyMaster()

# 分析
result = master.analyze('./my-project/')
print(f"可优化空间: {result['optimization_potential']}%")

# 优化
opt_result = master.optimize('./my-project/', auto_fix=True)
print(f"节省Token: {opt_result['tokens_saved']}")

# 触发进化
master.evolve()
```

## 🧠 自我进化

每完成100次优化，系统会自动进化：
- 学习最佳优化模式
- 更新优化策略库
- 提高优化效率

## 📊 效果

| 项目类型 | 平均节省 |
|---------|---------|
| 提示词 | 40-70% |
| 代码 | 20-50% |
| 工作流 | 30-60% |

## 📝 License

MIT-0
