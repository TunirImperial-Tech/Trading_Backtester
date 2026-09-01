import yfinance as yf
import pandas as pd
from datetime import datetime
import sqlite3

START = datetime(2015, 1, 1)
END = datetime(2025, 1, 1)
TICKERS = ["AAPL", "MSFT", "XOM", "JNJ", "JPM"]

def fetch_and_populate():
    raw = yf.download(tickers=TICKERS, start=START, end=END, auto_adjust=True)
    raw = raw.stack(level=1, future_stack=True).rename_axis(["date", "ticker"]).reset_index()

    raw = raw.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume"
    })
    raw["date"] = raw["date"].dt.strftime("%Y-%m-%d")

    conn = sqlite3.connect("data/prices.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        ticker TEXT, date TEXT,
        open REAL, high REAL, low REAL, close REAL, volume INTEGER,
        PRIMARY KEY (ticker, date)
    )
    """)

    cols = ["ticker", "date", "open", "high", "low", "close", "volume"]

    missing = raw[cols].isna().any(axis=1).sum()
    print(f"Dropping {missing} rows with NaNs")
    raw = raw.dropna(subset=cols)

    conn.executemany(
        "INSERT OR REPLACE INTO prices VALUES (?, ?, ?, ?, ?, ?, ?)",
        raw[cols].itertuples(index=False, name=None)
    )
    conn.commit()

    dupes = pd.read_sql("""
        SELECT ticker, date, COUNT(*) c FROM prices
        GROUP BY ticker, date HAVING c > 1
    """, conn)
    print("Duplicates:", len(dupes))

    calendar = pd.read_sql("SELECT DISTINCT date FROM prices WHERE ticker='AAPL'", conn)
    for t in TICKERS:
        dates_t = pd.read_sql("SELECT date FROM prices WHERE ticker=?", conn, params=(t,))
        missing_days = set(calendar["date"]) - set(dates_t["date"])
        print(t, "missing", len(missing_days), "days")

    check = pd.read_sql("""
        SELECT ticker, COUNT(*), MIN(date), MAX(date)
        FROM prices GROUP BY ticker
    """, conn)


    print(check)
    conn.close()

def get_prices(ticker: str, db_path :str = "data/prices.db")-> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM prices WHERE ticker = ? ORDER BY date", conn, params=(ticker, ))
    conn.close()
    return df

