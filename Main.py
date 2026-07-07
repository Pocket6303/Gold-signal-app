import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XAUUSD Master Engine v5.37", layout="wide")
st.title("🏛️ XAUUSD Master Institutional Engine v5.37")

ticker = "XAUUSD=X"

# Data Fetching
@st.cache_data(ttl=10)
def get_data(tf):
    data = yf.download(ticker, period="5d", interval=tf, progress=False)
    daily = yf.download(ticker, period="5d", interval="1d", progress=False)
    return data, daily

tf = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m"], index=1)
data, daily = get_data(tf)
price = float(data['Close'].iloc[-1])

# Indicators Stack
data['ema_50'] = ta.ema(data['Close'], length=50)
data['rsi'] = ta.rsi(data['Close'], length=14)
data['atr'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)

# Institutional Levels
pdh = float(daily['High'].iloc[-2])
pdl = float(daily['Low'].iloc[-2])

# Logic Definitions
is_pdh_sweep = price > pdh and price < (pdh + 5)
is_pdl_sweep = price < pdl and price > (pdl - 5)
mss_bull = price > data['High'].rolling(10).max().iloc[-2]
mss_bear = price < data['Low'].rolling(10).min().iloc[-2]

# Confluence Filter (The Heavy Logic)
trend_ok = price > data['ema_50'].iloc[-1]
momentum_ok = data['rsi'].iloc[-1] > 40 and data['rsi'].iloc[-1] < 60

# --- MASTER STRATEGY DECODER ---
st.markdown("---")
if is_pdh_sweep and mss_bear and trend_ok:
    signal, color = "SELL: Institutional PDH Sweep + MSS + Trend Filter", "#ef4444"
elif is_pdl_sweep and mss_bull and trend_ok:
    signal, color = "BUY: Institutional PDL Sweep + MSS + Trend Filter", "#22c55e"
else:
    signal, color = "MONITORING: Analyzing Confluence...", "#64748b"

# Display Dashboard
st.markdown(f"""
<div style="background-color: #1e293b; padding: 25px; border-radius: 15px; border: 2px solid {color};">
    <h2 style="color:{color};">{signal}</h2>
    <hr>
    <p><b>Price:</b> {price:.2f} | <b>ATR:</b> {data['atr'].iloc[-1]:.2f} | <b>RSI:</b> {data['rsi'].iloc[-1]:.2f}</p>
    <p><b>Logic Active:</b> Institutional Sweep & Structure Alignment</p>
</div>
""", unsafe_allow_html=True)
