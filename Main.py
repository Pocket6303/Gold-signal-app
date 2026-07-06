import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

st.set_page_config(page_title="Gold Institutional Terminal v5.0", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v5.0")

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

# 1. Price Action Indicators
price = float(data['Close'].values[-1])
# Bollinger Band (Volatility Filter) - Sentiment ke liye best hai
data['std'] = data['Close'].rolling(20).std()
data['mid'] = data['Close'].rolling(20).mean()
upper_band = float(data['mid'].values[-1] + (2 * data['std'].values[-1]))
lower_band = float(data['mid'].values[-1] - (2 * data['std'].values[-1]))

# 2. Institutional Sentiment (Relative Volume + Price Momentum)
# Agar Price Bollinger Band ko break kar raha hai aur Volume spike hai -> True Sentiment
vol_spike = data['Volume'].values[-1] > (data['Volume'].rolling(20).mean().values[-1] * 1.5)
sentiment_bullish = (price > upper_band) and vol_spike
sentiment_bearish = (price < lower_band) and vol_spike

# 3. Logic
if sentiment_bullish:
    signal, color, sl, tp = "INSTITUTIONAL BUY (Sentiment)", "#22c55e", price - 3.0, price + 9.0
elif sentiment_bearish:
    signal, color, sl, tp = "INSTITUTIONAL SELL (Sentiment)", "#ef4444", price + 3.0, price - 9.0
else:
    signal, color, sl, tp = "WAITING FOR INSTITUTIONAL SENTIMENT", "#f59e0b", None, None

# Display
st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 10px solid {color};">
    <h1 style="margin:0; color:{color};">{signal}</h1>
    <p><b>Time (IST):</b> {now.strftime('%H:%M:%S')}</p>
    <hr>
    <h3>Entry: {price:.2f}</h3>
    {f'<p style="color:red; font-size:1.2rem;"><b>SL:</b> {sl:.2f}</p><p style="color:green; font-size:1.2rem;"><b>TP:</b> {tp:.2f}</p>' if sl else '<p><i>Waiting for volatility breakout...</i></p>'}
    <p><small>Logic: Price Deviation (Bollinger) + 150% Volume Spike (Institutional Flow)</small></p>
</div>
""", unsafe_allow_html=True)
