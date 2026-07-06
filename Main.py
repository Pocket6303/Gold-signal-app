import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

st.set_page_config(page_title="Gold Institutional Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v3.0")

ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)

ticker = "GC=F"
try:
    data = yf.download(ticker, period="10d", interval="15m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.dropna()
except Exception:
    st.stop()

# Indicators
price = float(data['Close'].values[-1])
ema_200 = float(data['Close'].ewm(span=200, adjust=False).mean().values[-1])
vol_avg = float(data['Volume'].rolling(20).mean().values[-1])
current_vol = float(data['Volume'].values[-1])
rsi = float(100 - (100 / (1 + (data['Close'].diff(1).clip(lower=0).rolling(14).mean() / 
                               data['Close'].diff(1).clip(upper=0).abs().rolling(14).mean()).values[-1])))

# Logic
is_bullish_sweep = (price > ema_200) and (rsi > 40 and rsi < 60) and (current_vol > vol_avg * 1.2)
is_bearish_sweep = (price < ema_200) and (rsi < 60 and rsi > 40) and (current_vol > vol_avg * 1.2)

if is_bullish_sweep:
    signal, color, sl, tp = "INSTITUTIONAL BUY (Sweep)", "#22c55e", price - 2.5, price + 7.5
elif is_bearish_sweep:
    signal, color, sl, tp = "INSTITUTIONAL SELL (Sweep)", "#ef4444", price + 2.5, price - 7.5
else:
    signal, color, sl, tp = "WAITING FOR LIQUIDITY SWEEP", "#f59e0b", None, None

# Display
st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid {color};">
    <h2 style="margin:0;">Signal: {signal}</h2>
    <p><b>Time (IST):</b> {now.strftime('%H:%M:%S')}</p>
    <hr>
    <p><b>Current Price (Entry):</b> {price:.2f}</p>
    {f'<p style="color:red;"><b>SL:</b> {sl:.2f}</p><p style="color:green;"><b>TP:</b> {tp:.2f}</p>' if sl else '<p><i>Levels will appear when signal triggers.</i></p>'}
    <p><small>Logic: Price Action + EMA Trend + Institutional Volume Spike</small></p>
</div>
""", unsafe_allow_html=True)
