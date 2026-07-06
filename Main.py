import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v2.0")

# 1. Aaj ka din check karein (Glitch-free logic)
today = datetime.datetime.now().weekday() # Monday=0, Sunday=6
if today >= 5: # Saturday(5) ya Sunday(6)
    st.warning("⚠️ Weekend: Market band hai. Monday ko wapas aaiye.")
    st.stop()

ticker = "GC=F"
# Data download karte waqt error handling
try:
    data = yf.download(ticker, period="5d", interval="15m")
    data = data.dropna()
except Exception as e:
    st.error("⚠️ Data load karne mein error aaya, kripya refresh karein.")
    st.stop()

if data.empty or len(data) < 50:
    st.info("⚠️ Data process ho raha hai, thodi der rukiye...")
    st.stop()

# Calculations
current_price = float(data['Close'].iloc[-1])
ema_200 = float(data['Close'].ewm(span=200, adjust=False).mean().iloc[-1])

delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / (loss + 0.00001)
rsi = (100 - (100 / (1 + rs))).iloc[-1]

volume = float(data['Volume'].iloc[-1])
avg_vol = float(data['Volume'].mean())

# Bias aur Score
bias = "BULLISH" if current_price > ema_200 else "BEARISH"
score = 50
if (bias == "BULLISH" and rsi < 65) or (bias == "BEARISH" and rsi > 35): score += 20
if volume > avg_vol: score += 20
if abs(current_price - ema_200) > 2: score += 10

# UI Display
st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
    <h3>Signal: {bias}</h3>
    <p><b>Accuracy Confidence:</b> {score}%</p>
    <p><b>Entry Price:</b> {current_price:.2f}</p>
    <p><b>RSI:</b> {rsi:.2f} | <b>Volume:</b> {'High' if volume > avg_vol else 'Low'}</p>
</div>
""", unsafe_allow_html=True)
