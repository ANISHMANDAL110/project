# ARIMA Model for 30-day Stock Forecast
import sys
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

FORECAST_DAYS = 30

def get_paths(symbol):
    csv_file = f'data-uploader/stock-data/{symbol}.csv'
    output_file = f'data-uploader/predicted-data/{symbol}-arima-predicted.csv'
    return csv_file, output_file

def load_and_prepare_data(csv_file):
    df = pd.read_csv(csv_file)
    df['published_date'] = pd.to_datetime(df['published_date'])
    df = df.sort_values('published_date')
    df = df.set_index('published_date')
    df = df.fillna(method='ffill')
    ts = df[['close']].copy()
    ts = ts.dropna()
    return ts

def find_arima_order(ts, max_p=2, max_d=1, max_q=2):
    """Find best ARIMA order using AIC"""
    best_aic = np.inf
    best_order = (1, 1, 1)
    
    try:
        for p in range(0, max_p + 1):
            for d in range(0, max_d + 1):
                for q in range(0, max_q + 1):
                    try:
                        model = ARIMA(ts['close'], order=(p, d, q))
                        fitted = model.fit()
                        if fitted.aic < best_aic:
                            best_aic = fitted.aic
                            best_order = (p, d, q)
                    except:
                        continue
    except:
        pass
    
    return best_order

def main():
    if len(sys.argv) != 2:
        print('Usage: python arima_model_anish.py <SYMBOL>')
        return
    
    symbol = sys.argv[1]
    csv_file, output_file = get_paths(symbol)
    
    if not os.path.exists(csv_file):
        print(f'Input file not found: {csv_file}')
        return
    
    # Load and prepare data
    ts = load_and_prepare_data(csv_file)
    
    if ts is None or ts.empty:
        print('Failed to load data.')
        return
    
    # Split data into train and test
    split_ratio = 0.8
    split_index = int(len(ts) * split_ratio)
    ts_train = ts.iloc[:split_index]
    ts_test = ts.iloc[split_index:]
    
    # Find best ARIMA order
    print(f"Finding best ARIMA order for {symbol}...")
    best_order = find_arima_order(ts_train)
    print(f"Best ARIMA order: {best_order}")
    
    # Fit ARIMA model on training data
    try:
        model = ARIMA(ts_train['close'], order=best_order)
        fitted_model = model.fit()
        print(f"ARIMA model fitted successfully with order {best_order}")
    except Exception as e:
        print(f"Error fitting ARIMA model: {e}")
        print("Falling back to ARIMA(1,1,1)")
        model = ARIMA(ts_train['close'], order=(1, 1, 1))
        fitted_model = model.fit()
    
    # Forecast next 30 business days
    last_date = ts.index[-1]
    forecast_dates = pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=FORECAST_DAYS)
    forecast = fitted_model.forecast(steps=FORECAST_DAYS)
    
    # Save predictions
    forecasted_df = pd.DataFrame({
        'date': forecast_dates.strftime('%Y-%m-%d'),
        'Forecasted_Price': forecast.values
    })
    
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    forecasted_df.to_csv(output_file, index=False)
    print(f"Forecasted data saved to '{output_file}'")

if __name__ == '__main__':
    main()
