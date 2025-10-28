# pages/dashboard.py
import streamlit as st
import sqlite3
from stock_data import get_stock_quote, POPULAR_ASSETS

def show():
    # Safety check
    if 'user' not in st.session_state:
        st.error("Session expired. Please log in again.")
        st.session_state.page = "landing"
        st.rerun()
        return

    user_id = st.session_state.user['id']
    username = st.session_state.user['username']
    tier = st.session_state.user['tier']

    # Optional: refresh tier from DB (in case upgraded)
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT tier FROM users WHERE id = ?", (user_id,))
    db_tier = cursor.fetchone()
    if db_tier:
        tier = db_tier[0]
    conn.close()

    # Update sidebar (in case tier changed)
    st.sidebar.title(f"Hi, {username} ({tier})")

    st.header("Dashboard")

    # Example: Show popular stocks
    st.subheader("Live Market Snapshot")
    cols = st.columns(4)
    symbols = ['RELIANCE.NS', 'TCS.NS', 'EURUSD=X', 'USDINR=X']
    for i, sym in enumerate(symbols):
        with cols[i]:
            q = get_stock_quote(sym)
            if q:
                fmt = f"{q['current_price']:.4f}" if '=X' in sym else f"{q['current_price']:.2f}"
                delta = f"{q['change_percent']:.2f}%"
                st.metric(q['name'], fmt, delta)

    # Tier limits info
    from database import get_user_tier_limits
    limits = get_user_tier_limits(tier)
    st.info(f"**{tier} Plan**: Watchlist ≤ {limits['watchlist_limit']} | Portfolio ≤ {limits['portfolio_limit']} | Alerts ≤ {limits['alerts_limit']}")

    # Add more dashboard features here...
    st.write("More features coming soon!")
