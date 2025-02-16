"""
# My first app
Here's our first attempt at using data to create a table:
"""

import streamlit as st
import pandas as pd
import numpy as np
df = pd.DataFrame({
  'first column': [1, 2, 3, 4],
  'second column': [10, 20, 30, 40]
})

# def load_data():
#     data = pd.read_csv("youtube_channel_data.csv")
#     data['DATE'] = pd.to_datetime(data['DATE'])
#     data['NET_SUBSCRIBERS'] = data['SUBSCRIBERS_GAINED'] - data['SUBSCRIBERS_LOST']
#     return data



# df = load_data()
def plots(title, y_axis):
    st.subheader(title)
    data = pd.DataFrame(
        np.random.randn(10,2),
        columns=['X','Y']
        )
    st.line_chart(data, x_label = "time, t", y_label=y_axis, width=500, height=400,)
    st.markdown("<br><br>", unsafe_allow_html=True)
    

with st.sidebar:
    st.title("HydroMIND Dashboard")
    st.header("⚙️ Settings")
    chart_selection = st.selectbox("Select a chart type",
                                   ("Real Time", "Projection"))
    time_frame = st.selectbox("Select time frame",("Daily", "Weekly", "Monthly"))
    
if chart_selection == "Real Time":
    st.markdown("<h1 style='text-align: center; ;'>Water monitor real time statistics </h1>", unsafe_allow_html=True)
if chart_selection == "Projection":
    st.markdown("<h1 style='text-align: center; ;'>Water monitor projection statistics </h1>", unsafe_allow_html=True)



col1, col2 = st.columns([1,1])

with col1:
    plots("Water Quality", "Rercent    %")  
    plots("Flow Rate", "Litre/Minute    L/min")
with col2:
    
    plots("Temperature Rate", "Celcius    °C")

with st.expander('See DataFrame (Selected time frame)'):
    st.dataframe(df)


st.markdown("""
    <style>
    .block-container {
        max-width: 90% !important;  /* Make content wider */
            
    }
    .stChart {
        padding: 20px !important; /* Add padding around each chart */   
            
    }
    </style>
    
    
    """, unsafe_allow_html=True)
