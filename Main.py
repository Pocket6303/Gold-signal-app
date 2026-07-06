import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

st.set_page_config(page_title="Gold Institutional Terminal v5.2", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v5.2")

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
data['std'] = data['Close'].rolling(20).std()
data['mid'] = data['Close'].rolling(20).mean()
upper_band = float(data['mid'].values[-1] + (2 * data['std'].values[-1]))
lower_band = float(data['mid'].values[-1] - (2 * data['std'].values[-1]))

vol_spike = data['Volume'].values[-1] > (data['Volume'].rolling(20).mean().values[-1] * 1.5)
sentiment_bullish = (price > upper_band) and vol_spike
sentiment_bearish = (price < lower_band) and vol_spike

# Signal Logic
if sentiment_bullish:
    signal, color, sl, tp = "INSTITUTIONAL BUY (Sentiment)", "#22c55e", price - 3.0, price + 9.0
    display_entry = f"<b>Confirmed Entry:</b> {price:.2f}"
elif sentiment_bearish:
    signal, color, sl, tp = "INSTITUTIONAL SELL (Sentiment)", "#ef4444", price + 3.0, price - 9.0
    display_entry = f"<b>Confirmed Entry:</b> {price:.2f}"
else:
    signal, color, sl, tp = "WAITING FOR INSTITUTIONAL SENTIMENT", "#f59e0b", None, None
    display_entry = f"<i>Current Market Price: {price:.2f}</i>"

# UI Display with forced Dark Theme CSS
st.markdown(f"""
<div style="
    background-color: #1e293b; 
    padding: 25px; 
    border-radius: 15px; 
    border-left: 12px solid {color};
    color: #f8fafc;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
">
    <h1 style="margin:0; color:{color}; font-size: 2rem;">{signal}</h1>
    <p style="color: #cbd5e1; margin-top: 10px;"><b>Time (IST):</b> {now.strftime('%H:%M:%S')}</p>
    <hr style="border-color: #475569; margin: 20px 0;">
    <p style="font-size: 1.3rem; color: #ffffff;">{display_entry}</p>
    {f'<p style="color:#ff6b6b; font-size:1.2rem; margin: 5px 0;"><b>SL:</b> {sl:.2f}</p><p style="color:#51cf66; font-size:1.2rem; margin: 5px 0;"><b>TP:</b> {tp:.2f}</p>' if sl else '<p style="color: #94a3b8; font-style: italic;">Waiting for volatility breakout...</p>'}
    <p style="color: #64748b; font-size: 0.85rem; margin-top: 20px;">Logic: Price Deviation (Bollinger) + 150% Volume Spike (Institutional Flow)</p>
</div>
""", unsafe_allow_html=True)
