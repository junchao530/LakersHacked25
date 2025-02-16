import pandas as pd
import numpy as np
from datetime import datetime
import os

# Define simulation parameters
start_date = pd.Timestamp("2020-01-01")
end_date = pd.Timestamp("2024-12-31")
output_file = "simulated_water_flow_5_years.csv"

# Baseline water flow and amplitude for the daily pattern
baseline = 5      # baseline flow rate in L/min
amplitude = 5     # amplitude for daily variation

# Function to determine seasonal factor based on month
def seasonal_factor(m):
    if m in [6, 7, 8]:
        return 1.2  # higher usage in summer
    elif m in [12, 1, 2]:
        return 0.9  # lower usage in winter
    else:
        return 1.0  # average for other months

# Remove output file if it exists (to avoid appending to an old file)
if os.path.exists(output_file):
    os.remove(output_file)

first_chunk = True
current = start_date

while current <= end_date:
    # Determine the end of the current month
    next_month = (current + pd.offsets.MonthEnd(1)).normalize() + pd.Timedelta(seconds=1)
    if next_month > end_date:
        next_month = end_date + pd.Timedelta(seconds=1)
    
    # Generate 1-second interval timestamps for the month
    timestamps = pd.date_range(start=current, end=next_month - pd.Timedelta(seconds=1), freq='S')
    df = pd.DataFrame({'timestamp': timestamps})
    
    # Extract time-of-day as a fractional hour (e.g., 13.5 means 13:30:00)
    df['hour_fraction'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60 + df['timestamp'].dt.second / 3600
    
    # Daily pattern: a combination to simulate two usage peaks (morning and evening)
    df['daily_pattern'] = (np.sin(2 * np.pi * (df['hour_fraction'] / 24)) + 
                            0.5 * np.sin(2 * np.pi * ((df['hour_fraction'] - 8) / 24)))
    
    # Seasonal factor based on the month
    df['month'] = df['timestamp'].dt.month
    df['seasonal_factor'] = df['month'].apply(seasonal_factor)
    
    # Weekend factor: slightly lower usage on weekends (Saturday=5, Sunday=6)
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['weekend_factor'] = df['day_of_week'].apply(lambda x: 0.95 if x >= 5 else 1.0)
    
    # Combine factors to simulate flow rate, and add random noise (std deviation = 1 L/min)
    df['noise'] = np.random.normal(0, 1, size=len(df))
    df['flow_rate'] = baseline + amplitude * df['daily_pattern'] * df['seasonal_factor'] * df['weekend_factor'] + df['noise']
    df['flow_rate'] = df['flow_rate'].clip(lower=0)  # ensure no negative flow
    
    # Format the timestamp as "yyyy-mm-dd:HH:MM:SS"
    df['timestamp'] = df['timestamp'].dt.strftime("%Y-%m-%d:%H:%M:%S")
    
    # Determine day type for additional context
    df['day_type'] = df['timestamp'].apply(lambda ts: "Weekend" 
                                           if pd.to_datetime(ts, format="%Y-%m-%d:%H:%M:%S").dayofweek >= 5 
                                           else "Weekday")
    
    # Select desired columns
    df_out = df[['timestamp', 'flow_rate', 'day_type', 'month']]
    
    # Write the chunk to CSV
    if first_chunk:
        df_out.to_csv(output_file, index=False, mode='w')
        first_chunk = False
    else:
        df_out.to_csv(output_file, index=False, mode='a', header=False)
    
    print(f"Chunk for {current.strftime('%Y-%m')} written with {len(df_out)} records.")
    
    # Move to the next month
    current = next_month

print("Data generation complete!")
