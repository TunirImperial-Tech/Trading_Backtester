import numpy as np
import pandas as pd

class Metrics:
    def __init__(self, trades: pd.DataFrame, equity: pd.DataFrame):
        self.trades = trades
        self.equity = equity

    def sharpeRatio(self):
        returns = self.equity['value'].pct_change().dropna()

        if returns.std() == 0.0:
            return 0.0

        sharpe = (returns.mean()/returns.std()) * np.sqrt(252)
        return sharpe

    def maxDrawdown(self):
        values = self.equity['value']

        peak = values.cummax()
        drawdown = (values - peak)/peak
        mdd = drawdown.min()
        return abs(mdd)

    def trade_pnls(self):
        if self.trades.empty:
            return pd.Series(dtype=float)

        equity = self.equity.set_index('date')
        trade_dates = list(self.trades['date']) + [equity.index[-1]]

        pnls = []
        for i in range(len(self.trades)):
            entry_date = trade_dates[i]
            exit_date = trade_dates[i+1]
            position_held = self.trades.iloc[i]['to_position']

            if position_held == 0:
                continue

            entry_value = equity.loc[entry_date, 'value']
            exit_value = equity.loc[exit_date, 'value']
            segment_return = (exit_value/entry_value) - 1
            pnls.append(segment_return)

        return pd.Series(pnls)

    def win_rate(self)-> float:
        pnls = self.trade_pnls()
        if pnls.empty:
            return 0.0
        return (pnls>0).mean()

    def avg_win_loss(self)-> dict:
        pnls = self.trade_pnls()
        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]

        return {
            'avg_win': wins.mean() if not wins.empty else 0.0,
            'avg_loss': losses.mean() if not losses.empty else 0.0, 
            'win_loss_ratio': abs(wins.mean()/losses.mean()) if not losses.empty and losses.mean() != 0 else float('inf')
        }

    def summary(self, strategy_name: str, ticker:str)-> dict:
        wl = self.avg_win_loss()
        total_returns = (self.equity['value'].iloc[-1] / self.equity['value'].iloc[0]) - 1

        return {
            'strategy': strategy_name,
            'ticker': ticker,
            'total_return': total_returns, 
            'sharpe_ratio': self.sharpeRatio(),
            'max_drawdown': self.maxDrawdown(), 
            'num_trades': len(self.trades), 
            'win_rate': self.win_rate(), 
            'avg_win': wl['avg_win'],
            'avg_loss': wl['avg_loss'], 
            'win_loss_ratio': wl['win_loss_ratio'],
            'total_cost': self.trades['cost'].sum() if not self.trades.empty else 0.0
        }
    
