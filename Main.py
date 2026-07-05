import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

st.set_page_config(page_title="Gold SMC Pro Terminal", layout="wide")

# Styling
st.markdown("""
<style>
    .card { background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8; }
    .title { font-size: 24px; font-weight: bold; color: #f8fafc; }
    .acc-high { color: #10b981; font-weight: bold; }
    .acc-low { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 XAUUSD Institutional Terminal v2.0")

# Fetch Data
ticker = "GC=F"
data = yf.download(ticker, period="1d", interval="15m")

if not data.empty:
    current_price = data['Close'].iloc[-1]
    ema_200 = ta.ema(data['Close'], length=200).iloc[-1]
    rsi = ta.rsi(data['Close'], length=14).iloc[-1]
    volume = data['Volume'].iloc[-1]
    avg_vol = data['Volume'].mean()

    # Logic Engine & Accuracy Calculation
    bias = "BULLISH" if current_price > ema_200 else "BEARISH"
    
    # Accuracy Formula
    score = 50 # Base score
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
            <p style="color:#ef4444;">SL: {(current_price-8 if bias=='BULLISH' else current_price+8):.2f}</p>
            <p style="color:#10b981;">TP: {(current_price+24 if bias=='BULLISH' else current_price-24):.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Confluence Analysis")
        st.write(f"📊 **RSI Strength:** {rsi:.2f}")
        st.write(f"📈 **Trend Position:** {'Above' if current_price > ema_200 else 'Below'} 200 EMA")
        st.write(f"🔊 **Volume Flow:** {'Institutional' if volume > avg_vol else 'Retail'}")

else:
    st.error("Data load nahi ho raha.")

