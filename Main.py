import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import json

st.set_page_config(page_title="Institutional Pro v5.28", layout="wide")
st.title("🔴 XAUUSD Institutional Pro v5.28 (Auto-Journaling Feed)")

ticker = "XAUUSD=X"
JOURNAL_FILE = "trade_journal.json"
IST_TZ = pytz.timezone('Asia/Kolkata')

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            with open(JOURNAL_FILE, "r") as f:
                data = json.load(f)
                # Auto-purge records older than 30 days
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
    # Check if last logged trade is too recent to avoid duplicate spam for the same bar
    if journal:
        last_t = datetime.fromisoformat(journal[-1]['timestamp'])
        if (datetime.now(IST_TZ) - last_t).seconds < 900:  # 15 mins cooldown per signal log
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
    data = yf.download(ticker, period="5d", interval=tf, progress=False)
    if data.empty:
        data = yf.download("GC=F", period="5d", interval=tf, progress=False)
    return data

tf = st.sidebar.selectbox("Select Timeframe", ["15m", "1h", "4h", "1d"], index=0)
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

now_ist = datetime.now(IST_TZ)
hour_ist = now_ist.hour

is_asian = (22 <= hour_ist) or (hour_ist < 7)
is_london = (12 <= hour_ist < 22)
is_ny = (17 <= hour_ist) or (hour_ist < 3)
is_london_close = (19 <= hour_ist) or (hour_ist < 2)

active_sessions = []
if is_asian: active_sessions.append("Asian")
if is_london: active_sessions.append("London")
if is_ny: active_sessions.append("New York")
if is_london_close: active_sessions.append("London Close")

is_session = len(active_sessions) > 0 or force_signal

# Indicators & Structure
data['std'] = data['Close'].rolling(20).std()
data['mid'] = data['Close'].rolling(20).mean()
upper_band = float(data['mid'].iloc[-1] + (1.5 * data['std'].iloc[-1])) + manual_offset
lower_band = float(data['mid'].iloc[-1] - (1.5 * data['std'].iloc[-1])) + manual_offset

vol_spike = data['Volume'].iloc[-1] > (data['Volume'].rolling(20).mean().iloc[-1] * 1.05)
prev_high = data['High'].iloc[-10:-2].max() + manual_offset
prev_low = data['Low'].iloc[-10:-2].min() + manual_offset
mss_bullish = (price > prev_high) and vol_spike
mss_bearish = (price < prev_low) and vol_spike

approaching_bullish_ob = price <= prev_low + (atr * 1.5) and price > prev_low + (atr * 0.8)
approaching_bearish_ob = price >= prev_high - (atr * 1.5) and price < prev_high - (atr * 0.8)

bullish_ob_valid = price <= prev_low + (atr * 0.8)
bearish_ob_valid = price >= prev_high - (atr * 0.8)

sl, tp = None, None
if not is_session:
    signal, color = "MARKET OUT OF SESSION", "#64748b"
    display_entry = f"<i>IST Time: {now_ist.strftime('%H:%M')} - Waiting...</i>"
else:
    if bearish_ob_valid and mss_bearish:
        signal, color = "INSTITUTIONAL SELL (MSS + OB Confirmed)", "#ef4444"
        sl = price + (atr*1.5)
        tp = "HOLD (Trailing SL)"
        display_entry = f"<b>Auto-Corrected Mode Active | Price:</b> {price:.2f}"
        log_trade("SELL", price, sl)
    elif bullish_ob_valid and mss_bullish:
        signal, color = "INSTITUTIONAL BUY (MSS + OB Confirmed)", "#22c55e"
        sl = price - (atr*1.5)
        tp = "HOLD (Trailing SL)"
        display_entry = f"<b>Auto-Corrected Mode Active | Price:</b> {price:.2f}"
        log_trade("BUY", price, sl)
    elif approaching_bullish_ob or approaching_bearish_ob:
        signal, color = "PRE-ALERT: SETUP FORMING", "#f59e0b"
        display_entry = f"<i>Price approaching institutional zone. Get ready! | Price: {price:.2f}</i>"
    else:
        signal, color = "SCANNING MARKET STRUCTURE", "#64748b"
        display_entry = f"<i>Auto-Corrected Mode Active | Price: {price:.2f}</i>"

st.markdown(f"""
<div style="background-color: #1e293b; padding: 25px; border-radius: 15px; border-left: 12px solid {color}; color: #f8fafc;">
    <h1 style="margin:0; color:{color}; font-size: 1.8rem;">{signal}</h1>
    <p><b>IST Time:</b> {now_ist.strftime('%H:%M:%S')} | <b>TF:</b> {tf} | <b>Fixed Offset:</b> {manual_offset:+.2f}$</p>
    <hr style="border-color: #475569;">
    <p style="font-size: 1.3rem;">{display_entry}</p>
    {f'<p style="color:#ff6b6b; font-size:1.2rem;"><b>Initial SL:</b> {sl:.2f}</p><p style="color:#51cf66; font-size:1.2rem;"><b>TP:</b> {tp}</p>' if sl is not None else '<p style="color:#94a3b8;">Monitoring synchronized structure...</p>'}
</div>
""", unsafe_allow_html=True)

# --- TRADITIONAL MONTHLY JOURNAL SECTION ---
st.markdown("---")
st.subheader("📅 30-Day Automated Performance Journal")
journal_data = load_journal()

col1, col2, col3 = st.columns(3)
total_logged = len(journal_data)
col1.metric("Total Signals Logged (30d Cycle)", total_logged)
col2.metric("Active Offset Buffer", f"{manual_offset}$")
col3.metric("Storage Status", "Auto-Purge Active (<30 Days)")

if journal_data:
    df_journal = pd.DataFrame(journal_data)
    st.dataframe(df_journal, use_container_width=True)
else:
    st.info("No trades or signals logged in the current 30-day window yet. They will appear here automatically when triggered.")
