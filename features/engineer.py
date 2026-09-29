import pandas as pd
import numpy as np

def compute_historical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates customer-level historical features.
    For the IBM dataset, we treat 'sender' as the primary customer originating the transaction.
    """
    if 'sender' not in df.columns or 'amount' not in df.columns or 'timestamp' not in df.columns:
        return df

    # Ensure timestamp is sorted for rolling calculations
    df = df.sort_values(by=['sender', 'timestamp'])

    # 1. Transaction count per sender (cumulative)
    df['sender_txn_count'] = df.groupby('sender').cumcount() + 1
    
    # 2. Historical average transaction amount (expanding mean)
    df['sender_avg_amount'] = df.groupby('sender')['amount'].transform(
        lambda x: x.expanding().mean()
    )
    
    # 3. Historical deviation (Z-score compared to their own history)
    # We calculate the expanding standard deviation.
    # Note: std requires at least 2 data points, so we fillna with 0 for the first transaction.
    sender_std = df.groupby('sender')['amount'].transform(lambda x: x.expanding().std()).fillna(0)
    
    # Prevent division by zero
    sender_std_safe = sender_std.replace(0, 1)
    
    df['historical_deviation'] = np.where(
        df['sender_txn_count'] > 1,
        (df['amount'] - df['sender_avg_amount']) / sender_std_safe,
        0.0 # Deviation is 0 if it's the first transaction
    )

    return df

def compute_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates time-based features like hour of day or burst activity.
    """
    if 'timestamp' not in df.columns:
        return df

    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Calculate time since last transaction for the same sender
    if 'sender' in df.columns:
        df = df.sort_values(by=['sender', 'timestamp'])
        df['time_since_last_txn_sec'] = df.groupby('sender')['timestamp'].diff().dt.total_seconds().fillna(0)
        
        # Burst activity: if transaction is within 60 seconds of the previous one
        df['is_burst_activity'] = (df['time_since_last_txn_sec'] > 0) & (df['time_since_last_txn_sec'] <= 60)
        df['is_burst_activity'] = df['is_burst_activity'].astype(int)

    return df

def compute_network_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates network/entity features (e.g., unique counterparties).
    """
    if 'sender' not in df.columns or 'receiver' not in df.columns:
        return df
        
    # Calculate how many distinct receivers a sender has sent to up to this point
    # We use an expanding set trick, but for performance, we can just group and count unique globally
    # (In a real streaming system this would be a cumulative unique count state).
    # For this batch DF, we'll calculate global unique counterparties.
    unique_receivers = df.groupby('sender')['receiver'].nunique().reset_index()
    unique_receivers.columns = ['sender', 'sender_unique_counterparties']
    
    df = df.merge(unique_receivers, on='sender', how='left')
    
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main feature engineering pipeline.
    """
    if df.empty:
        return df
        
    df = df.copy()
    df = compute_historical_features(df)
    df = compute_temporal_features(df)
    df = compute_network_features(df)
    
    return df
