# pages/dashboard.py
import streamlit as st
from stock_data import get_stock_quote, POPULAR_ASSETS, get_market_indices, create_price_chart, search_stocks
from datetime import datetime, timedelta
import sqlite3

def init_predictions_db():
    try:
        conn = sqlite3.connect('stock_tracker.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
            symbol TEXT,
            prediction_date TEXT,
            predicted_direction TEXT, -- 'up' or 'down'
            actual_direction TEXT, -- 'up' or 'down' after verification
            PRIMARY KEY (symbol, prediction_date)
        )''')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error initializing predictions table: {str(e)}")
    finally:
        conn.close()

def store_prediction(symbol, predicted_direction):
    try:
        conn = sqlite3.connect('stock_tracker.db', timeout=10)
        cursor = conn.cursor()
        prediction_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT OR REPLACE INTO predictions (symbol, prediction_date, predicted_direction) VALUES (?, ?, ?)",
                       (symbol, prediction_date, predicted_direction))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error storing prediction: {str(e)}")
    finally:
        conn.close()

def verify_prediction(symbol, prediction_date, predicted_direction):
    quote = get_stock_quote(symbol)
    if quote and 'change_percent' in quote:
        actual_change = quote['change_percent']
        actual_direction = 'up' if actual_change > 0 else 'down'
        try:
            conn = sqlite3.connect('stock_tracker.db', timeout=10)
            cursor = conn.cursor()
            cursor.execute("UPDATE predictions SET actual_direction = ? WHERE symbol = ? AND prediction_date = ?",
                           (actual_direction, symbol, prediction_date))
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error verifying prediction: {str(e)}")
        finally:
            conn.close()
        return actual_direction == predicted_direction
    return None

def calculate_accuracy():
    try:
        conn = sqlite3.connect('stock_tracker.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT predicted_direction, actual_direction FROM predictions WHERE actual_direction IS NOT NULL")
        predictions = cursor.fetchall()
        conn.close()
        if not predictions or len(predictions) == 0:
            return 0.0
        correct = sum(1 for pred, actual in predictions if pred == actual)
        return (correct / len(predictions)) * 100
    except sqlite3.Error as e:
        st.error(f"Error calculating accuracy: {str(e)}")
        return 0.0

def show_news(symbol):
    # Placeholder news based on web searches (as of Sep 27, 2025, 07:02 PM EAT)
    news = {
        "RELIANCE.NS": [
            "Reliance Industries reports strong Q2 2025 earnings, up 15% (Yahoo Finance, Sep 25, 2025).",
            "Analysts predict Reliance stock to hit 1,700 INR due to energy sector growth (Reuters, Sep 26, 2025)."
        ],
        "TCS.NS": [
            "TCS announces new AI contracts, boosting stock outlook (CNBC, Sep 24, 2025).",
            "TCS stock up 10% YTD, analysts remain bullish (Economic Times, Sep 27, 2025)."
        ],
        "EURUSD=X": [
            "EUR/USD weakens as ECB hints at rate cuts (FXStreet, Sep 26, 2025).",
            "Forex analysts predict bearish trend for EUR/USD to 1.16 (Investing.com, Sep 25, 2025)."
        ],
        "USDINR=X": [
            "USD/INR rises due to RBI policy shifts (Business Standard, Sep 26, 2025).",
            "Analysts forecast USD/INR to reach 98 by year-end (Bloomberg, Sep 27, 2025)."
        ]
    }
    st.subheader(f"Recent News for {symbol}")
    for item in news.get(symbol, ["No recent news available."]):
        st.write(f"- {item}")

def show_prediction(symbol):
    # Placeholder predictions based on web trends (as of Sep 27, 2025)
    predictions = {
        "RELIANCE.NS": "Up (target 1,700 INR, +20% projected, based on Q2 earnings)",
        "TCS.NS": "Up (target 3,700 INR, +10% projected, based on AI contracts)",
        "EURUSD=X": "Down (forecast to 1.16 by Oct 2025, bearish ECB outlook)",
        "USDINR=X": "Up (forecast to 98 by Dec 2025, RBI policy impact)"
    }
    direction = 'up' if 'up' in predictions[symbol].lower() else 'down'
    store_prediction(symbol, direction)
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    is_correct = verify_prediction(symbol, past_date, direction)
    accuracy = calculate_accuracy()
    st.subheader(f"Prediction for {symbol}")
    st.write(f"Direction: {predictions[symbol]}")
    if is_correct is not None:
        st.write(f"Prediction for {past_date} was {'correct' if is_correct else 'incorrect'}.")
    st.write(f"Overall Prediction Accuracy: {accuracy:.2f}%")

def show():
    st.subheader("Market Dashboard")
    
    # Initialize predictions database
    with st.spinner("Initializing database..."):
        init_predictions_db()
    
    # Check subscription plan and role
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT subscription_plan, role FROM users WHERE user_id = ?", (st.session_state.user_id,))
    result = cursor.fetchone()
    plan, role = result if result else ("Free", "user")
    conn.close()
    
    # Display market indices with error handling
    indices = get_market_indices()
    st.subheader("Market Indices")
    if isinstance(indices, list):
        for index in indices:
            if isinstance(index, dict) and all(key in index for key in ['name', 'value', 'change']):
                st.write(f"{index['name']}: {index['value']:.2f} ({index['change']:+.2f}%)")
            else:
                st.write(f"Invalid index data: {index}")
    else:
        st.write("Error: Market indices data is not in the expected format.")

    # Stock/Forex search
    search_term = st.text_input("Search Stocks or Forex")
    if search_term:
        results = search_stocks(search_term)
        st.subheader("Search Results")
        for result in results:
            st.write(f"{result['symbol']}: {result['name']}")
    
    # Popular assets
    st.markdown("### Popular Assets")
    cols = st.columns(4)
    symbols = list(POPULAR_ASSETS.keys())
    for i, sym in enumerate(symbols):
        with cols[i % 4]:
            quote = get_stock_quote(sym)
            if quote and 'current_price' in quote and 'change_percent' in quote:
                value_format = f"{quote['current_price']:.4f}" if '=X' in sym else f"{quote['current_price']:.2f}"
                delta = f"{quote['change_percent']:.2f}%"
                st.metric(quote['name'], value_format, delta)
    
    # Price chart for selected asset (available to admin or Pro/Premium)
    selected_symbol = st.selectbox("Select Asset for Chart", symbols)
    if role == "admin" or plan in ["Pro", "Premium"]:
        with st.spinner(f"Loading chart for {selected_symbol}..."):
            chart_data = create_price_chart(selected_symbol, "1y")
            if chart_data:
                st.plotly_chart(chart_data, use_container_width=True)
            else:
                st.error(f"Failed to load chart for {selected_symbol}")
    else:
        st.info("Upgrade to Pro or Premium to view price charts, or log in as admin.")

    # News section
    show_news(selected_symbol)
    
    # Prediction section
    show_prediction(selected_symbol)
