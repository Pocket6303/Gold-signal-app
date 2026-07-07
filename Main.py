import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="XAUUSD Master Ultimate v5.41", layout="wide")
st.title("🏛️ XAUUSD Master Cumulative Institutional Engine v5.41")

ticker = "XAUUSD=X"
JOURNAL_FILE = "trade_journal.json"
IST_TZ = pytz.timezone('Asia/Kolkata')

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, "r") as f:
                data = json.load(f)
                now = datetime.now(IST_TZ)
                filtered = []
                for item in data:
                    t_time = datetime.fromisoformat(item['timestamp'])
                    if (now - t_time).days < 30:
                        filtered.append(item)
                return filtered
        except:
            return []
    return []

def log_trade(signal_type, entry_p, sl_p):
    journal = load_journal()
    now_str = datetime.now(IST_TZ).isoformat()
    if journal:
        last_t = datetime.fromisoformat(journal[-1]['timestamp'])
        if (datetime.now(IST_TZ) - last_t).seconds < 900:
            return
            
    trade_entry = {
        "timestamp": now_str,
        "type": signal_type,
        "entry": entry_p,
        "sl": sl_p,
        "risk_points": abs(entry_p - sl_p)
    }
    journal.append(trade_entry)
    try:
        with open(JOURNAL_FILE, "w") as f:
            json.dump(journal, f, indent=4)
    except:
        pass

# Sidebar Configuration
tf = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "30m", "1h"], index=1)
manual_offset = st.sidebar.slider("Fixed Offset ($)", -50.0, 50.0, -14.0, 0.25)
force_signal = st.sidebar.checkbox("🚀 Force Active Session", value=True)

@st.cache_data(ttl=10)
def get_data(tf):
    data = yf.download(ticker, period="5d", interval=tf, progress=False)
    daily = yf.download(ticker, period="5d", interval="1d", progress=False)
    if data.empty:
        data = yf.download("GC=F", period="5d", interval=tf, progress=False)
    return data, daily

data, daily = get_data(tf)

if data.empty or len(data) < 20:
    st.warning("⚠️ Market data loading or syncing. Please hold on...")
    st.stop()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
if isinstance(daily.columns, pd.MultiIndex):
    daily.columns = daily.columns.get_level_values(0)

data = data.dropna()
raw_price = float(data['Close'].iloc[-1])
price = raw_price + manual_offset

# --- C CUMULATIVE INDICATOR STACK (All past tools intact) ---
data['mid'] = data['Close'].rolling(20).mean() + manual_offset
data['std'] = data['Close'].rolling(20).std()
data['ema_50'] = data['Close'].ewm(span=50, adjust=False).mean() + manual_offset
data['atr'] = (data['High'] - data['Low']).rolling(14).mean()

delta = data['Close'].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = -delta.clip(upper=0).rolling(14).mean()
data['rsi'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

# Session & Daily Liquidity Bounds (Cumulative)
asian_high = data['High'].iloc[-24:].max() + manual_offset
asian_low = data['Low'].iloc[-24:].min() + manual_offset
pdh = float(daily['High'].iloc[-2]) + manual_offset
pdl = float(daily['Low'].iloc[-2]) + manual_offset

# Structure & Sweep Detections
vol_spike = data['Volume'].iloc[-1] > (data['Volume'].rolling(20).mean().iloc[-1] * 1.01)
is_pdh_sweep = price > pdh and price < (pdh + 3)
is_pdl_sweep = price < pdl and price > (pdl - 3)
is_asian_high_sweep = price > asian_high and price < (asian_high + 2.5)
is_asian_low_sweep = price < asian_low and price > (asian_low - 2.5)

mss_bull = price > data['High'].rolling(10).max().iloc[-2] + manual_offset
mss_bear = price < data['Low'].rolling(10).min().iloc[-2] + manual_offset

# --- ADVANCED CONFLUENCE & MULTI-STRATEGY DECISION ENGINE ---
now_ist = datetime.now(IST_TZ)
hour_ist = now_ist.hour
is_active_session = (22 <= hour_ist) or (hour_ist < 7) or (12 <= hour_ist < 22) or force_signal

signal, color, display_detail, sl, tp = "SCANNING MARKET STRUCTURE", "#64748b", "Monitoring all layers for institutional setup...", None, None

if is_active_session:
    if (is_pdh_sweep or is_asian_high_sweep) and mss_bear and (price < data['ema_50'].iloc[-1]):
        signal, color = "SELL: Liquidity Sweep (PDH/Session) + LTF MSS", "#ef4444"
        sl = price + (data['atr'].iloc[-1] * 1.5)
        tp = f"Targeting Session Low: {asian_low:.2f}"
        display_detail = f"High liquidity grabbed, structure shifted bearish | Price: {price:.2f}"
        log_trade("SELL", price, sl)
    elif (is_pdl_sweep or is_asian_low_sweep) and mss_bull and (price > data['ema_50'].iloc[-1]):
        signal, color = "BUY: Liquidity Sweep (PDL/Session) + LTF MSS", "#22c55e"
        sl = price - (data['atr'].iloc[-1] * 1.5)
        tp = f"Targeting Session High: {asian_high:.2f}"
        display_detail = f"Low liquidity grabbed, structure shifted bullish | Price: {price:.2f}"
        log_trade("BUY", price, sl)
    elif abs(price - pdh) <= (data['atr'].iloc[-1] * 0.4) or abs(price - pdl) <= (data['atr'].iloc[-1] * 0.4):
        signal, color = "⚡ PREPARE: Price Approaching Key Liquidity Zone", "#f59e0b"
        display_detail = f"Watching for potential sweep & MSS reaction | Price: {price:.2f}"

st.markdown(f"""
<div style="background-color: #0f172a; padding: 25px; border-radius: 15px; border-left: 12px solid {color}; color: #f8fafc;">
    <h2 style="margin:0; color:{color};">{signal}</h2>
    <p><b>IST Time:</b> {now_ist.strftime('%H:%M:%S')} | <b>TF:</b> {tf} | <b>Offset:</b> {manual_offset:+.2f}$ | <b>ATR:</b> {data['atr'].iloc[-1]:.2f}</p>
    <p><b>Levels:</b> PDH: {pdh:.2f} | PDL: {pdl:.2f} | Asian High: {asian_high:.2f} | Asian Low: {asian_low:.2f}</p>
    <hr style="border-color: #475569;">
    <p style="font-size: 1.2rem;">{display_detail}</p>
    {f'<p style="color:#ff6b6b;"><b>SL:</b> {sl:.2f}</p><p style="color:#51cf66;"><b>TP:</b> {tp}</p>' if sl is not None else ''}
</div>
""", unsafe_allow_html=True)

# --- 30-DAY AUTOMATED PERFORMANCE JOURNAL ---
st.markdown("---")
st.subheader("📅 30-Day Automated Performance Journal")
journal_data = load_journal()
if journal_data:
    st.dataframe(pd.DataFrame(journal_data), use_container_width=True)
else:
    st.info("No trades logged in the current 30-day window yet.")
    
