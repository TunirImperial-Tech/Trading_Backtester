import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from src.Strategies import Strategy, MovingAverageCrossover, MeanReversion
from src.Backtest import Backtester
from src.metrics import Metrics

STRATEGY_MAP = {
    "MovingAverageCrossover": MovingAverageCrossover,
    "MeanReversion": MeanReversion,
}

DEFAULT_PARAMS = {
    "MovingAverageCrossover": {"fast": 10, "slow": 50},
    "MeanReversion": {"window": 20, "z_thresh": 2.0},
}

st.set_page_config(page_title="Backtester Dashboard", layout='wide')
st.title("Quant Backtest Engine")

def get_tickers(database: str = "data/prices.db"):
    conn = sqlite3.connect(database)
    tickers = pd.read_sql("SELECT DISTINCT ticker FROM prices ORDER BY ticker", conn)
    conn.close()
    return tickers['ticker'].to_list()

def get_price_df(ticker: str, database: str = "data/prices.db"):
    conn = sqlite3.connect(database)
    df = pd.read_sql("SELECT * FROM prices WHERE ticker = ? ORDER BY date", conn, params=(ticker, ))
    conn.close()
    return df

def get_strategy_map(strategy: type[Strategy] = Strategy):
    return {child.__name__: child for child in strategy.__subclasses__()}

def run_combo(strategy_name: str, ticker: str, params):
    strategy_class = STRATEGY_MAP[strategy_name]
    price_df = get_price_df(ticker)
    strategy = strategy_class(**params)
    backtester = Backtester(strategy)
    trades, equity = backtester.run(price_df)
    metrics = Metrics(trades, equity)
    return metrics.summary(strategy_name, ticker)


st.sidebar.header("Backtest Settings")
ticker = st.sidebar.selectbox("Ticker", get_tickers())
initial_investment = st.sidebar.number_input(
    "Initial Investment (£)", min_value=100, max_value=10000, step=100
)

STRATEGY_MAP = get_strategy_map()
strategy_names = list(STRATEGY_MAP.keys())
strategy_name = st.sidebar.selectbox("Strategy", strategy_names)

strategy_class = STRATEGY_MAP[strategy_name]

if strategy_name == "MovingAverageCrossover":
    fast_window = st.sidebar.slider("Fast Window", 5,50,10)
    slow_window = st.sidebar.slider("Slow Window", 20, 200, 50)

    strategy = strategy_class(fast= fast_window, slow=slow_window)

    st.write(f"Fast: {fast_window}, Slow: {slow_window}")

elif strategy_name == "MeanReversion":
    z_window = st.sidebar.slider("Rolling Window", 10, 100, 20)
    z_threshold = st.sidebar.slider("Z-score Threshold", 1.0, 3.0, 2.0)

    strategy = strategy_class(window = z_window, z_thresh = z_threshold)

    st.write(f"Window: {z_window}, Threshold: {z_threshold}")

price_df = get_price_df(ticker)
backtester = Backtester(strategy)
trades, equity = backtester.run(price_df)
equity['portfolio_value'] = equity['value'] * initial_investment

buys = trades[trades['to_position'] > trades['from_position']]
sells = trades[trades['to_position'] < trades['from_position']]

equity_indexed = equity.set_index('date')['portfolio_value']

buy_points = equity_indexed.loc[buys['date']]
sell_points = equity_indexed.loc[sells['date']]

metrics = Metrics(trades, equity)
summary = metrics.summary(strategy_name, ticker)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Sharpe ratio",  f"{summary['sharpe_ratio']:.2f}")
col2.metric("Max Drawdown", f"{summary['max_drawdown']:.1%}")
col3.metric("Win rate", f"{summary['win_rate']:.1%}")
col4.metric("Total returns", f"{summary['total_return']:.1%}")
col5.metric("Final amount", f"£{equity['portfolio_value'].iloc[-1]:.2f}")

fig = go.Figure()

#Equity line
fig.add_trace(go.Scatter(
    x=equity_indexed.index, y=equity_indexed.values,
    mode='lines', name='Equity', line=dict(color='steelblue') 
))

fig.add_trace(go.Scatter(
    x=buy_points.index, y=buy_points.values, 
    mode='markers', name='Buy', 
    marker=dict(color='green', size=9, symbol='circle')
))

fig.add_trace(go.Scatter(
    x=sell_points.index, y=sell_points.values, 
    mode='markers', name='Sell', 
    marker=dict(color='red', size=9, symbol='circle')
))

fig.update_layout(
    title='Equity curve with trader markers', 
    xaxis_title='Date', yaxis_title='Portfolio Value',
    hovermode='x unified'
)

st.subheader('Equity Curve')
st.plotly_chart(fig, use_container_width=True)

st.subheader('Drawdown')
values = equity.set_index('date')['value']
peak = values.cummax()
drawdown = (values - peak)/peak
st.line_chart(drawdown)

st.subheader("Strategy Comparison")

if st.button("Run Comparision across all tickers"):
    results = []
    for strategy_name in STRATEGY_MAP:
        for ticker in get_tickers():
            summary = run_combo(strategy_name, ticker, DEFAULT_PARAMS[strategy_name])
            results.append(summary)

    comparison_df = pd.DataFrame(results)
    display_df = comparison_df.copy()

    for col in ["total_return", "max_drawdown", "win_rate"]:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.1%}")
    display_df["sharpe_ratio"] = display_df["sharpe_ratio"].apply(lambda x: f"{x:.2f}")

    st.dataframe(display_df)



