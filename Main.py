import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")

st.markdown("""
<style>
.card { background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8; }
.title { font-size: 24px; font-weight: bold; color: #f8fafc; }
.acc-high { color: #10b981; font-weight: bold; }
.acc-low { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🔴 XAUUSD Institutional Terminal v2.0")

ticker = "GC=F"
data = yf.download(ticker, period="1d", interval="15m")

if not data.empty:
    current_price = data['Close'].iloc[-1]
    
    # EMA 200 (Pandas calculation)
    ema_200 = data['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
    
    # RSI (Pandas calculation)
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="title">Signal: {bias}</div>
            <p>Accuracy Confidence: <span class="{acc_class}">{score}%</span></p>
            <p>Entry: <b>{current_price:.2f}</b></p>
            <p>SL/TP: {f"SL: {current_price-8:.2f} | TP: {current_price+24:.2f}" if bias=="BULLISH" else f"SL: {current_price+8:.2f} | TP: {current_price-24:.2f}"}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("Confluence Analysis")
        st.write(f"📊 **RSI Strength:** {rsi:.2f}")
        st.write(f"📈 **Trend Position:** {'Above' if current_price > ema_200 else 'Below'} 200 EMA")
        st.write(f"⚖️ **Volume Flow:** {'Institutional' if volume > avg_vol else 'Retail'}")
else:
    st.error("Data load nahi ho raha hai.")
        
