import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Institutional Master v5.32", layout="wide")
st.title("🔴 XAUUSD Master Hybrid Pro v5.32 (Session Sweep + 5M MSS + POI)")

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

@st.cache_data(ttl=10)
def get_data(tf):
    data = yf.download(ticker, period="3d", interval=tf, progress=False)
    if data.empty:
        data = yf.download("GC=F", period="3d", interval=tf, progress=False)
    return data

# Sidebar Configuration
tf = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "30m", "1h"], index=0)
force_signal = st.sidebar.checkbox("🚀 Force Active Session", value=True)
manual_offset = st.sidebar.slider("Fixed Offset ($)", -50.0, 50.0, -14.0, 0.25)

data = get_data(tf)
if data.empty:
    st.error("Data unavailable.")
    st.stop()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
data = data.dropna()

raw_price = float(data['Close'].iloc[-1])
price = raw_price + manual_offset

data['tr'] = data['High'] - data['Low']
atr = data['tr'].rolling(14).mean().iloc[-1]

# Session calculation (Asian Session ranges)
now_ist = datetime.now(IST_TZ)
hour_ist = now_ist.hour
is_asian = (22 <= hour_ist) or (hour_ist < 7)
is_london = (12 <= hour_ist < 22)
is_ny = (17 <= hour_ist) or (hour_ist < 3)

# Session High/Low approximation from recent bars
asian_high = data['High'].iloc[-24:].max() + manual_offset
asian_low = data['Low'].iloc[-24:].min() + manual_offset

# Liquidity Sweep & 5m MSS Logic
vol_spike = data['Volume'].iloc[-1] > (data['Volume'].rolling(20).mean().iloc[-1] * 1.01)

prev_high = data['High'].iloc[-10:-2].max() + manual_offset
prev_low = data['Low'].iloc[-10:-2].min() + manual_offset

# Sweep of session liquidity followed by structural shift (MSS)
sweep_asian_low_bullish = (price <= asian_low + (atr * 0.3)) and (price > asian_low) and vol_spike
sweep_asian_high_bearish = (price >= asian_high - (atr * 0.3)) and (price < asian_high) and vol_spike

mss_bullish = (price > prev_high) and vol_spike
mss_bearish = (price < prev_low) and vol_spike

# POI Retest check
retest_poi_bullish = (price <= prev_low + (atr * 0.8)) and mss_bullish
retest_poi_bearish = (price >= prev_high - (atr * 0.8)) and mss_bearish

sl, tp = None, None
if not (is_asian or is_london or is_ny or force_signal):
    signal, color = "MARKET OUT OF SESSION", "#64748b"
    display_entry = f"<i>IST Time: {now_ist.strftime('%H:%M')} - Waiting...</i>"
else:
    if sweep_asian_low_bullish or retest_poi_bullish:
        signal, color = "INSTITUTIONAL BUY (Session Sweep + 5M MSS + POI)", "#22c55e"
        sl = price - (atr * 1.5)
        tp = f"Targeting Asian High: {asian_high:.2f} (Trailing)"
        display_entry = f"<b>Liquidity Grabbed & POI Retested | Price:</b> {price:.2f}"
        log_trade("BUY", price, sl)
    elif sweep_asian_high_bearish or retest_poi_bearish:
        signal, color = "INSTITUTIONAL SELL (Session Sweep + 5M MSS + POI)", "#ef4444"
        sl = price + (atr * 1.5)
        tp = f"Targeting Asian Low: {asian_low:.2f} (Trailing)"
        display_entry = f"<b>Liquidity Grabbed & POI Retested | Price:</b> {price:.2f}"
        log_trade("SELL", price, sl)
    else:
        signal, color = "SCANNING MARKET STRUCTURE", "#64748b"
        display_entry = f"<i>Monitoring Session Liquidity (High: {asian_high:.2f} | Low: {asian_low:.2f})</i>"

st.markdown(f"""
<div style="background-color: #1e293b; padding: 25px; border-radius: 15px; border-left: 12px solid {color}; color: #f8fafc;">
    <h1 style="margin:0; color:{color}; font-size: 1.8rem;">{signal}</h1>
    <p><b>IST Time:</b> {now_ist.strftime('%H:%M:%S')} | <b>TF:</b> {tf} | <b>Offset:</b> {manual_offset:+.2f}$ | <b>ATR:</b> {atr:.2f}</p>
    <p><b>Session Liquidity Bounds:</b> High: {asian_high:.2f} / Low: {asian_low:.2f}</p>
    <hr style="border-color: #475569;">
    <p style="font-size: 1.3rem;">{display_entry}</p>
    {f'<p style="color:#ff6b6b; font-size:1.2rem;"><b>Initial SL:</b> {sl:.2f}</p><p style="color:#51cf66; font-size:1.2rem;"><b>TP/Hold:</b> {tp}</p>' if sl is not None else '<p style="color:#94a3b8;">Scanning manipulation & retest zones...</p>'}
</div>
""", unsafe_allow_html=True)

# --- AUTOMATED PERFORMANCE JOURNAL ---
st.markdown("---")
st.subheader("📅 30-Day Automated Performance Journal")
journal_data = load_journal()
if journal_data:
    st.dataframe(pd.DataFrame(journal_data), use_container_width=True)
else:
    st.info("No trades logged in the current 30-day window yet.")
