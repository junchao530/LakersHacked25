import pandas as pd
import numpy as np

def main():
    # 1. Load the CSV
    csv_file = "simulated_water_flow_3_years.csv"
    print(f"Reading CSV: {csv_file}")
    
    # Parse timestamp with the known format "yyyy-mm-dd:HH:MM:SS"
    df = pd.read_csv(
        csv_file,
        parse_dates=["timestamp"],
        date_parser=lambda x: pd.to_datetime(x, format="%Y-%m-%d:%H:%M:%S")
    )
    
    # 2. Set timestamp as index and sort by time
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    # Quick peek at original data
    print("\n--- Original DataFrame Head ---")
    print(df.head())
    print(df.info())

    # ------------------------------------------------------------------
    # 3. Convert flow_rate (L/min) at 1-second intervals to liters_used
    #    Each 1-second reading represents 1/60 of a minute, so:
    #    liters_used = flow_rate * (1/60)
    # ------------------------------------------------------------------
    df["liters_used"] = df["flow_rate"] * (1.0 / 60.0)

    # ------------------------------------------------------------------
    # 4. Aggregate to Daily Level
    #    - daily_liters_sum: sum of liters_used over the day
    #    - daily_flow_mean: average flow_rate (L/min) for the day
    #    - daily_flow_max, daily_flow_min: max/min flow_rate for the day
    #    - daily_temp_mean: average temperature for the day
    # ------------------------------------------------------------------
    daily_agg = df.resample("D").agg({
        "liters_used": "sum",       # total liters used in the day
        "flow_rate": ["mean", "max", "min"],  # keep daily stats on flow_rate if needed
        "temperature": "mean"
    })

    # Flatten column names
    daily_agg.columns = [
        "daily_liters_sum",    # sum of liters_used (actual daily usage in liters)
        "daily_flow_mean",     # average flow_rate (L/min) across the day
        "daily_flow_max",      # max flow_rate (L/min) in that day
        "daily_flow_min",      # min flow_rate (L/min) in that day
        "daily_temp_mean"      # average temperature
    ]
    daily_agg.reset_index(inplace=True)

    # ------------------------------------------------------------------
    # 5. Add Time-Based Features (year, month, day, day_of_week, day_type)
    # ------------------------------------------------------------------
    daily_agg["year"] = daily_agg["timestamp"].dt.year
    daily_agg["month"] = daily_agg["timestamp"].dt.month
    daily_agg["day"] = daily_agg["timestamp"].dt.day
    daily_agg["day_of_week"] = daily_agg["timestamp"].dt.dayofweek  # Monday=0, Sunday=6

    def classify_day_type(row):
        # Weekend if Saturday (5) or Sunday (6)
        return "Weekend" if row["day_of_week"] in [5, 6] else "Weekday"
    
    daily_agg["day_type"] = daily_agg.apply(classify_day_type, axis=1)

    # ------------------------------------------------------------------
    # 6. Rolling Averages (on daily_liters_sum)
    #    - 7-day and 30-day rolling means
    # ------------------------------------------------------------------
    daily_agg.set_index("timestamp", inplace=True)
    daily_agg["rolling_7d_liters_mean"] = daily_agg["daily_liters_sum"].rolling(window=7, min_periods=1).mean()
    daily_agg["rolling_30d_liters_mean"] = daily_agg["daily_liters_sum"].rolling(window=30, min_periods=1).mean()
    daily_agg.reset_index(inplace=True)

    # Quick peek at the final daily dataset
    print("\n--- Daily Aggregated Data (Head) ---")
    print(daily_agg.head())

    # 7. Save aggregated data
    output_file = "daily_aggregated.csv"
    daily_agg.to_csv(output_file, index=False)
    print(f"\nDaily aggregated data saved to {output_file}.")

if __name__ == "__main__":
    main()
