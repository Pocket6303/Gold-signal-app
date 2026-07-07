import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import os
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Institutional Hybrid v5.30", layout="wide")
st.title("🔴 XAUUSD Hybrid Pro v5.30 (Liquidity + MSS + OB)")

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
    
