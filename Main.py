import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# Page Config
st.set_page_config(page_title="Institutional Pro v5.4", layout="wide")
st.title("🔴 XAUUSD Institutional Pro v5.4")

# Timeframe Selector
tf = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h", "4h", "1d"], index=1)
ticker = "GC=F"

# Data Fetching
@st.cache_data(ttl=60)
def get_data(tf):
    data = yf.download(ticker, period="5d" if tf in ["5m", "15m"] else "1mo", interval=tf, progress=False)
    return data.dropna()

data = get_data(tf)
price = float(data['Close'].values[-1])
# ATR for Dynamic TP
data['tr'] = data['High'] - data['Low']
atr = data['tr'].rolling(14).mean().values[-1]

# Session Logic (IST)
ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)
hour = now.hour

# Only Trade in London (12:30-16:00) & NY (18:00-22:00)
is_session = (12 <= hour < 16) or (18 <= hour < 22)

# Indicators
data['std'] = data['Close'].rolling(20).std()
data['mid'] = data['Close'].rolling(20).mean()
upper_band = float(data['mid'].values[-1] + (1.8 * data['std'].values[-1]))
lower_band = float(data['mid'].values[-1] - (1.8 * data['std'].values[-1]))
vol_spike = data['Volume'].values[-1] > (data['Volume'].rolling(20).mean().values[-1] * 1.2)

# Logic
sentiment_bullish = (price > upper_band) and vol_spike
sentiment_bearish = (price < lower_band) and vol_spike

# Signal Processing
if not is_session:
    signal, color = "MARKET OUT OF SESSION", "#64748b"
    display_entry = "<i>Waiting for London/NY Session...</i>"
    sl, tp = None, None
else:
    if sentiment_bullish and price < (upper_band + 2.0):
        signal, color = "INSTITUTIONAL BUY (Pro)", "#22c55e"
        sl, tp = price - (atr*1.5), price + (atr*3)
        display_entry = f"<b>Entry:</b> {price:.2f}"
    elif sentiment_bearish and price > (lower_band - 2.0):
        signal, color = "INSTITUTIONAL SELL (Pro)", "#ef4444"
        sl, tp = price + (atr*1.5), price - (atr*3)
        display_entry = f"<b>Entry:</b> {price:.2f}"
    else:
        signal, color = "WAITING FOR PRO SIGNAL", "#f59e0b"
        display_entry = f"<i>Monitor: {price:.2f}</i>"
        sl, tp = None, None

# UI
st.markdown(f"""
<div style="background-color: #1e293b; padding: 25px; border-radius: 15px; border-left: 12px solid {color}; color: #f8fafc;">
    <h1 style="margin:0; color:{color};">{signal}</h1>
    <p><b>Time:</b> {now.strftime('%H:%M:%S')} | <b>TF:</b> {tf}</p>
    <hr>
    <p style="font-size: 1.3rem;">{display_entry}</p>
    {f'<p style="color:#ff6b6b;"><b>SL:</b> {sl:.2f}</p><p style="color:#51cf66;"><b>TP:</b> {tp:.2f}</p>' if sl else '<p>Searching for liquidity...</p>'}
</div>
""", unsafe_allow_html=True)

# Audio Alert Trigger (JS hack for Streamlit)
if signal in ["INSTITUTIONAL BUY (Pro)", "INSTITUTIONAL SELL (Pro)"]:
    st.write("🔊 **SIGNAL DETECTED!**")
    
