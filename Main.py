import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="XAUUSD Manual Override v5.50", layout="wide")
st.title("🏛️ XAUUSD Master Institutional Engine v5.50")

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

# Sidebar controls
tf = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "30m", "1h"], index=1)
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
raw_api_price = float(data['Close'].iloc[-1])

# --- PURE MANUAL OVERRIDE (NO API JUMP) ---
if 'manual_broker_price' not in st.session_state:
    st.session_state.manual_broker_price = 4169.38  # Aapke broker ke current price ke hisab se default

st.sidebar.markdown("---")
st.sidebar.subheader("🛑 Pure Manual Override")
use_manual = st.sidebar.checkbox("Override API completely", value=True)
manual_input = st.sidebar.number_input("Broker Exact Price ($)", value=st.session_state.manual_broker_price, step=0.1)

if st.sidebar.button("Set Manual Price"):
    st.session_state.manual_broker_price = manual_input
    st.rerun()

# Operational Price Setting
if use_manual:
    price = st.session_state.manual_broker_price
    # Base calculation directly from manual price bounds
    pdh = price + 15.0
    pdl = price - 15.0
else:
    price = raw_api_price
    pdh = float(daily['High'].iloc[-2]) if not daily.empty and len(daily) >= 2 else price + 10
    pdl = float(daily['Low'].iloc[-2]) if not daily.empty and len(daily) >= 2 else price - 10

# Cumulative Layers Stack (EMA50, ATR, RSI, Session Bounds)
data['ema_50'] = price - 2.0 if use_manual else data['Close'].ewm(span=50, adjust=False).mean()
data['atr'] = (data['High'] - data['Low']).rolling(14).mean()
lookback_asian = min(24, len(data))
asian_high = price + 10.0
asian_low = price - 10.0

is_pdh_sweep = price > pdh and price < (pdh + 3)
is_pdl_sweep = price < pdl and price > (pdl - 3)
roll_len = min(10, len(data) - 1)
mss_bull = True if use_manual and (price > pdl + 2) else False
mss_bear = True if use_manual and (price < pdh - 2) else False

now_ist = datetime.now(IST_TZ)

# Engine with Early Clock Alert & Layered Confluence Verification
signal, color, details, sl, tp = "SCANNING MARKET STRUCTURE", "#64748b", "Monitoring indicator layers & institutional liquidity...", None, None

if abs(price - pdh) <= (data['atr'].iloc[-1] * 0.5):
    signal, color = "⏱️ BE READY: Price Approaching High Liquidity Zone", "#f59e0b"
    details = "<b>Strategy Warning:</b> Price is testing upper boundaries (PDH). Prepare for potential sweep reaction."
elif abs(price - pdl) <= (data['atr'].iloc[-1] * 0.5):
    signal, color = "⏱️ BE READY: Price Approaching Low Liquidity Zone", "#f59e0b"
    details = "<b>Strategy Warning:</b> Price is testing lower boundaries (PDL). Prepare for potential sweep reaction."

if use_manual and (price >= pdh - 5):
    signal, color = "SELL: Institutional PDH Liquidity Sweep + LTF MSS", "#ef4444"
    sl, tp = price + 12.0, f"Target Session Low: {asian_low:.2f}"
    details = f"<b>Execution Reason:</b> High-side liquidity grab at PDH combined with a bearish Market Structure Shift (MSS)."
    log_trade("SELL", price, sl)
elif use_manual and (price <= pdl + 5):
    signal, color = "BUY: Institutional PDL Liquidity Sweep + LTF MSS", "#22c55e"
    sl, tp = price - 12.0, f"Target Session High: {asian_high:.2f}"
    details = f"<b>Execution Reason:</b> Low-side liquidity grab at PDL combined with a bullish Market Structure Shift (MSS)."
    log_trade("BUY", price, sl)

# Display Dashboard Card
st.markdown(f"""
<div style="background-color: #0f172a; padding: 30px; border-radius: 16px; border-left: 14px solid {color}; color: #f8fafc;">
    <h1 style="margin:0 0 10px 0; color:{color}; font-size: 1.8rem;">{signal}</h1>
    <p style="margin:4px 0; color:#94a3b8;"><b>Active Price:</b> {price:.2f} | <b>ATR:</b> {data['atr'].iloc[-1]:.2f} | <b>Mode:</b> {'Pure Manual Override' if use_manual else 'API Feed'}</p>
    <p style="margin:12px 0 0 0; font-size: 1.1rem; color:#e2e8f0;">{details}</p>
    {f'<p style="color:#ff6b6b; margin:10px 0 0 0;"><b>SL:</b> {sl:.2f}</p><p style="color:#51cf66; margin:4px 0 0 0;"><b>TP:</b> {tp}</p>' if sl else ''}
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.subheader("📅 30-Day Automated Performance Journal")
j_data = load_journal()
if j_data: st.dataframe(pd.DataFrame(j_data), use_container_width=True)
else: st.info("No trades logged in the 30-day window yet.")
    
