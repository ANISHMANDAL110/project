
# Prophet Model for 30-day Stock Forecast
import sys
import os
import pandas as pd
from prophet import Prophet

def get_paths(symbol):
    csv_file = os.path.join("data-uploader", "stock-data", f"{symbol}.csv")
    output_file = os.path.join("data-uploader", "predicted-data", f"{symbol}-prophet-predicted.csv")
    return csv_file, output_file

def load_and_prepare_data(csv_file):
    df = pd.read_csv(csv_file, parse_dates=["published_date"])
    df = df.drop_duplicates(subset=["published_date"])
    df = df.sort_values("published_date")
    prophet_df = df[["published_date", "close"]].rename(columns={"published_date": "ds", "close": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    return prophet_df

def main():
    if len(sys.argv) != 2:
        print("Usage: python prophet_model_anish.py <SYMBOL>")
        return
    symbol = sys.argv[1]
    csv_file, output_file = get_paths(symbol)
    if not os.path.exists(csv_file):
        print(f"Input file not found: {csv_file}")
        return
    prophet_df = load_and_prepare_data(csv_file)
    # Train Prophet model
    model = Prophet(daily_seasonality=True)
    model.fit(prophet_df)
    # Forecast next 30 business days
    last_date = prophet_df["ds"].max()
    future_dates = pd.bdate_range(last_date + pd.Timedelta(days=1), periods=30)
    future = pd.DataFrame({"ds": future_dates})
    forecast = model.predict(future)
    # Save predictions
    out_df = forecast[["ds", "yhat"]].rename(columns={"ds": "date", "yhat": "Forecasted_Price"})
    out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")
    out_df.to_csv(output_file, index=False)
    print(f"Forecasted data saved to '{output_file}'")

if __name__ == "__main__":
    main()
    main()