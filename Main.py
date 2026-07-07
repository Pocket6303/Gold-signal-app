import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="XAUUSD Master Institutional Engine v5.44.1", layout="wide")
st.title("🏛️ XAUUSD Master Institutional Engine v5.44.1")

ticker = "XAUUSD=X"
JOURNAL_FILE = "trade_journal.json"
IST_TZ = pytz.timezone('Asia/Kolkata')

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, "r") as f:
                data = json.load(f)
                now = datetime.now(IST_TZ)
                return [i for i in data if (now - datetime.fromisoformat(i['timestamp'])).days < 30]
        except:
            return []
    return []

def log_trade(signal_type, entry_p, sl_p):
    journal = load_journal()
    now_str = datetime.now(IST_TZ).isoformat()
    if journal and (datetime.now(IST_TZ) - datetime.fromisoformat(journal[-1]['timestamp'])).seconds < 900:
        return
    journal.append({"timestamp": now_str, "type": signal_type, "entry": entry_p, "sl": sl_p, "risk_points": abs(entry_p - sl_p)})
    try:
        with open(JOURNAL_FILE, "w") as f:
            json.dump(journal, f, indent=4)
    except:
        pass

# Sidebar with Fixed Offset & Filters
tf = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "30m", "1h"], index=1)
manual_offset = st.sidebar.slider("Fixed Offset ($)", -100.0, 100.0, -14.0, 0.25)
force_signal = st.sidebar.checkbox("🚀 Force Active Session", value=True)

@st.cache_data(ttl=10)
def get_data(tf):
    data = yf.download(ticker, period="5d", interval=tf, progress=False)
    daily = yf.download(ticker, period="10d", interval="1d", progress=False)
    if data.empty: data = yf.download("GC=F", period="5d", interval=tf, progress=False)
    if daily.empty: daily = yf.download("GC=F", period="10d", interval="1d", progress=False)
    return data, daily

data, daily = get_data(tf)

if data.empty or len(data) < 10:
    st.warning("⚠️ Market data syncing or unavailable. Please wait...")
    st.stop()

if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
if isinstance(daily.columns, pd.MultiIndex): daily.columns = daily.columns.get_level_values(0)

data = data.dropna()
raw_price = float(data['Close'].iloc[-1])
price = raw_price + manual_offset
pdh = float(daily['High'].iloc[-2]) + manual_offset if not daily.empty and len(daily) >= 2 else price + 10
pdl = float(daily['Low'].iloc[-2]) + manual_offset if not daily.empty and len(daily) >= 2 else price - 10

# Cumulative Layers Stack
data['ema_50'] = data['Close'].ewm(span=50, adjust=False).mean() + manual_offset
data['atr'] = (data['High'] - data['Low']).rolling(14).mean()
lookback_asian = min(24, len(data))
asian_high = data['High'].iloc[-lookback_asian:].max() + manual_offset
asian_low = data['Low'].iloc[-lookback_asian:].min() + manual_offset

is_pdh_sweep = price > pdh and price < (pdh + 3)
is_pdl_sweep = price < pdl and price > (pdl - 3)
roll_len = min(10, len(data) - 1)
mss_bull = price > data['High'].rolling(roll_len).max().iloc[-2] + manual_offset if roll_len > 1 else False
mss_bear = price < data['Low'].rolling(roll_len).min().iloc[-2] + manual_offset if roll_len > 1 else False

now_ist = datetime.now(IST_TZ)

# Engine with Early Clock Alert
signal, color, details, sl, tp = "SCANNING MARKET STRUCTURE", "#64748b", "Monitoring indicator layers & institutional liquidity...", None, None

if abs(price - pdh) <= (data['atr'].iloc[-1] * 0.5) or abs(price - asian_high) <= (data['atr'].iloc[-1] * 0.5):
    signal, color = "⏱️ BE READY: Price Approaching High Liquidity Zone", "#f59e0b"
    details = "<b>Strategy Warning:</b> Price is testing upper boundaries (PDH / Asian High). Prepare for potential sweep reaction."
elif abs(price - pdl) <= (data['atr'].iloc[-1] * 0.5) or abs(price - asian_low) <= (data['atr'].iloc[-1] * 0.5):
    signal, color = "⏱️ BE READY: Price Approaching Low Liquidity Zone", "#f59e0b"
    details = "<b>Strategy Warning:</b> Price is testing lower boundaries (PDL / Asian Low). Prepare for potential sweep reaction."

if is_pdh_sweep and mss_bear and (price < data['ema_50'].iloc[-1]):
    signal, color = "SELL: Institutional PDH Liquidity Sweep + LTF MSS", "#ef4444"
    sl, tp = price + (data['atr'].iloc[-1] * 1.5), f"Target Session Low: {asian_low:.2f}"
    details = f"<b>Execution Reason:</b> High-side liquidity grab at PDH combined with a bearish Market Structure Shift (MSS) under the 50-EMA trend line."
    log_trade("SELL", price, sl)
elif is_pdl_sweep and mss_bull and (price > data['ema_50'].iloc[-1]):
    signal, color = "BUY: Institutional PDL Liquidity Sweep + LTF MSS", "#22c55e"
    sl, tp = price - (data['atr'].iloc[-1] * 1.5), f"Target Session High: {asian_high:.2f}"
    details = f"<b>Execution Reason:</b> Low-side liquidity grab at PDL combined with a bullish Market Structure Shift (MSS) above the 50-EMA trend line."
    log_trade("BUY", price, sl)

# Display Dashboard with IST Timestamp
st.markdown(f"""
<div style="background-color: #0f172a; padding: 30px; border-radius: 16px; border-left: 14px solid {color}; color: #f8fafc;">
    <h1 style="margin:0 0 10px 0; color:{color}; font-size: 1.8rem;">{signal}</h1>
    <p style="margin:4px 0; color:#94a3b8;"><b>Price:</b> {price:.2f} | <b>ATR:</b> {data['atr'].iloc[-1]:.2f} | <b>Offset:</b> {manual_offset:+.2f}$</p>
    <p style="margin:0 0 15px 0; color:#cbd5e1; font-size: 0.9rem;">🕒 IST Time: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p style="margin:12px 0 0 0; font-size: 1.1rem; color:#e2e8f0;">{details}</p>
    {f'<p style="color:#ff6b6b; margin:10px 0 0 0;"><b>SL:</b> {sl:.2f}</p><p style="color:#51cf66; margin:4px 0 0 0;"><b>TP:</b> {tp}</p>' if sl else ''}
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.subheader("📅 30-Day Automated Performance Journal")
j_data = load_journal()
if j_data: st.dataframe(pd.DataFrame(j_data), use_container_width=True)
else: st.info("No trades logged in the 30-day window yet.")
    
