import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="XAUUSD Master Cumulative v5.39", layout="wide")
st.title("🏛️ XAUUSD Master Cumulative Engine v5.39")

# --- DATA & OFFSET ---
ticker = "XAUUSD=X"
tf = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m"], index=1)
manual_offset = st.sidebar.slider("Fixed Offset ($)", -50.0, 50.0, -14.0, 0.25)

@st.cache_data(ttl=10)
def get_data(tf):
    data = yf.download(ticker, period="5d", interval=tf, progress=False)
    daily = yf.download(ticker, period="5d", interval="1d", progress=False)
    return data, daily

data, daily = get_data(tf)
price = float(data['Close'].iloc[-1]) + manual_offset

# --- CUMULATIVE INDICATOR STACK (No deletion, only addition) ---
# 1. Base Indicators
data['mid'] = data['Close'].rolling(20).mean() + manual_offset
data['std'] = data['Close'].rolling(20).std()
data['ema_50'] = data['Close'].ewm(span=50, adjust=False).mean() + manual_offset
data['atr'] = (data['High'] - data['Low']).rolling(14).mean()
data['rsi'] = 100 - (100 / (1 + (data['Close'].diff().clip(lower=0).rolling(14).mean() / -data['Close'].diff().clip(upper=0).rolling(14).mean())))

# 2. Institutional Layers
pdh = float(daily['High'].iloc[-2]) + manual_offset
pdl = float(daily['Low'].iloc[-2]) + manual_offset
is_pdh_sweep = price > pdh and price < (pdh + 2)
is_pdl_sweep = price < pdl and price > (pdl - 2)
mss_bull = price > data['High'].rolling(10).max().iloc[-2] + manual_offset
mss_bear = price < data['Low'].rolling(10).min().iloc[-2] + manual_offset

# --- DECISION ENGINE ---
signal = "MONITORING: All Indicators Scanning..."
color = "#64748b"

# Verification (Layered)
if is_pdh_sweep and mss_bear and price < data['ema_50'].iloc[-1]:
    signal, color = "SELL: Institutional PDH Sweep + MSS + Trend Alignment", "#ef4444"
elif is_pdl_sweep and mss_bull and price > data['ema_50'].iloc[-1]:
    signal, color = "BUY: Institutional PDL Sweep + MSS + Trend Alignment", "#22c55e"

# UI Display
st.markdown(f"""
<div style="background-color: #0f172a; padding: 25px; border-radius: 15px; border-left: 10px solid {color};">
    <h2 style="color:{color};">{signal}</h2>
    <p><b>Price:</b> {price:.2f} | <b>ATR:</b> {data['atr'].iloc[-1]:.2f} | <b>RSI:</b> {data['rsi'].iloc[-1]:.1f}</p>
    <p style="font-size: 0.8rem; color: #94a3b8;">Active Layers: Bollinger, EMA50, ATR, RSI, Session Liquidity, PDH/PDL Sweep, MSS</p>
</div>
""", unsafe_allow_html=True)
