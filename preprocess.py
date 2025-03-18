import pandas as pd
def check_time_series(df_bnb):
    # Ensure the open_time column is datetime and sorted

    df_bnb['datetime'] = pd.to_datetime(df_bnb['open_time'],unit='ms', utc= True)
    df = df_bnb.sort_values('datetime').reset_index(drop=True)

    # Create a complete date range from the minimum to maximum timestamp with 5-minute intervals
    full_range = pd.date_range(start=df['datetime'].min(), end=df['datetime'].max(), freq='5min')

    # Find missing timestamps by comparing with the DataFrame's open_time values
    missing_periods = full_range.difference(df['datetime'])

    print("Missing 5-minute periods:", missing_periods)
    df = df.drop(columns='datetime')

def impute_missing_values_t_s(df):
    
    # Ensure open_time is datetime and sorted
    df['datetime'] = pd.to_datetime(df['open_time'],unit='ms', utc= True)
    df = df.sort_values('datetime').reset_index(drop=True)

    # Set open_time as the DataFrame index
    df = df.set_index('datetime')

    # Create a complete date range of 5-minute intervals
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='5min')

    # Reindex the DataFrame to include every 5-minute period
    df = df.reindex(full_range)

    # Option 1: Forward-fill missing values (if appropriate for your strategy)
    df_filled = df.fillna(method='ffill')

    # Option 2: Interpolate missing values (if you prefer interpolation)
    # df_filled = df.interpolate(method='time')

    # Reset the index to have open_time as a column again
    df_filled = df_filled.reset_index().rename(columns={'index': 'datetime'})
    
    df_filled['open_time'] = df_filled['datetime'].astype('int64') // 10**6
    df_filled = df_filled.drop(columns='datetime')
    # Check for missing periods again
    return df_filled
