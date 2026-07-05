import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v2.0")

ticker = "GC=F"
data = yf.download(ticker, period="5d", interval="15m")

# Data saaf karein
data = data.dropna()

# Check: Agar data mein numerical values nahi hain ya khali hai
if data.empty or data['Close'].isnull().all():
    st.warning("⚠️ Sunday: Market band hai, koi valid data nahi mila.")
    st.stop()

# Safety calculation: iloc ke jagah values access karein
current_price = float(data['Close'].iloc[-1])
ema_200 = float(data['Close'].ewm(span=200, adjust=False).mean().iloc[-1])

bias = "BULLISH" if current_price > ema_200 else "BEARISH"
score = 50

st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
    <h3>Signal: {bias}</h3>
    <p>Entry Price: {current_price:.2f}</p>
</div>
""", unsafe_allow_html=True)
