import os
from datetime import date

import akquant as aq
import akshare as ak
import akshare_proxy_patch
import pandas as pd
from akquant import Strategy
from dotenv import load_dotenv

load_dotenv()
auth_token = os.getenv("AKSHARE_PROXY_AUTH_TOKEN")

akshare_proxy_patch.install_patch(
    "101.201.173.125",
    auth_token=auth_token,
    retry=30,
    hook_domains=["push2his.eastmoney.com"],
    fast=True,
)

# Customization
symbol = "515180"
moving_average_window = 120
buy_deviation_threshold = 0.07
sell_deviation_threshold = 0.10
initial_cash = 10_000.0

if moving_average_window <= 0:
    raise ValueError("moving_average_window 必须为正整数")

df = ak.fund_etf_hist_em(
    symbol=symbol,
    period="daily",
    start_date="19700101",
    end_date=date.today().strftime("%Y%m%d"),
    adjust="qfq",
)
df["日期"] = pd.to_datetime(df["日期"])
df = df.sort_values("日期").reset_index(drop=True)

df_bt = df.rename(
    columns={
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
    }
).copy()

if len(df_bt) < moving_average_window:
    raise ValueError(
        f"数据不足: 需要至少 {moving_average_window} 条，实际 {len(df_bt)} 条"
    )

start_date = df_bt["date"].iloc[moving_average_window - 1]
start_time = start_date.strftime("%Y-%m-%d")


class DeviationStrategy(Strategy):
    def on_start(self):
        self.ma = self.I(
            aq.SMA(moving_average_window),
            name="MA",
            warmup_bars=moving_average_window,
        )

    def on_bar(self, bar):
        ma = self.ma[0]
        if ma is None:
            return

        deviation = bar.close / ma - 1
        position = self.get_position(bar.symbol)
        if position == 0 and deviation < -buy_deviation_threshold:
            qty = int(self.ctx.cash / bar.close / 100) * 100
            if qty > 0:
                self.buy(symbol=bar.symbol, quantity=qty)
        elif position > 0 and deviation > sell_deviation_threshold:
            self.close_position(symbol=bar.symbol)


result = aq.run_backtest(
    data=df_bt,
    strategy=DeviationStrategy,
    symbols=symbol,
    initial_cash=initial_cash,
    commission_rate=0.0003,
    slippage={"type": "percent", "value": 0.001},
    t_plus_one=True,
    lot_size=100,
    start_time=start_time,
    show_progress=True,
)

benchmark_returns = (
    df_bt.loc[df_bt["date"] >= start_date]
    .set_index("date")["close"]
    .pct_change()
    .fillna(0.0)
    .rename("BUY_HOLD")
)
result.viz.report(
    filename=f"{symbol}_ma_deviation_report.html",
    show=False,
    benchmark=benchmark_returns,
)
review_path = result.viz.review(
    market_data=df_bt,
    title=f"AKQuant 交易复盘 - {symbol}",
    filename=f"{symbol}_ma_deviation_review.html",
    show=True,
)
