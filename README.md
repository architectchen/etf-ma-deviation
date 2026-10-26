# ETF MA Deviation

基于 ETF 日线收盘价与移动平均线（MA）偏离度的研究/回测项目。项目包含两个
信号扫描 notebook 和一个 AKQuant 回测脚本，用于观察“价格相对均线明显偏离”
时的潜在买入/卖出时机。

> 本项目仅用于研究和回测验证，不构成任何投资建议。

## 策略逻辑

- MA：对收盘价计算固定窗口的简单移动平均。
- 偏离度：`close / MA - 1`。
- 买入：偏离度低于负阈值时触发买入信号。
- 卖出：偏离度高于正阈值时触发卖出信号。
- 回测默认按 A 股 ETF 规则处理：T+1、100 份一手、手续费和滑点。
- 回测从均线首次有效（第 `moving_average_window` 条）的交易日开始，之前
  的行情仅用于均线预热。

## 项目结构

```text
etf_ma_deviation_buy_signal.ipynb       # 只做买入信号扫描、表格和图表
etf_ma_deviation_buy_sell_signal.ipynb  # 买入/卖出信号扫描和图表
etf_ma_deviation_buy_sell_backtesting.py # AKQuant 回测脚本
```

## 环境要求

- Python 3.11（当前验证版本为 3.11.15）
- 可访问 AKShare 数据源及其代理服务的网络环境

## 安装

```bash
python3.11 -m venv .venv
source .venv/bin/activate

# 只安装运行依赖
python -m pip install -r requirements.txt

# 开发环境：额外安装 ruff、black、isort
python -m pip install -r requirements-dev.txt
```

## 配置

脚本和 notebook 顶部的主要配置项（`initial_cash` 仅回测脚本使用）：

| 配置                         | 说明         | 默认值      |
| ---------------------------- | ------------ | ----------- |
| `symbol`                   | ETF 代码     | `515180`  |
| `moving_average_window`    | 均线窗口     | `120`     |
| `buy_deviation_threshold`  | 买入偏离阈值 | `0.07`    |
| `sell_deviation_threshold` | 卖出偏离阈值 | `0.10`    |
| `initial_cash`             | 回测初始资金 | `10000.0` |

均线窗口必须为正整数；数据长度不足 `moving_average_window` 条时脚本会报错。

## 运行

```bash
# 启动 Jupyter
.venv/bin/jupyter lab

# 运行回测（会联网获取数据，并生成/打开 HTML 报告）
.venv/bin/python etf_ma_deviation_buy_sell_backtesting.py

# 无头执行 notebook，并将输出写回 notebook
.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  etf_ma_deviation_buy_sell_signal.ipynb

# 不修改源 notebook
.venv/bin/jupyter nbconvert --to notebook --execute \
  etf_ma_deviation_buy_signal.ipynb --output /tmp/etf_ma_deviation_buy_signal.ipynb
```

## 输出

回测会在仓库根目录生成：

- `{symbol}_ma_deviation_report.html`（绩效报告，包含 `BUY_HOLD` 基准）
- `{symbol}_ma_deviation_review.html`

这些文件属于生成产物，已在 `.gitignore` 中忽略；需要时重新运行脚本生成。

交易复盘图只标注已平仓交易（`trades_df`），当前未平仓头寸不会被额外标注。

## 代码检查

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/black --check etf_ma_deviation_buy_sell_backtesting.py
.venv/bin/isort --check-only --diff etf_ma_deviation_buy_sell_backtesting.py
```

## 测试

当前项目没有自动化测试，主要通过运行脚本和 notebook 进行验证。后续引入
pytest 时，建议使用确定性的合成行情数据，避免依赖实时网络数据。

## 数据与网络

数据通过 AKShare 实时获取，执行前请确认网络和代理配置可用。不要在代码、
notebook 或日志中新增明文凭据；新的代理配置建议使用环境变量管理。

## 免责声明

本项目及其输出仅用于技术研究和策略验证，不构成投资建议。历史回测结果不代表
未来收益，使用前请自行评估风险。
