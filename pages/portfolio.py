import streamlit as st
import sqlite3
from stock_data import get_stock_quote, POPULAR_ASSETS, search_stocks

def show():
    st.subheader("Portfolio")
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT subscription_plan FROM users WHERE user_id = ?", (st.session_state.user_id,))
    result = cursor.fetchone()
    plan = result[0] if result else "Free"
    
    if plan in ["Pro", "Premium"]:
        cursor.execute("SELECT stock_symbol, quantity, purchase_price FROM portfolio WHERE user_id = ?", 
                      (st.session_state.user_id,))
        holdings = cursor.fetchall()
        if holdings:
            for symbol, qty, price in holdings:
                st.write(f"{symbol}: {qty} shares @ ${price:.2f}")
        else:
            st.info("No holdings in portfolio.")
        # Add stock purchase (no wallet, just add to portfolio)
        symbol = st.selectbox("Select Stock", list(POPULAR_ASSETS.keys()))
        quantity = st.number_input("Quantity", min_value=1, value=1)
        if st.button("Add to Portfolio"):
            quote = get_stock_quote(symbol)
            if quote:
                cursor.execute(
                    "INSERT INTO portfolio (user_id, stock_symbol, quantity, purchase_price) VALUES (?, ?, ?, ?)",
                    (st.session_state.user_id, symbol, quantity, quote['current_price'])
                )
                conn.commit()
                st.success("Added to portfolio.")
    else:
        st.error("Upgrade to Pro or Premium to manage portfolio.")
    conn.close()