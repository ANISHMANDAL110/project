# LSTM Model for 30-day Stock Forecast
import sys
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from typing import TYPE_CHECKING
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

# TensorFlow imports with fallback
TENSORFLOW_AVAILABLE = False
try:
    import tensorflow as tf  # type: ignore
    from tensorflow.keras.models import Sequential  # type: ignore
    from tensorflow.keras.layers import Dense, LSTM, Dropout  # type: ignore
    from tensorflow.keras.optimizers import Adam  # type: ignore
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. Using exponential smoothing fallback.")

# Type hints for IDE support
if TYPE_CHECKING:
    from tensorflow.keras.models import Sequential  # type: ignore
    from tensorflow.keras.layers import Dense, LSTM, Dropout  # type: ignore

FORECAST_DAYS = 30
SEQ_LENGTH = 60

def get_paths(symbol):
    csv_file = f'data-uploader/stock-data/{symbol}.csv'
    output_file = f'data-uploader/predicted-data/{symbol}-lstm-predicted.csv'
    return csv_file, output_file

def load_and_prepare_data(csv_file):
    df = pd.read_csv(csv_file)
    df['published_date'] = pd.to_datetime(df['published_date'])
    df = df.sort_values('published_date')
    df = df[['published_date', 'close']].copy()
    df = df.dropna()
    return df

def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(seq_length, len(data)):
        X.append(data[i-seq_length:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

def exponential_smoothing_forecast(data, forecast_days, alpha=0.3):
    """Fallback method using exponential smoothing"""
    forecasts = []
    last_value = data[-1]
    
    for _ in range(forecast_days):
        forecast = alpha * last_value + (1 - alpha) * (forecasts[-1] if forecasts else last_value)
        forecasts.append(forecast)
        last_value = forecast
    
    return np.array(forecasts)

def main():
    if len(sys.argv) != 2:
        print('Usage: python lstm_model_anish.py <SYMBOL>')
        return
    
    symbol = sys.argv[1]
    csv_file, output_file = get_paths(symbol)
    
    if not os.path.exists(csv_file):
        print(f'Input file not found: {csv_file}')
        return
    
    # Load and prepare data
    df = load_and_prepare_data(csv_file)
    
    if df is None or df.empty:
        print('Failed to load data.')
        return
    
    # Extract closing prices and reshape for scaling
    data = df['close'].values.reshape(-1, 1)
    
    # Scale the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    if not TENSORFLOW_AVAILABLE:
        # Use fallback exponential smoothing method
        forecasted_values = exponential_smoothing_forecast(data.flatten(), FORECAST_DAYS)
    else:
        # Split into train and test
        train_size = int(len(scaled_data) * 0.8)
        train_data = scaled_data[:train_size]
        test_data = scaled_data[train_size:]
        
        # Create sequences
        X_train, y_train = create_sequences(train_data, SEQ_LENGTH)
        X_test, y_test = create_sequences(test_data, SEQ_LENGTH)
        
        # Reshape for LSTM input [samples, time steps, features]
        X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
        X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
        
        # Build Stacked LSTM Model
        print(f"Building LSTM model for {symbol}...")
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])
        
        # Compile model
        model.compile(optimizer=Adam(learning_rate=0.001),
                      loss='mean_squared_error',
                      metrics=['mae'])
        
        # Train model
        print(f"Training LSTM model...")
        history = model.fit(
            X_train, y_train,
            batch_size=32,
            epochs=50,
            validation_data=(X_test, y_test),
            verbose=0,
            shuffle=False
        )
        
        # Generate future predictions
        last_sequence = scaled_data[-SEQ_LENGTH:]
        forecasted_values_scaled = []
        
        for _ in range(FORECAST_DAYS):
            seq_input = last_sequence.reshape((1, SEQ_LENGTH, 1))
            pred = model.predict(seq_input, verbose=0)
            forecasted_values_scaled.append(pred[0, 0])
            last_sequence = np.append(last_sequence[1:], pred[0, 0])
        
        # Inverse transform predictions
        forecasted_values = scaler.inverse_transform(np.array(forecasted_values_scaled).reshape(-1, 1)).flatten()
    
    # Create forecast dates (business days)
    last_date = df['published_date'].iloc[-1]
    forecast_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=FORECAST_DAYS)
    
    # Save predictions
    forecasted_df = pd.DataFrame({
        'date': forecast_dates.strftime('%Y-%m-%d'),
        'Forecasted_Price': forecasted_values.flatten() if isinstance(forecasted_values, np.ndarray) else forecasted_values
    })
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    forecasted_df.to_csv(output_file, index=False)
    print(f"Forecasted data saved to '{output_file}'")

if __name__ == '__main__':
    main()
