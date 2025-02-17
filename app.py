import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.graph_objects as go
from prophet import Prophet
from datetime import datetime, timedelta
import openai
import os
import time 
import serial
import re
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

from serial.serialutil import SerialException


@st.cache_resource
def load_prophet_model():
    with open("./prediction/prophet_model.pkl", "rb") as f:
        model = pickle.load(f)
    return model

@st.cache_data
def load_historical_data():
    # Load the daily aggregated CSV and resample to monthly totals
    df_daily = pd.read_csv("daily_aggregated.csv", parse_dates=["timestamp"])
    df_daily.set_index("timestamp", inplace=True)
    monthly_data = df_daily.resample("M").agg({"daily_liters_sum": "sum"})
    monthly_data.reset_index(inplace=True)
    monthly_data.rename(columns={"timestamp": "ds", "daily_liters_sum": "y"}, inplace=True)
    return monthly_data

def create_forecast_chart(monthly_data, forecast):
    last_hist_date = monthly_data['ds'].max()
    forecast_future = forecast[forecast['ds'] > last_hist_date]
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
        name='Forecast',
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
        title="Historical Water Usage & 2-Year Forecast",
        xaxis_title="Date",
        yaxis_title="Monthly Water Usage (Liters)",
        template="plotly_white"
    )
    return fig



def load_data():
    try:
        data = pd.read_csv("1_year_data.csv")
        data['timestamp'] = pd.to_datetime(data['timestamp'], format="%Y-%m-%d %H:%M:%S")
        return data
    except FileNotFoundError:
        st.error("File '1_year_data.csv' not found. Please ensure the file exists.")
        return pd.DataFrame()

def aggregate_data(data, date, type):
    if type == "Daily":
        daily_data = data[data['timestamp'].dt.date == date]
        numeric_columns = daily_data.select_dtypes(include=[np.number]).columns
        return daily_data.groupby(pd.Grouper(key='timestamp', freq='10min'))[numeric_columns].mean().reset_index()
    
    elif type == "Weekly":
        start_of_week = date - pd.Timedelta(days=date.weekday()) 
        end_of_week = start_of_week + pd.Timedelta(days=6)  
      
        weekly_data = data[(data['timestamp'].dt.date >= start_of_week) & (data['timestamp'].dt.date <= end_of_week)]
 
        numeric_columns = weekly_data.select_dtypes(include=[np.number]).columns
        return weekly_data.groupby(pd.Grouper(key='timestamp', freq='H'))[numeric_columns].mean().reset_index()
    
    elif type == "Monthly":
        
        monthly_data = data[(data['timestamp'].dt.year == date.year) & (data['timestamp'].dt.month == date.month)]
        
        numeric_columns = monthly_data.select_dtypes(include=[np.number]).columns
    
        return monthly_data.groupby(pd.Grouper(key='timestamp', freq='12H'))[numeric_columns].mean().reset_index()

def plots(title, y_axis, time, data, y):
    st.subheader(title)
    chart_data = pd.DataFrame({
        'time': time,
        y_axis: data[y]
    }).set_index('time')
    st.line_chart(chart_data)
    st.markdown("<br><br>", unsafe_allow_html=True)

# --- Caching functions for efficiency ---
@st.cache_resource
def load_prophet_model():
    with open("./prediction/prophet_model.pkl", "rb") as f:
        model = pickle.load(f)
    return model

@st.cache_data
def load_historical_data():
    # Load the daily aggregated CSV and resample to monthly totals
    df_daily = pd.read_csv("daily_aggregated.csv", parse_dates=["timestamp"])
    df_daily.set_index("timestamp", inplace=True)
    monthly_data = df_daily.resample("M").agg({"daily_liters_sum": "sum"})
    monthly_data.reset_index(inplace=True)
    monthly_data.rename(columns={"timestamp": "ds", "daily_liters_sum": "y"}, inplace=True)
    return monthly_data

def create_forecast_chart(monthly_data, forecast):
    last_hist_date = monthly_data['ds'].max()
    forecast_future = forecast[forecast['ds'] > last_hist_date]
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
        name='Forecast',
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
        title="Historical Water Usage & 2-Year Forecast",
        xaxis_title="Date",
        yaxis_title="Monthly Water Usage (Liters)",
        template="plotly_white"
    )
    return fig

def Historical(df_filtered,time_frame):

    col1, col2 = st.columns([1, 1])
    #flow_total = df_filtered["flow_rate"].sum()

    settings = {
        "Temperature": {"average": 19.67, "range": (5, 15)},
        "Flow_rate": {"average": 5.03, "range": (0, 150)},
        "Purity": {"average": 79.67, "range": (60, 100)},
    }
    flow_avg = df_filtered["flow_rate"].mean()
    temp_avg = df_filtered["temperature"].mean()
    purity_avg = df_filtered["purity"].mean()
    
    flow_avg = df_filtered["flow_rate"].mean()
    temp_avg = df_filtered["temperature"].mean()
    purity_avg = df_filtered["purity"].mean()


    temperature_range = settings["Temperature"]["average"]
    flow_rate_range = settings["Flow_rate"]["average"]
    purity_range = settings["Purity"]["average"]
# Define the labels and corresponding average values
    metrics = ["Temperature", "Flow Rate", "Purity"]
    averages = [temp_avg, flow_avg, purity_avg]

    bar_data = pd.DataFrame({
    f"{time_frame} Average": [temp_avg, flow_avg, purity_avg],
    "Overall_Average":[temperature_range, flow_rate_range, purity_range]
    }, index=["Temperature", "Flow Rate", "Purity"])

    with col1:
        plots("Water Quality", "Percent %", df_filtered['timestamp'], df_filtered, 'purity')
        plots("Flow Rate", "Litre/Minute L/min", df_filtered['timestamp'], df_filtered, 'flow_rate')
    with col2:      
        plots("Temperature Rate", "Celsius °C", df_filtered['timestamp'], df_filtered, 'temperature')
        st.subheader("Historical Insights")
        st.bar_chart(bar_data)
    st.subheader("Cost Analysis")
    current_volume = calculate_vol(flow_avg, time_frame)
    average_volume = calculate_vol(flow_rate_range, time_frame)
    current_cost = current_volume* 0.0023173
    average_cost = average_volume* 0.0023173
    col3, col4, col5, col6 = st.columns(4)

    with col3:
        st.metric(label=f"{time_frame} Volume (L)", value=f"{current_volume:.2f}", delta=f"{current_volume - average_volume:.2f} L")

    with col4:
        st.metric(label="Average Volume (L)", value=f"{average_volume:.2f}")

    with col5:
        st.metric(label=f"{time_frame} Cost ($)", value=f"${current_cost:.4f}", delta=f"${current_cost - average_cost:.4f}")

    with col6:
        st.metric(label="Average Cost ($)", value=f"${average_cost:.4f}")

    

def calculate_vol(val, time_frame):
    if time_frame == 'Daily':
        return day_vol(val)
    if time_frame == 'Weekly':
        return week_vol(val)
    if time_frame == "Monthly":
        return month_vol(val)


def day_vol(val):
    return val*86.4
def week_vol(val):
    return val*604.8
def month_vol(val):
    return val*2.628*10**3     

def usb_init():
    comPort = "/dev/rfcomm0"
    print("Attempting connection to: ", comPort)
    test = 0
    try:
        serialPort = serial.Serial(port=comPort, baudrate=9600, timeout=0, parity=serial.PARITY_EVEN, stopbits=1)
        print("Connection Successful!")
        return serialPort
    except Exception as e:
        print("Connection Failed :(")
    return -1

def read_from_usb(connection):
    size = 1024
    if connection != -1:
        try:
            data = connection.readline(size)
            if data:
                return data.decode('utf-8', errors='ignore')  # Decode bytes to string
            else:
                return None
        except SerialException as e:
            print(f"SerialException: {e}")
            return None
    return None

def parse_data_packet(packet):
    parts = packet.split(';')

# Extract each value based on the structure of the string
    date = parts[0].split(":")[1].strip()
    flow = float(parts[1].split(":")[1].strip())
    temperature = float(parts[2].split(":")[1].strip())
    turbidity = float(parts[3].split(":")[1].strip())


    date_time = datetime.strptime(date, "%Y-%m-%d %H-%M-%S")


    return date_time, flow, temperature, turbidity

def Real_Time():
    #st.title("Real-Time Data Visualization")
    columns = ['timestamp', 'flow_rate', 'temperature', 'turbidity']
    data = pd.DataFrame(columns=columns)
    

    col1, col2, col3 = st.columns(3)  

   
    chart_placeholder1 = col1.empty()
    chart_placeholder2 = col2.empty()
    chart_placeholder3 = col3.empty()

    connection = usb_init()

    while True:
        raw_data = read_from_usb(connection)
        if raw_data is None:  # Check if raw_data is None
            continue  # Skip the rest of the loop if no data is available
        
        date_time, flow_rate, temperature, turbidity = parse_data_packet(raw_data)

        new_row = {
            'timestamp': date_time,
            'flow_rate': flow_rate,
            'temperature': temperature,
            'turbidity': turbidity
        }
        data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)


        # Convert timestamp column to index for plotting
        data_indexed = data.set_index('timestamp')

        # Update each chart separately
        
        chart_placeholder1.line_chart(data_indexed[['flow_rate']])
        chart_placeholder2.line_chart(data_indexed[['temperature']])
        chart_placeholder3.line_chart(data_indexed[['turbidity']])

        time.sleep(1)


    

df = load_data()


with st.sidebar:
    st.title("HydroMIND Dashboard")
    st.header("⚙️ Settings")
    max_date = df['timestamp'].max().date()
    default_start_date = max_date - timedelta(days=365)  # Show a year by default

    chart_selection = st.selectbox("Select a chart type", ("Real Time", "Historical", "Projection"))

    start_date = default_start_date
    time_frame = "Daily"
    df_filtered = aggregate_data(df, start_date, time_frame)

if chart_selection == "Real Time":
    st.markdown("<h1 style='text-align: center;'>Water monitor real time statistics</h1>", unsafe_allow_html=True)
    Real_Time()



if chart_selection == "Projection":
    st.markdown("<h1 style='text-align: center;'>Water monitor projection statistics</h1>", unsafe_allow_html=True)
    st.title("HydroMIND Projections & Insights")
    st.markdown("### Empowering remote communities with actionable water monitoring insights")

    st.sidebar.header("Projections Settings")
    horizon_months = st.sidebar.slider("Forecast Horizon (months)", min_value=12, max_value=36, value=24, step=6)
    show_ai_insights = st.sidebar.checkbox("Show AI-generated Insights", value=True)
    

    monthly_data = load_historical_data()
    model = load_prophet_model()
    

    future = model.make_future_dataframe(periods=horizon_months, freq='M')
    forecast = model.predict(future)
    

    fig = create_forecast_chart(monthly_data, forecast)
    st.plotly_chart(fig, use_container_width=True)
    
#     # 2. Display AI-driven insights with increased font size for better readability
    if show_ai_insights:
        st.markdown("#### <span style='font-size:20px;'>Personalized Advice</span>", unsafe_allow_html=True)
        recent_summary = (
            "Recent data indicates that last week's water usage was higher than normal, "
            "especially during peak hours."
        )
        prompt = (
            "You are a friendly water usage advisor for a household. Based on the following summary:\n\n"
            f"{recent_summary}\n\n"
            "Provide a concise, personalized recommendation (under 150 tokens) "
            "for encouraging water conservation and responsible water usage. "
            "Mention common household factors such as parents being at work or children at home if applicable."
        )
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful and friendly water usage advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        insights = response.choices[0].message.content.strip()
        st.markdown(f"<div style='font-size:18px;'>{insights}</div>", unsafe_allow_html=True)
    
    # 3. Display the comparison table (wider, using container width)
    st.markdown("#### Recent Historical vs. Forecasted Water Usage")
    forecast_comp = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    comparison = monthly_data.merge(forecast_comp, on='ds', how='left')
    st.dataframe(comparison.tail(12), use_container_width=True)
    
    # 4. Display download buttons for forecast data and interactive chart
    st.markdown("#### Download Options")
    csv_data = forecast.to_csv(index=False)
    st.download_button("Download Forecast CSV", csv_data, file_name="forecast_data.csv", mime="text/csv")
    
    html_bytes = fig.to_html(full_html=False, include_plotlyjs='cdn')
    st.download_button("Download Forecast Chart HTML", html_bytes, file_name="forecast_chart.html", mime="text/html")
    
if chart_selection == "Historical":
    st.markdown("<h1 style='text-align: center;'>Water monitor historical statistics</h1>", unsafe_allow_html=True)
    with st.sidebar:
        start_date = st.date_input("Start date", default_start_date, min_value=df['timestamp'].min().date(), max_value=max_date)
        time_frame = st.selectbox("Select time frame", ("Daily", "Weekly", "Monthly"))
    
    Historical(df_filtered,time_frame)



# with st.expander('See DataFrame (Selected time frame)'):
#     st.dataframe(df)



st.markdown("""
    <style>
    .block-container {
        max-width: 90% !important;
    }
    .stChart {
        padding: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)