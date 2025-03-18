# open_time,item_id,volume,EMA_12,RSI_12,ATR_14,Pivot_R2,Pivot_S2,dow_sin,dow_cos,hour_sin,hour_cos,month_sin,month_cos,isweekend,log_return,open,high,low,close
import numpy as np
import pandas as pd

def compute_RSI(series, period=14):
    """
    Computes the RSI for a given price series.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Avoid division by zero
    avg_loss = avg_loss.replace({0: 1e-10})
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_ATR(df, period=14):
    """
    Computes the Average True Range (ATR) over 'period' bars.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr


def compute_pivot_points(df):
    """
    Computes classic pivot points (Floor pivot) for each candle:
      Pivot, R1, S1, R2, S2, ...
    """
    pivot = (df["high"] + df["low"] + df["close"]) / 3
    r1 = 2 * pivot - df["low"]
    s1 = 2 * pivot - df["high"]
    r2 = pivot + (df["high"] - df["low"])
    s2 = pivot - (df["high"] - df["low"])
    
    return pivot, r1, s1, r2, s2

def preprocess_data(df):
    

    # ----------------------------------------------------------------
    # 1. Basic Technical Indicators
    # ----------------------------------------------------------------
    # Basic Moving Averages
    df["EMA_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["SMA_24"] = df["close"].rolling(window=24, min_periods=24).mean()
    
    # RSI
    df["RSI_12"] = compute_RSI(df["close"], period=12)
    
    # ATR
    df["ATR_14"] = compute_ATR(df)
    

    # ----------------------------------------------------------------
    # 2. Pivot Points
    # ----------------------------------------------------------------
    pivot, r1, s1, r2, s2 = compute_pivot_points(df)
    df["Pivot_R2"] = r2
    df["Pivot_S2"] = s2
    
    
    # ----------------------------------------------------------------
    # 3. Time-based Features
    # ----------------------------------------------------------------
    df["hour"] = df["open_time"].dt.hour
    df["minute"] = df["open_time"].dt.minute
    df["day_of_week"] = df["open_time"].dt.dayofweek  # Monday=0, Sunday=6
    df["month"] = df["open_time"].dt.month
    
    # Cyclical transforms
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["minute_sin"] = np.sin(2 * np.pi * df["minute"] / 60)
    df["minute_cos"] = np.cos(2 * np.pi * df["minute"] / 60)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    
    df["isweekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))

    drop_cols = [
    "hour",             # Drop raw time features if cyclical transforms (hour_sin, hour_cos) are used.
    "minute",           # Same rationale.
    "day_of_week",      # Keep cyclical transforms (dow_sin, dow_cos) instead.
    "month",            # Keep month_sin/month_cos to capture seasonality.
    'quote_asset_volume',
    'number_of_trades',
    'taker_buy_base_volume',
    'taker_buy_quote_volume',
    ]
    
    df = df.drop(columns=drop_cols)
    
    # ----------------------------------------------------------------
    # 9. Drop Rows with Missing Values
    # ----------------------------------------------------------------
    # Because we have many rolling windows up to 50 intervals, we might lose the first 50 rows.
    df.dropna(inplace=True)
    #df.reset_index(drop=True, inplace=True)

    # ----------------------------------------------------------------
    # 10. Reorder Columns: Place OHLC at the end
    # ----------------------------------------------------------------
    ohlc_cols = ["open", "high", "low", "close"]
    current_cols = list(df.columns)
    id_cols = ["symbol"] if "symbol" in current_cols else []
    
    remaining_cols = [c for c in current_cols if c not in ["open_time"] + id_cols + ohlc_cols]
    new_order = ["open_time"] + id_cols + remaining_cols + ohlc_cols
    df = df[new_order].reset_index(drop=True)
    
    return df