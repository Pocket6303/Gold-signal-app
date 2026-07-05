import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")

st.title("🔴 XAUUSD Institutional Terminal v2.0")

# Fetch Data
ticker = "GC=F"
data = yf.download(ticker, period="5d", interval="15m")

# DATA SAFETY BLOCK
if data is None or data.empty:
    st.warning("⚠️ Data nahi mil raha hai (Market band ho sakta hai).")
else:
    # Saara calculation sirf tab hoga agar data valid hoga
    data = data.dropna()
    
    if len(data) < 200:
        st.warning("⚠️ Data analysis ke liye insufficient hai (Monday ka intezar karein).")
    else:
        current_price = data['Close'].iloc[-1]
        
        # Calculations
        ema_200 = data['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        volume = data['Volume'].iloc[-1]
        avg_vol = data['Volume'].mean()

        bias = "BULLISH" if current_price > ema_200 else "BEARISH"
        score = 50
        if (bias == "BULLISH" and rsi < 65) or (bias == "BEARISH" and rsi > 35): score += 20
        if volume > avg_vol: score += 20
        if abs(current_price - ema_200) > 2: score += 10
        
        acc_class = "acc-high" if score >= 80 else "acc-low"

        # UI Display
        st.markdown(f"""
        <div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
            <h3>Signal: {bias}</h3>
            <p>Accuracy Confidence: {score}%</p>
            <p>Entry Price: {current_price:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
