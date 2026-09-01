from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def generate_signal(self, price_history: pd.DataFrame, current_idx: int) -> float:
        raise NotImplementedError

class MovingAverageCrossover(Strategy):
    def __init__(self, fast = 10, slow = 50, **params):
        super().__init__(**params)

        self.fast = fast
        self.slow = slow
        self._cache = {}

    def generate_signal(self, price_history, current_idx):
        key = id(price_history)
        if key not in self._cache:
            fast_ma = price_history['close'].rolling(self.fast).mean()
            slow_ma = price_history['close'].rolling(self.slow).mean()
            self._cache[key] =  (fast_ma, slow_ma)

        fast_today = self._cache[key][0].iloc[current_idx]
        slow_today = self._cache[key][1].iloc[current_idx]

        if pd.isna(fast_today) or pd.isna(slow_today):
            return 0

        return 1 if fast_today > slow_today else -1

class MeanReversion(Strategy):
    def __init__(self, window = 20, z_thresh = 2.0, **params):
        super().__init__(**params)

        self.window = window
        self.z_thresh = z_thresh
        self._cache = {}

    def generate_signal(self, price_history, current_idx):
        key = id(price_history)
        if key not in self._cache:
            mean = price_history['close'].rolling(self.window).mean()
            std = price_history['close'].rolling(self.window).std()
            self._cache[key] =  (price_history['close'] - mean)/std

        z_today = self._cache[key].iloc[current_idx]

        if pd.isna(z_today):
            return 0 #Not enough data/history

        if z_today < -self.z_thresh:
            return 1 #Long/buy
        elif z_today > self.z_thresh:
            return -1 #Short/sell
        else:
            return 0 #Stay
        
