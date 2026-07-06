import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Institutional Pro v5.6", layout="wide")
st.title("🔴 XAUUSD Institutional Pro v5.6 (Master Control)")

# Sidebar Controls
tf = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h", "4h", "1d"], index=1)
force_signal = st.sidebar.checkbox("🚀 Force Active Session (Manual Override)")

ticker = "GC=F"

# Data Fetching
@st.cache_data(ttl=60)
def get_data(tf):
    data = yf.download(ticker, period="5d" if tf in ["5m", "15m"] else "1mo", interval=tf, progress=False)
    return data

data = get_data(tf)
if data.empty:
    st.error("Market data temporarily unavailable.")
    st.stop()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
data = data.dropna()

price = float(data['Close'].iloc[-1])
data['tr'] = data['High'] - data['Low']
atr = data['tr'].rolling(14).mean().iloc[-1]

# Session Logic
ny_tz = pytz.timezone('America/New_York')
now_ny = datetime.now(ny_tz)
hour_ny = now_ny.hour
# London (3-7) or NY (8-12)
is_session = (3 <= hour_ny < 7) or (8 <= hour_ny < 12) or force_signal

# Indicators
data['std'] = data['Close'].rolling(20).std()
data['mid'] = data['Close'].rolling(20).mean()
upper_band = float(data['mid'].iloc[-1] + (1.8 * data['std'].iloc[-1]))
lower_band = float(data['mid'].iloc[-1] - (1.8 * data['std'].iloc[-1]))
vol_spike = data['Volume'].iloc[-1] > (data['Volume'].rolling(20).mean().iloc[-1] * 1.2)

# Logic
sentiment_bullish = (price > upper_band) and vol_spike
sentiment_bearish = (price < lower_band) and vol_spike

# UI
if not is_session:
    signal, color = "MARKET OUT OF SESSION", "#64748b"
    display_entry = f"<i>NY Time: {now_ny.strftime('%H:%M')} - Waiting for session...</i>"
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
        display_entry = f"<i>Market Active | Price: {price:.2f}</i>"
        sl, tp = None, None

st.markdown(f"""
<div style="background-color: #1e293b; padding: 25px; border-radius: 15px; border-left: 12px solid {color}; color: #f8fafc;">
    <h1 style="margin:0; color:{color}; font-size: 1.8rem;">{signal}</h1>
    <p><b>NY Time:</b> {now_ny.strftime('%H:%M:%S')} | <b>TF:</b> {tf} {'(Manual Override ON)' if force_signal else ''}</p>
    <hr style="border-color: #475569;">
    <p style="font-size: 1.3rem;">{display_entry}</p>
    {f'<p style="color:#ff6b6b; font-size:1.2rem;"><b>SL:</b> {sl:.2f}</p><p style="color:#51cf66; font-size:1.2rem;"><b>TP:</b> {tp:.2f}</p>' if sl else '<p style="color:#94a3b8;">Searching for liquidity...</p>'}
</div>
""", unsafe_allow_html=True)
