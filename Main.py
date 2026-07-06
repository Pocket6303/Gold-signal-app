import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v2.0")

# Current Time
now = datetime.datetime.now()

ticker = "GC=F"
try:
    # 5d ka data liya taaki calculations stable rahein
    data = yf.download(ticker, period="5d", interval="15m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.dropna()
except Exception as e:
    st.error("Data load karne mein error.")
    st.stop()

# Calculations
current_price = float(data['Close'].values[-1])
ema_200 = float(data['Close'].ewm(span=200, adjust=False).mean().values[-1])

# Signal Logic
bias = "BULLISH" if current_price > ema_200 else "BEARISH"

# 1:3 Risk-Reward Calculation
# SL 2 points ka rakha hai, toh TP 6 points ka hoga (1:3 ratio)
risk_points = 2.0
reward_points = 6.0

if bias == "BULLISH":
    sl = current_price - risk_points
    tp = current_price + reward_points
else:
    sl = current_price + risk_points
    tp = current_price - reward_points

st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
    <h2 style="margin:0;">Signal: {bias}</h2>
    <p style="font-size: 1.2rem; margin: 10px 0;"><b>Time:</b> {now.strftime('%H:%M:%S IST')}</p>
    <hr style="border: 0.5px solid #475569;">
    <p style="font-size: 1.2rem; margin: 5px 0;"><b>Entry:</b> {current_price:.2f}</p>
    <p style="font-size: 1.2rem; margin: 5px 0; color: #ef4444;"><b>SL:</b> {sl:.2f}</p>
    <p style="font-size: 1.2rem; margin: 5px 0; color: #22c55e;"><b>TP:</b> {tp:.2f}</p>
</div>
""", unsafe_allow_html=True)
