from src.data_pipeline import get_prices
from src.Strategies import MovingAverageCrossover, MeanReversion
from src.Backtest import Backtester
from src.metrics import Metrics

def test_any_strat_any_ticker():
    strategies = [MovingAverageCrossover(), MeanReversion()]
    tickers = ['AAPL', 'XOM']

    for strat in strategies:
        for ticker in tickers:
            trades, equity = Backtester(strat).run(get_prices(ticker))
            metrics = Metrics(trades=trades, equity=equity)
            print(metrics.summary(strat.__class__.__name__, ticker))

if __name__ == "__main__":
    test_any_strat_any_ticker()