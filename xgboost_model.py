
# XGBoost Model for 30-day Stock Forecast
import sys
import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor

DAYS_LIST = [1, 2, 3, 5, 10]
FORECAST_DAYS = 30

def get_paths(symbol):
    csv_file = f'data-uploader/stock-data/{symbol}.csv'
    output_file = f'data-uploader/predicted-data/{symbol}-xgboost-predicted.csv'
    return csv_file, output_file

def load_and_prepare_data(csv_file, days_list):
    df = pd.read_csv(csv_file)
    df['published_date'] = pd.to_datetime(df['published_date'])
    df = df.set_index('published_date')
    df = df.rename(columns={'close': 'adjclose'})
    df = df[['adjclose']]
    features = ['adjclose']
    for day in days_list:
        df[f'adjclose_{day}d'] = df.adjclose.shift(day)
        features.append(f'adjclose_{day}d')
    df = df[df[f'adjclose_{max(days_list)}d'].notna()]
    df['target'] = df.adjclose.shift(-1)
    df = df[df['target'].notna()]
    return df, features


def main():
    if len(sys.argv) != 2:
        print('Usage: python xgboost_model.py <SYMBOL>')
        return
    symbol = sys.argv[1]
    csv_file, output_file = get_paths(symbol)
    if not os.path.exists(csv_file):
        print(f'Input file not found: {csv_file}')
        return
    df, features = load_and_prepare_data(csv_file, DAYS_LIST)
    if df is None or df.empty:
        print('Failed to load data.')
        return
    # Train XGBoost model
    X, y = df[features], df['target']
    model = XGBRegressor(n_estimators=2000, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    # Forecast next 30 business days
    last_data_point = X.iloc[-1].values.reshape(1, -1)
    forecast_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=FORECAST_DAYS, freq='B')
    forecasted_values = []
    current_features = last_data_point.copy()
    historical_data_needed = df['adjclose'].iloc[-10:].values
    for i in range(FORECAST_DAYS):
        next_day_prediction = model.predict(current_features)[0]
        forecasted_values.append(next_day_prediction)
        # Build next features
        next_features = [next_day_prediction]
        for lag in DAYS_LIST:
            if len(forecasted_values) > lag:
                next_features.append(forecasted_values[-lag-1])
            elif len(forecasted_values) == lag:
                next_features.append(df['adjclose'].iloc[-1])
            else:
                historical_index = len(historical_data_needed) - (lag - len(forecasted_values)) - 1
                if historical_index >= 0:
                    next_features.append(historical_data_needed[historical_index])
                else:
                    next_features.append(df['adjclose'].iloc[-1])
        current_features = np.array(next_features).reshape(1, -1)
    forecasted_df = pd.DataFrame({'Forecasted_Price': forecasted_values}, index=forecast_dates)
    # Save predictions
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    forecasted_df.to_csv(output_file)
    print(f"Forecasted data saved to '{output_file}'")

if __name__ == '__main__':
    main()
