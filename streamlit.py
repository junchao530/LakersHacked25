import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import os

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


# def generate_insights(data_segment, period_type):

    
#     return 0

def Historical(df_filtered,time_frame):

    col1, col2 = st.columns([1, 1])

    with col1:
        plots("Water Quality", "Percent %", df_filtered['timestamp'], df_filtered, 'purity')
        plots("Flow Rate", "Litre/Minute L/min", df_filtered['timestamp'], df_filtered, 'flow_rate')
    with col2:
        plots("Temperature Rate", "Celsius °C", df_filtered['timestamp'], df_filtered, 'temperature')
        



    

df = load_data()


with st.sidebar:
    st.title("HydroMIND Dashboard")
    st.header("⚙️ Settings")
    max_date = df['timestamp'].max().date()
    default_start_date = max_date - timedelta(days=365)  # Show a year by default

    chart_selection = st.selectbox("Select a chart type", ("Real Time", "Historical", "Projection"))
    start_date = st.date_input("Start date", default_start_date, min_value=df['timestamp'].min().date(), max_value=max_date)
    time_frame = st.selectbox("Select time frame", ("Daily", "Weekly", "Monthly"))
    
df_filtered = aggregate_data(df, start_date, time_frame)

if chart_selection == "Real Time":
    st.markdown("<h1 style='text-align: center;'>Water monitor real time statistics</h1>", unsafe_allow_html=True)
if chart_selection == "Projection":
    st.markdown("<h1 style='text-align: center;'>Water monitor projection statistics</h1>", unsafe_allow_html=True)
if chart_selection == "Historical":
    st.markdown("<h1 style='text-align: center;'>Water monitor historical statistics</h1>", unsafe_allow_html=True)
    Historical(df_filtered,time_frame)



with st.expander('See DataFrame (Selected time frame)'):
    st.dataframe(df_filtered)



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