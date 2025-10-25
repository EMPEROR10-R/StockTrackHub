import streamlit as st
import sqlite3
from datetime import datetime, timedelta

def update_subscription(user_id, plan):
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    cursor.execute(
        "UPDATE users SET subscription_plan = ?, subscription_expiry = ? WHERE user_id = ?",
        (plan, expiry, user_id)
    )
    conn.commit()
    conn.close()

def show():
    if st.session_state.role != "admin":
        st.error("Access denied.")
        return
    
    st.subheader("Admin Panel")
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    
    # Display admin wallet balance
    cursor.execute("SELECT balance FROM wallet WHERE user_id = 1")
    result = cursor.fetchone()
    admin_balance = result[0] if result else 0.0
    st.write(f"Admin Wallet Balance: ${admin_balance:.2f}")
    
    # Display pending payment requests
    st.markdown("### Pending Payment Requests")
    cursor.execute(
        """
        SELECT pr.request_id, pr.user_id, u.username, pr.amount, pr.reference_number, pr.submission_time
        FROM payment_requests pr
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.status = 'Pending'
        """
    )
    requests = cursor.fetchall()
    
    if requests:
        for request in requests:
            request_id, user_id, username, amount, ref_number, submission_time = request
            with st.expander(f"Request ID: {request_id} - {username}"):
                st.write(f"User ID: {user_id}")
                st.write(f"Username: {username}")
                st.write(f"Amount: KES {amount:.2f}")
                st.write(f"Reference Number: {ref_number}")
                st.write(f"Submitted: {submission_time}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{request_id}"):
                        # Calculate 2% admin fee in USD (130 KES/USD)
                        admin_fee_kes = amount * 0.02
                        admin_fee_usd = admin_fee_kes / 130
                        
                        # Update admin wallet only
                        cursor.execute(
                            "INSERT OR REPLACE INTO wallet (user_id, balance) VALUES (1, COALESCE((SELECT balance FROM wallet WHERE user_id = 1) + ?, ?))",
                            (admin_fee_usd, admin_fee_usd)
                        )
                        # Update payment request status
                        cursor.execute(
                            "UPDATE payment_requests SET status = 'Approved' WHERE request_id = ?",
                            (request_id,)
                        )
                        # Update subscription plan
                        plan = "Pro" if amount == 1000 else "Premium" if amount == 2500 else "Free"
                        update_subscription(user_id, plan)
                        conn.commit()
                        st.success(f"Payment approved for {username}. Plan updated to {plan}.")
                with col2:
                    if st.button("Reject", key=f"reject_{request_id}"):
                        cursor.execute(
                            "UPDATE payment_requests SET status = 'Rejected' WHERE request_id = ?",
                            (request_id,)
                        )
                        conn.commit()
                        st.error(f"Payment rejected for {username}.")
    else:
        st.info("No pending payment requests.")
    
    conn.close()