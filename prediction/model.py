import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly
from sklearn.metrics import mean_absolute_error, mean_squared_error

def main():
    # 1. Load daily aggregated data and resample to monthly totals
    df_daily = pd.read_csv("daily_aggregated.csv", parse_dates=["timestamp"])
    df_daily.set_index("timestamp", inplace=True)
    monthly_data = df_daily.resample("M").agg({"daily_liters_sum": "sum"})
    monthly_data.reset_index(inplace=True)
    monthly_data.rename(columns={"timestamp": "ds", "daily_liters_sum": "y"}, inplace=True)
    print("Monthly Data Head:")
    print(monthly_data.head())

    # 2. Split into training and test sets if we have enough data (last 24 months as test)
    if len(monthly_data) > 24:
        train = monthly_data.iloc[:-24].copy()
        test = monthly_data.iloc[-24:].copy()
        print("\nTraining Data Head:")
        print(train.head())
        print("\nTest Data Head:")
        print(test.head())
    else:
        train = monthly_data.copy()
        test = None
        print("\nNot enough data for a test split; using all data for training.")

    # 3. Fit Prophet model on training data
    model = Prophet()
    model.fit(train)

    # 4. Forecast for the test period (if available) and compute accuracy metrics
    if test is not None:
        future_test = model.make_future_dataframe(periods=len(test), freq='M')
        forecast_test = model.predict(future_test)
        # Keep only the dates corresponding to our test set
        forecast_test = forecast_test[forecast_test['ds'].isin(test['ds'])]
        mae = mean_absolute_error(test['y'], forecast_test['yhat'])
        rmse = np.sqrt(mean_squared_error(test['y'], forecast_test['yhat']))
        mape = np.mean(np.abs((test['y'] - forecast_test['yhat']) / test['y'])) * 100
        accuracy = 100 - mape  # Define accuracy as 100 minus MAPE
        print(f"\nAccuracy Metrics on Test Set:")
        print(f"  MAE: {mae:.2f}")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  MAPE: {mape:.2f}%")
        print(f"  Accuracy Percentage: {accuracy:.2f}%")
    
    # 5. Refit Prophet on the full historical monthly data and forecast 2 years (24 months) into the future
    model_full = Prophet()
    model_full.fit(monthly_data)
    future = model_full.make_future_dataframe(periods=24, freq='M')
    forecast_full = model_full.predict(future)
    
    # 6. Save the full model to disk
    with open("prophet_model.pkl", "wb") as f:
        pickle.dump(model_full, f)
    print("\nProphet model saved as 'prophet_model.pkl'.")

    # 7. Create an interactive Plotly chart
    last_hist_date = monthly_data['ds'].max()
    forecast_future = forecast_full[forecast_full['ds'] > last_hist_date]
    
    historical_trace = go.Scatter(
        x=monthly_data['ds'],
        y=monthly_data['y'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='blue')
    )
    forecast_trace = go.Scatter(
        x=forecast_future['ds'],
        y=forecast_future['yhat'],
        mode='lines+markers',
        name='Forecast (Next 2 Years)',
        line=dict(color='red')
    )
    ci_trace = go.Scatter(
        x=forecast_future['ds'].tolist() + forecast_future['ds'][::-1].tolist(),
        y=forecast_future['yhat_upper'].tolist() + forecast_future['yhat_lower'][::-1].tolist(),
        fill='toself',
        fillcolor='rgba(255, 0, 0, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='Confidence Interval'
    )
    
    fig = go.Figure(data=[historical_trace, forecast_trace, ci_trace])
    fig.update_layout(
        title="Monthly Water Usage: Historical (Blue) & Forecast (Red)",
        xaxis_title="Date",
        yaxis_title="Monthly Water Usage (Liters)",
        template="plotly_white"
    )
    
    # 8. Save the interactive chart as an HTML file
    fig.write_html("forecast_chart.html")
    print("\nInteractive chart saved as 'forecast_chart.html'.")
    
    # Optionally show the figure (if running locally with a browser)
    fig.show()

if __name__ == "__main__":
    main()
