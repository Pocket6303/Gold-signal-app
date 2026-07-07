import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Institutional Pro v5.13", layout="wide")
st.title("🔴 XAUUSD Institutional Pro v5.13 (Live Spot Feed)")

# Sidebar Controls
tf = st.sidebar.selectbox("Select Timeframe", ["15m", "1h", "4h", "1d"], index=0)
force_signal = st.sidebar.checkbox("🚀 Force Active Session", value=True)

# Switched to Direct Spot Ticker for XAUUSD matching broker spot
ticker = "XAUUSD=X"

@st.cache_data(ttl=60)
def get_data(tf):
    data = yf.download(ticker, period="1mo", interval=tf, progress=False)
    # Fallback to GC=F if spot feed is empty or limited on yfinance
    if data.empty:
        data = yf.download("GC=F", period="1mo", interval=tf, progress=False)
    return data

data = get_data(tf)
if data.empty:
    st.error("Data unavailable.")
    st.stop()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
data = data.dropna()

price = float(data['Close'].iloc[-1])
data['tr'] = data['High'] - data['Low']
atr = data['tr'].rolling(14).mean().iloc[-1]

# Timezone & Session
ny_tz = pytz.timezone('America/New_York')
now_ny = datetime.now(ny_tz)
hour_ny = now_ny.hour
is_session = (19 <= hour_ny) or (hour_ny < 17) or force_signal

# Indicators & Structure
data['std'] = data['Close'].rolling(20).std()
data['mid'] = data['Close'].rolling(20).mean()
upper_band = float(data['mid'].iloc[-1] + (1.5 * data['std'].iloc[-1]))
lower_band = float(data['mid'].iloc[-1] - (1.5 * data['std'].iloc[-1]))
vol_spike = data['Volume'].iloc[-1] > (data['Volume'].rolling(20).mean().iloc[-1] * 1.05)

# High-TF Order Block & MSS Proxy
prev_high = data['High'].iloc[-10:-2].max()
prev_low = data['Low'].iloc[-10:-2].min()
mss_bullish = (price > prev_high) and vol_spike
mss_bearish = (price < prev_low) and vol_spike

approaching_bullish_ob = price <= prev_low + (atr * 1.5) and price > prev_low + (atr * 0.8)
approaching_bearish_ob = price >= prev_high - (atr * 1.5) and price < prev_high - (atr * 0.8)

bullish_ob_valid = price <= prev_low + (atr * 0.8)
bearish_ob_valid = price >= prev_high - (atr * 0.8)

# Logic with Live Spot Price
sl, tp = None, None
if not is_session:
    signal, color = "MARKET OUT OF SESSION", "#64748b"
    display_entry = f"<i>NY Time: {now_ny.strftime('%H:%M')} - Waiting...</i>"
else:
    if bearish_ob_valid and mss_bearish:
        signal, color = "INSTITUTIONAL SELL (MSS + OB Confirmed)", "#ef4444"
        sl = price + (atr*1.5)
        tp = "HOLD (Trailing SL)"
        display_entry = f"<b>Spot Entry:</b> {price:.2f} | <b>Status:</b> Sell Executed"
    elif bullish_ob_valid and mss_bullish:
        signal, color = "INSTITUTIONAL BUY (MSS + OB Confirmed)", "#22c55e"
        sl = price - (atr*1.5)
        tp = "HOLD (Trailing SL)"
        display_entry = f"<b>Spot Entry:</b> {price:.2f} | <b>Status:</b> Buy Executed"
    elif approaching_bullish_ob or approaching_bearish_ob:
        signal, color = "PRE-ALERT: SETUP FORMING", "#f59e0b"
        display_entry = f"<i>Price approaching spot zone. Get ready in 5-10 mins! | Spot Price: {price:.2f}</i>"
    else:
        signal, color = "SCANNING MARKET STRUCTURE", "#64748b"
        display_entry = f"<i>Live Spot Feed Active | Price: {price:.2f}</i>"

# UI
st.markdown(f"""
<div style="background-color: #1e293b; padding: 25px; border-radius: 15px; border-left: 12px solid {color}; color: #f8fafc;">
    <h1 style="margin:0; color:{color}; font-size: 1.8rem;">{signal}</h1>
    <p><b>NY Time:</b> {now_ny.strftime('%H:%M:%S')} | <b>TF:</b> {tf} | <b>Feed:</b> Spot (XAUUSD=X)</p>
    <hr style="border-color: #475569;">
    <p style="font-size: 1.3rem;">{display_entry}</p>
    {f'<p style="color:#ff6b6b; font-size:1.2rem;"><b>Initial SL:</b> {sl:.2f}</p><p style="color:#51cf66; font-size:1.2rem;"><b>TP:</b> {tp}</p>' if sl is not None else '<p style="color:#94a3b8;">Monitoring live spot structure...</p>'}
</div>
""", unsafe_allow_html=True)
