import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v2.0")

# 1. Weekend Check
today = datetime.datetime.now().weekday()
if today >= 5:
    st.warning("⚠️ Weekend: Market band hai.")
    st.stop()

ticker = "GC=F"

try:
    data = yf.download(ticker, period="5d", interval="15m", progress=False)
    if data is None or data.empty:
        st.info("⚠️ Data load ho raha hai...")
        st.stop()
    
    # Fix: Agar multi-index column hai, toh sirf 'Close' aur 'Volume' lein
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
        
    data = data.dropna()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# 2. Calculation Fix: .iloc[-1] ke baad direct scalar access
try:
    # .item() sirf tab kaam karta hai jab wo single element ho
    current_price = float(data['Close'].iloc[-1])
    ema_200 = float(data['Close'].ewm(span=200, adjust=False).mean().iloc[-1])

    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 0.00001)
    rsi = float(rs.iloc[-1])
    
    volume = float(data['Volume'].iloc[-1])
    avg_vol = float(data['Volume'].mean())

    bias = "BULLISH" if current_price > ema_200 else "BEARISH"
    score = 50
    if (bias == "BULLISH" and rsi < 65) or (bias == "BEARISH" and rsi > 35): score += 20
    if volume > avg_vol: score += 20
    if abs(current_price - ema_200) > 2: score += 10

    st.markdown(f"""
    <div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
        <h3>Signal: {bias}</h3>
        <p><b>Accuracy:</b> {score}%</p>
        <p><b>Price:</b> {current_price:.2f}</p>
        <p><b>RSI:</b> {rsi:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Calculation Error: {e}")
    
