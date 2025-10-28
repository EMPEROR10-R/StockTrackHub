# C:\Users\J\Downloads\StockTrackHub\app.py
import streamlit as st
import os

from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timedelta
from stock_data import get_stock_quote, POPULAR_ASSETS  # Added missing import
import pages.dashboard as dashboard  # Added import for dashboard
import pages.portfolio as portfolio  # Added import for portfolio
import pages.ai_assistant as ai_assistant  # Added import for ai_assistant
import pages.admin as admin  # Added import for admin

load_dotenv()

def authenticate(username, password):
    """Authenticate user and return (user_id, role, subscription_plan) or None."""
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role, subscription_plan FROM users WHERE username = ? AND password = ?", 
                   (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def logout():
    """Clear session state for logout."""
    st.session_state.clear()

def init_db():
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    print("Initializing database...")  # Debug print
    # Drop existing tables to avoid schema mismatches
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS portfolio")
    cursor.execute("DROP TABLE IF EXISTS wallet")
    cursor.execute("DROP TABLE IF EXISTS payment_requests")
    cursor.execute("DROP TABLE IF EXISTS predictions")  # Ensure predictions table is dropped
    
    # Create tables with the correct schema
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        subscription_plan TEXT DEFAULT 'Free',
        subscription_expiry TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS portfolio (
        user_id INTEGER,
        stock_symbol TEXT,
        quantity INTEGER,
        purchase_price REAL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS wallet (
        user_id INTEGER PRIMARY KEY,
        balance REAL DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        reference_number TEXT,
        status TEXT DEFAULT 'Pending',
        submission_time TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
        symbol TEXT,
        prediction_date TEXT,
        predicted_direction TEXT,
        actual_direction TEXT,
        PRIMARY KEY (symbol, prediction_date)
    )''')
    # Insert new admin user with Premium subscription
    cursor.execute('''INSERT INTO users (user_id, username, password, role, subscription_plan) 
        VALUES (1, 'EMP-10', '10-EMP', 'admin', 'Premium')''')  # Set to Premium
    cursor.execute('''INSERT OR REPLACE INTO wallet (user_id, balance) 
        VALUES (1, 0.0)''')
    cursor.execute("DELETE FROM wallet WHERE user_id != 1")
    conn.commit()
    print("Database initialized.")  # Debug print
    conn.close()

def check_subscription_expiry():
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, subscription_plan, subscription_expiry FROM users WHERE user_id != 1")
    users = cursor.fetchall()
    current_date = datetime.now()
    for user_id, plan, expiry in users:
        if expiry and plan != "Free":
            try:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                if current_date > expiry_date:
                    cursor.execute(
                        "UPDATE users SET subscription_plan = 'Free', subscription_expiry = NULL WHERE user_id = ?",
                        (user_id,)
                    )
            except ValueError:
                cursor.execute(
                    "UPDATE users SET subscription_plan = 'Free', subscription_expiry = NULL WHERE user_id = ?",
                    (user_id,)
                )
    conn.commit()
    conn.close()

def show_landing_page():
    st.title("Stock Tracker Hub")
    # Temporarily disable image display
    # st.image("images/payment_image.jpg", caption="Make payments using Bank Account or Paybill")
    st.write("Make payments using Bank Account Paybill.")  # Updated placeholder text
    popular_symbols = ['RELIANCE.NS', 'TCS.NS', 'EURUSD=X', 'USDINR=X']
    cols = st.columns(len(popular_symbols))
    for i, sym in enumerate(popular_symbols):
        with cols[i]:
            quote = get_stock_quote(sym)
            if quote:
                value_format = f"{quote['current_price']:.4f}" if '=X' in sym else f"{quote['current_price']:.2f}"
                delta = f"{quote['change_percent']:.2f}%"
                st.metric(quote['name'], value_format, delta)
    if st.button("Log in"):
        st.session_state.show_login = True
    if st.button("Sign up"):
        st.session_state.show_signup = True

def show_login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate(username, password)
        if user:
            st.session_state.user_id, st.session_state.role, st.session_state.subscription_plan = user
            st.session_state.username = username
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def show_signup():
    st.title("Sign Up")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Sign Up"):
        conn = sqlite3.connect('stock_tracker.db', timeout=10)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
            conn.commit()
            st.success("Account created! Please log in.")
            st.session_state.show_login = True
            st.session_state.show_signup = False
        except sqlite3.IntegrityError:
            st.error("Username already exists.")
        finally:
            conn.close()

def show_subscription_page():
    st.subheader("Subscription Plans")
    plans = {
        "Free": {"price": 0, "duration": "N/A", "features": ["Basic Dashboard Access"]},
        "Pro": {"price": 1000, "duration": "30 days", "features": ["Advanced Analytics", "Portfolio Tracking"]},
        "Premium": {"price": 2500, "duration": "30 days", "features": ["All Pro Features", "AI Assistant Access"]}
    }
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT subscription_plan, subscription_expiry FROM users WHERE user_id = ?", 
                   (st.session_state.user_id,))
    result = cursor.fetchone()
    current_plan, expiry = result if result else ("Free", None)
    conn.close()
    st.write(f"Current Plan: {current_plan}")
    if expiry:
        st.write(f"Expires: {expiry}")
    for plan, details in plans.items():
        with st.expander(f"{plan} Plan - KES {details['price']}"):
            for feature in details['features']:
                st.write(f"- {feature}")
            if plan != current_plan and st.button(f"Select {plan} Plan"):
                st.session_state.selected_plan = plan
                st.session_state.plan_price = details['price']
                st.session_state.show_payment = True

def show_payment_page():
    st.subheader("Make Payment")
    st.write("Please send payment to the following details:")
    st.write(f"**Bank Account Number**: 0650181285746")
    st.write(f"**Paybill Number**: 247247")
    st.write("After making the payment, click below to confirm and submit your transaction reference number.")
    if st.button("Confirm Payment"):
        st.session_state.show_reference_form = True

def show_reference_form():
    st.subheader("Submit Transaction Reference")
    reference_number = st.text_input("Enter Transaction Reference Number")
    amount = st.session_state.plan_price
    if st.button("Submit Reference"):
        if reference_number:
            conn = sqlite3.connect('stock_tracker.db', timeout=10)
            cursor = conn.cursor()
            submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT INTO payment_requests (user_id, amount, reference_number, status, submission_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (st.session_state.user_id, amount, reference_number, "Pending", submission_time)
            )
            conn.commit()
            conn.close()
            st.success("Reference submitted! Admin will verify within 24 hours.")
            st.session_state.show_reference_form = False
            st.session_state.show_payment = False
        else:
            st.error("Please enter a valid reference number.")

def show_main_app():
    check_subscription_expiry()
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    pages = ["Dashboard", "Portfolio", "Subscriptions", "AI Assistant"]
    if st.session_state.role == "admin":
        pages.append("Admin")
    page = st.sidebar.radio("Navigate", pages)
    if page == "Dashboard":
        dashboard.show()
    elif page == "Portfolio":
        portfolio.show()
    elif page == "Subscriptions":
        show_subscription_page()
        if st.session_state.get('show_payment', False):
            show_payment_page()
        if st.session_state.get('show_reference_form', False):
            show_reference_form()
    elif page == "AI Assistant":
        ai_assistant.show()
    elif page == "Admin":
        admin.show()

def main():
    init_db()
    st.set_page_config(page_title="Stock Tracker Hub", layout="wide")
    if 'user_id' not in st.session_state:
        if getattr(st.session_state, 'show_login', False):
            show_login()
        elif getattr(st.session_state, 'show_signup', False):
            show_signup()
        else:
            show_landing_page()
    else:
        show_main_app()
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()

if __name__ == "__main__":
    main()
