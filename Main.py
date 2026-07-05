import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v2.0")

# Fetch data
ticker = "GC=F"
data = yf.download(ticker, period="5d", interval="15m")

# DATA CLEANING: Drop all rows that have ANY missing values
data = data.dropna()

# CHECK: Agar clean karne ke baad data khali hai, toh stop ho jao
if data.empty or len(data) < 50:
    st.info("⚠️ Market band hai (Sunday). Data available nahi hai. Kal check karein.")
    st.stop()

# Ab jab hum yahan pahunche, data safe hai
current_price = data['Close'].iloc[-1]
ema_200 = data['Close'].ewm(span=200, adjust=False).mean().iloc[-1]

delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
# Zero division se bachne ke liye chhota sa check
rs = gain / (loss + 0.00001)
rsi = (100 - (100 / (1 + rs))).iloc[-1]

volume = data['Volume'].iloc[-1]
avg_vol = data['Volume'].mean()

bias = "BULLISH" if current_price > ema_200 else "BEARISH"
score = 50
if (bias == "BULLISH" and rsi < 65) or (bias == "BEARISH" and rsi > 35): score += 20
if volume > avg_vol: score += 20
if abs(current_price - ema_200) > 2: score += 10

st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
    <h3>Signal: {bias}</h3>
    <p>Accuracy Confidence: {score}%</p>
    <p>Entry Price: {current_price:.2f}</p>
</div>
""", unsafe_allow_html=True)
