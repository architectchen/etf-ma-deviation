# AGENTS.md

## Repository Overview

Standalone Python 3.11 research/backtesting workspace for ETF moving-average
deviation signals. There is no package build or CI here; `pyproject.toml` is
only for ruff/black/isort configuration, and the directory is not currently a
git repository.

- `etf_ma_deviation_buy_signal.ipynb` - buy-only signal scan, table, and chart.
- `etf_ma_deviation_buy_sell_signal.ipynb` - buy/sell signal scan and chart.
- `etf_ma_deviation_buy_sell_backtesting.py` - AKQuant backtest of the buy/sell
  rules; writes an HTML report with a `BUY_HOLD` benchmark and a review file.
- `README.md` - setup, usage, configuration, outputs, and disclaimer.
- `requirements.txt` / `requirements-dev.txt` - pinned runtime and development
  dependencies.
- `pyproject.toml` - formatting/linting configuration only.
- `.gitignore` - excludes environments, caches, secrets, and generated reports.
- `515180_*.html` - generated backtest artifacts, ignored by git. Do not edit.
- `.venv/`, `.ruff_cache/`, `.ipynb_checkpoints/` - local/generated state. Do not
  edit, lint, or treat as source.

Domain conventions: A-share ETF data from AKShare, forward-adjusted (`qfq`)
daily bars, Chinese source column names, 100-share lots, and T+1 settlement.

No Cursor rules (`.cursorrules`, `.cursor/rules/`) or Copilot instructions
(`.github/copilot-instructions.md`) exist as of this writing. If added, follow
them and update this file.

## Environment

Use the checked-in virtual environment; do not install globally.

```bash
source .venv/bin/activate          # optional
.venv/bin/python --version         # Python 3.11.15

# Runtime dependencies
.venv/bin/python -m pip install -r requirements.txt

# Development dependencies (includes runtime)
.venv/bin/python -m pip install -r requirements-dev.txt
```

Runtime dependencies are pinned in `requirements.txt`;
`requirements-dev.txt` adds `ruff`, `black`, and `isort`. There is no pytest
installation or test suite yet. Inspect `.venv/bin/pip list` before assuming a
dependency exists. Install new dependencies into `.venv` only, and update the
appropriate requirements file.

## Commands

### Run

```bash
# Backtest (fetches live data and opens the review in a browser)
.venv/bin/python etf_ma_deviation_buy_sell_backtesting.py

# Start Jupyter
.venv/bin/jupyter lab

# Execute a notebook headlessly (writes outputs back into the nb)
.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  etf_ma_deviation_buy_sell_signal.ipynb

# Omit --inplace and pass --output /tmp/out.ipynb to leave the source untouched.
```

Execution needs network access to the AKShare proxy. Data is fetched live and
the backtest writes `{symbol}_..._report.html` /
`{symbol}_ma_deviation_review.html` in the repo root. In headless environments
use `show=False` for plots/reports.

### Lint and format

Ruff is canonical and covers both `.py` and `.ipynb`; exclusions live in
`pyproject.toml`.

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .

# Apply fixes
.venv/bin/ruff check . --fix
.venv/bin/ruff format .
```

`black` and `isort` are installed and currently pass; use them for `.py` only.

```bash
.venv/bin/black --check etf_ma_deviation_buy_sell_backtesting.py
.venv/bin/isort --check-only --diff etf_ma_deviation_buy_sell_backtesting.py
```

### Tests

There is no test suite, framework, or config. Do not invent one casually;
command-line and notebook execution are the current validation path. If
adding pytest, install it into `.venv`, add it to `requirements-dev.txt`, and
use:

```bash
.venv/bin/python -m pytest -q                                    # whole suite
.venv/bin/python -m pytest tests/test_signals.py::test_buy_signal -q  # single test
.venv/bin/python -m unittest tests.test_signals.TestSignals.test_buy_signal
```

Prefer deterministic synthetic fixtures over live network calls. Before
finishing, run `ruff check`, `ruff format --check`, and the affected script or
notebook. Restart the kernel and run all cells when validating a notebook.

## Code Style

### Imports and formatting

- PEP 8, 4-space indentation, 88-character lines, double quotes, trailing
  commas; match Black/Ruff formatting.
- Order: standard library, blank line, third-party, blank line, local absolute
  imports. One import per line; no wildcard imports.
- Keep notebook imports in the first cells, not scattered through analysis.
- Preserve Unicode/Chinese text; do not re-encode files or reformat generated
  HTML, saved notebook outputs, or checkpoints unless explicitly required.

### Types and naming

- The codebase is untyped; type hints are optional. Add lightweight hints
  (`pd.DataFrame`, `pd.Series`, `float`, `str`, `None`) to reusable helpers, not
  scratch cells.
- Target Python 3.11; modern syntax such as `float | None` is fine in `.py`.
  Do not add typing dependencies.
- Use `snake_case` for variables/functions/knobs (`moving_average_window`,
  `buy_deviation_threshold`), `PascalCase` for classes (`DeviationStrategy`),
  and `UPPER_SNAKE_CASE` only for true constants. The lowercase top-of-file
  config block is intentional.
- Prefix private helpers with `_`; name files by topic (`etf_ma_deviation_*.py`).
- Keep AKShare Chinese columns (`日期`, `开盘`, `最高`, `最低`, `收盘`, `成交量`,
  `MA`, `偏离度`) until the AKQuant boundary, then rename to lowercase English
  OHLCV (`date`, `open`, `high`, `low`, `close`, `volume`).
- Keep user-facing titles and prints in Chinese when surrounding text is
  Chinese; internal names and comments may stay English.

### Data and signal rules

- Fetch with `ak.fund_etf_hist_em(symbol=..., period="daily",
  start_date="19700101", end_date=date.today().strftime("%Y%m%d"),
  adjust="qfq")`.
- Convert `日期` via `pd.to_datetime`, sort ascending by date, and
  `reset_index(drop=True)`.
- MA: `rolling(window=..., min_periods=window).mean()`; deviation:
  `close / MA - 1`. In pandas scans, drop rows missing MA/deviation before
  generating signals; for AKQuant incremental indicators, keep full history and
  use `start_time` to preserve warmup bars.
- Buy when deviation is below the negative threshold; sell when above the
  positive one. Keep signs and thresholds synchronized across both notebooks
  and the script.
- Backtest assumptions: commission `0.0003`, 0.1% percent slippage, T+1,
  `lot_size=100`, ~95% cash deployment, quantity floored to 100-share lots:
  `int(cash * 0.95 / price / 100) * 100`.
- Prefer the incremental `aq.SMA(window)` indicator (`warmup_bars=window`) and
  compute deviation in `on_bar` from `bar.close / ma - 1`. Keep the full price
  history and use `start_time` so pre-start bars warm the indicator; do not drop
  warmup rows before an incremental indicator. Use `PrecomputedIndicator` only
  for backtest-only vectorized cases. Do not mutate the raw dataframe; derive
  with `.copy()` and explicit filtering.
- `result.viz.review()` markers come from `trades_df`, which contains closed
  trades only; the current script does not annotate open positions. If
  open-position markers are added, merge review-only entry rows from
  `positions_df` and `executions_df` with `exit_time=pd.NaT`, then restore the
  original `trades_df` after rendering. Normalize tz-aware trade times to local
  naive before rendering so markers align with naive daily bars. Do not fake
  exits or use signal dates as fill dates.
- The performance report accepts `benchmark=`; pass a date-indexed
  `BUY_HOLD` daily-return series aligned to the backtest start date.

### Error handling and I/O

- Fail fast. Let data/network/schema errors propagate; never add empty or silent
  `except` blocks.
- Catch only expected failures (for example a deliberate retry/fallback) and
  preserve context in the error message.
- Validate before I/O: positive moving-average window, sensible thresholds,
  non-empty symbol, expected columns. Raise `ValueError`/`RuntimeError` with
  actionable messages.
- Keep the AKShare proxy setup centralized (retries plus `fast=True`); do not
  duplicate network settings.
- Never add credentials, tokens, or secrets to source, notebooks, or logs. The
  existing proxy token is hardcoded; do not copy it into new files. Use
  environment variables for new credentials.
- Use `show=False` for generated reports in non-interactive runs. Do not edit
  generated HTML; regenerate it.

### Notebook hygiene

- Notebooks must run top-to-bottom from a clean kernel; avoid stale state.
- Preserve existing outputs during code-only edits unless asked to clear or
  re-execute.
- Both notebooks duplicate fetch/MA logic. If a formula or signal rule changes,
  update both notebooks and the backtest script.
- Never edit `.ipynb_checkpoints/`; those are Jupyter recovery copies.
