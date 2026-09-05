import pandas as pd

FEATURE_COLUMNS = ['return_1d', 'return_5d', 'ma_ratio', 'volatility_10d', 'rsi_14']

def compute_rsi(close: pd.Series, period:int = 14)-> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain/loss
    return 100 - (100/(1+rs))

def engineer_features(price_df: pd.DataFrame)-> pd.DataFrame:
    df = price_df.copy()
    df['return_1d'] = df['close'].pct_change()
    df['return_5d'] = df['close'].pct_change(5)

    ma_10 = df['close'].rolling(10).mean()
    ma_50 = df['close'].rolling(50).mean()
    df['ma_ratio'] = ma_10/ma_50

    df['volatility_10d'] = df['return_1d'].rolling(10).std()

    df['rsi_14'] = compute_rsi(df['close'], period=14)

    return df

