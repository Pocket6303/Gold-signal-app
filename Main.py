import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz # Timezone ke liye

st.set_page_config(page_title="Gold SWC Pro Terminal", layout="wide")
st.title("🔴 XAUUSD Institutional Terminal v2.0")

# 1. IST Timezone set karna
ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)

ticker = "GC=F"
try:
    data = yf.download(ticker, period="5d", interval="15m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.dropna()
except Exception as e:
    st.error("Data load error.")
    st.stop()

# 2. Calculations
current_price = float(data['Close'].values[-1])
ema_200 = float(data['Close'].ewm(span=200, adjust=False).mean().values[-1])

bias = "BULLISH" if current_price > ema_200 else "BEARISH"

# 3. 1:3 RR Calculation (Risk 2 pts, Reward 6 pts)
risk = 2.0
reward = 6.0
if bias == "BULLISH":
    sl = current_price - risk
    tp = current_price + reward
else:
    sl = current_price + risk
    tp = current_price - reward

# 4. Display
st.markdown(f"""
<div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #38bdf8;">
    <h2 style="margin:0;">Signal: {bias}</h2>
    <p style="font-size: 1.2rem; margin: 10px 0;"><b>Time (IST):</b> {now.strftime('%H:%M:%S')}</p>
    <hr style="border: 0.5px solid #475569;">
    <p style="font-size: 1.2rem; margin: 5px 0;"><b>Entry Price:</b> {current_price:.2f}</p>
    <p style="font-size: 1.2rem; margin: 5px 0; color: #ef4444;"><b>SL:</b> {sl:.2f}</p>
    <p style="font-size: 1.2rem; margin: 5px 0; color: #22c55e;"><b>TP:</b> {tp:.2f}</p>
</div>
""", unsafe_allow_html=True)
