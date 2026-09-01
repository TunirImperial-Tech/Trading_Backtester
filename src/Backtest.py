import pandas as pd
from .Strategies import Strategy

class Backtester:
    def __init__(self, strategy: Strategy, cost_bps: float = 5.0):
        self.strategy = strategy
        self.cost_bps = cost_bps

    def run(self, price_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        price_df = price_df.reset_index(drop=True)
        position = 0.0
        portfolio_value = 1.0
        trades, equity = [], []

        for i in range(len(price_df)):
            signal = self.strategy.generate_signal(price_df, i)
            price_today = price_df.iloc[i]["close"]

            if i > 0:
                price_yesterday = price_df.iloc[i-1]['close']
                daily_return = (price_today/price_yesterday) - 1
                portfolio_value *= (1 + position * daily_return)

            if signal != position:
                cost = abs(signal - position) * (self.cost_bps/10000)
                portfolio_value *= (1-cost)
                trades.append({'date': price_df.iloc[i]['date'], 
                               'from_position': position, 
                               'to_position': signal, 
                               'price': price_today, 
                               'cost': cost * portfolio_value})
                position = signal

            equity.append({'date': price_df.iloc[i]['date'],
                           'position': position, 
                           'value': portfolio_value})

        return pd.DataFrame(trades), pd.DataFrame(equity)