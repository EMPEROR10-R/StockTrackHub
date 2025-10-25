# C:\Users\J\Downloads\StockTrackerHub\pages\ai_assistant.py
import streamlit as st
import sqlite3
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()

def show():
    st.subheader("AI Assistant (Premium Only)")
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT subscription_plan FROM users WHERE user_id = ?", (st.session_state.user_id,))
    result = cursor.fetchone()
    plan = result[0] if result else "Free"
    conn.close()

    if plan != "Premium":
        st.error("Upgrade to Premium to access the AI Assistant.")
        return

    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        st.error("Hugging Face API key not found. Please set HUGGINGFACE_API_KEY in .env.")
        return

    client = InferenceClient(api_key)
    prompt = st.text_input("Ask about stocks or forex (e.g., 'Analyze RELIANCE.NS'):")
    if prompt:
        try:
            response = client.text_generation(prompt, model="gpt2")  # Example model, adjust as needed
            st.write("AI Response:", response)
        except Exception as e:
            st.error(f"Error generating response: {e}")
