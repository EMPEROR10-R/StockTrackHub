# --------------------------------------------------------------
# app.py  (REPLACE ENTIRE FILE WITH THIS)
# --------------------------------------------------------------
import streamlit as st
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
from stock_data import get_stock_quote, POPULAR_ASSETS
import pages.dashboard as dashboard
import pages.portfolio as portfolio
import pages.ai_assistant as ai_assistant
import pages.admin as admin
import requests
from auth import authenticate_user

load_dotenv()

# ------------------------------------------------------------------
# LOTTIE ANIMATION (man in suit)
# ------------------------------------------------------------------
LOTTIE_URL = "https://assets4.lottiefiles.com/packages/lf20_yf3k.json"

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ------------------------------------------------------------------
# DB INITIALISATION
# ------------------------------------------------------------------
def init_db():
    from database import init_database
    init_database()

# ------------------------------------------------------------------
# AUTH
# ------------------------------------------------------------------
def do_login(username: str, password: str):
    user = authenticate_user(username, password)
    if user:
        st.session_state.user = {
            "id": user[0],
            "email": user[1],
            "username": user[3],
            "tier": user[4],
            "balance_usd": user[5],
            "is_admin": user[3] == "adminyoo"
        }
        return True
    return False

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# ------------------------------------------------------------------
# PAGES
# ------------------------------------------------------------------
def landing_page():
    st.title("Stock Tracker Hub")
    st.write("Track NSE, NASDAQ, Forex & Crypto in real time.")
    cols = st.columns(4)
    for i, sym in enumerate(['RELIANCE.NS', 'TCS.NS', 'EURUSD=X', 'USDINR=X']):
        with cols[i]:
            q = get_stock_quote(sym)
            if q:
                fmt = f"{q['current_price']:.4f}" if '=X' in sym else f"{q['current_price']:.2f}"
                st.metric(q['name'], fmt, f"{q['change_percent']:.2f}%")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("**Log in**", use_container_width=True):
            st.session_state.page = "login"
    with col2:
        if st.button("**Sign up**", use_container_width=True):
            st.session_state.page = "signup"
    st.rerun()

def login_page():
    st.title("Log in")
    lottie_json = load_lottieurl(LOTTIE_URL)
    if lottie_json:
        st.lottie(lottie_json, height=200, key="login_lottie")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="e.g. adminyoo")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if do_login(username, password):
                st.success("Welcome!")
                st.session_state.page = "main"
                st.rerun()
            else:
                st.error("Invalid credentials")

    if st.button("Back to Home"):
        st.session_state.page = "landing"
        st.rerun()

def signup_page():
    from auth import register_user
    st.title("Create Account")
    with st.form("signup_form"):
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            ok, msg = register_user(email, username, password)
            if ok:
                st.success(msg)
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)

def main_app():
    st.sidebar.image("https://via.placeholder.com/150x50?text=Logo", use_container_width=True)
    st.sidebar.title(f"Hi, {st.session_state.user['username']} ({st.session_state.user['tier']})")

    nav_items = [
        ("app", "Home / Dashboard"),
        ("dashboard", "Dashboard"),
        ("portfolio", "Portfolio"),
        ("ai assistant", "AI Assistant"),
    ]
    if st.session_state.user["is_admin"]:
        nav_items.append(("admin", "Admin Panel"))

    choice = st.sidebar.radio("Navigate", [label for _, label in nav_items], key="nav")

    page_map = {
        "Home / Dashboard": dashboard.show,
        "Dashboard": dashboard.show,
        "Portfolio": portfolio.show,
        "AI Assistant": ai_assistant.show,
        "Admin Panel": admin.show,
    }
    page_map[choice]()

    if st.sidebar.button("Logout"):
        logout()
        st.session_state.page = "landing"
        st.rerun()

# ------------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------------
def router():
    if "page" not in st.session_state:
        st.session_state.page = "landing"

    if st.session_state.page == "landing":
        landing_page()
    elif st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    elif st.session_state.page == "main":
        main_app()

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    init_db()
    st.set_page_config(page_title="Stock Tracker Hub", layout="wide")
    router()

if __name__ == "__main__":
    main()
