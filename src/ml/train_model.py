import sys
sys.path.append('..')

import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

from src.data_pipeline import get_prices
from src.ml.features import engineer_features, FEATURE_COLUMNS

TICKERS = ["AAPL", "MSFT", "XOM", "JNJ", "JPM"]
TRAIN_END_DATE = "2022-01-01"

def build_training_set()-> pd.DataFrame:
    frames = []
    for ticker in TICKERS:
        df = engineer_features(get_prices(ticker))
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

        df = df.dropna(subset=FEATURE_COLUMNS + ['target'])
        df = df[df['date'] < TRAIN_END_DATE]

        frames.append(df)

    return pd.concat(frames, ignore_index=True)

def train():
    data = build_training_set()
    X, y = data[FEATURE_COLUMNS], data['target']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression()
    model.fit(X_scaled, y)

    joblib.dump({'model':model, 'scaler': scaler}, 'data/ml_model.joblib')

    print(f"Trained on {len(X)} rows across {len(TICKERS)} tickers, cutoff {TRAIN_END_DATE}")
    print(f"Train accuracy: {model.score(X_scaled, y):.3f}")

if __name__ == '__main__':
    train()