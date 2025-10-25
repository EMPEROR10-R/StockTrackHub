import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
import streamlit as st

def validate_phone_number(phone_number):
    """Validate Kenyan phone number format"""
    # Remove any spaces or special characters
    phone = phone_number.replace(" ", "").replace("-", "").replace("+", "")
    
    # Check if it's a valid Kenyan number
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif not phone.startswith("254"):
        return False, "Phone number must be a valid Kenyan number (254XXXXXXXXX)"
    
    if len(phone) != 12:
        return False, "Phone number must be 12 digits (254XXXXXXXXX)"
    
    if not phone.isdigit():
        return False, "Phone number must contain only digits"
    
    return True, phone

def generate_reference_id():
    """Generate a unique reference ID for transactions"""
    return f"STH{int(datetime.now().timestamp())}{secrets.randbelow(9999):04d}"

def format_currency(amount, currency="USD"):
    """Format currency with appropriate symbol"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "KSh":
        return f"KSh {amount:,.0f}"
    else:
        return f"{amount:,.2f} {currency}"

def calculate_portfolio_metrics(portfolio_data):
    """Calculate portfolio performance metrics"""
    if not portfolio_data:
        return {
            'total_value': 0,
            'total_investment': 0,
            'total_pnl': 0,
            'total_pnl_percent': 0,
            'best_performer': None,
            'worst_performer': None
        }
    
    total_value = sum(item['current_value_inr'] for item in portfolio_data)
    total_investment = sum(item['investment'] for item in portfolio_data)
    total_pnl = total_value - total_investment
    total_pnl_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0
    
    # Find best and worst performers
    best_performer = max(portfolio_data, key=lambda x: x['pnl_percent'])
    worst_performer = min(portfolio_data, key=lambda x: x['pnl_percent'])
    
    return {
        'total_value': total_value,
        'total_investment': total_investment,
        'total_pnl': total_pnl,
        'total_pnl_percent': total_pnl_percent,
        'best_performer': best_performer,
        'worst_performer': worst_performer
    }

def log_user_activity(user_id, activity_type, details=None):
    """Log user activity for analytics"""
    conn = sqlite3.connect('stock_tracker.db')
    cursor = conn.cursor()
    
    # Create activity log table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute(
        "INSERT INTO activity_log (user_id, activity_type, details) VALUES (?, ?, ?)",
        (user_id, activity_type, details)
    )
    
    conn.commit()
    conn.close()

def get_exchange_rate():
    """Get current USD to KSh exchange rate (simplified)"""
    # In a real application, this would fetch from a currency API
    # For now, return a fixed rate
    return 130.0

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    
    # Basic HTML escape
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    
    return text

def check_rate_limit(user_id, action, limit=5, window_minutes=60):
    """Simple rate limiting check"""
    conn = sqlite3.connect('stock_tracker.db')
    cursor = conn.cursor()
    
    # Create rate limit table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Check recent attempts
    cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
    cursor.execute(
        """SELECT COUNT(*) FROM rate_limits 
           WHERE user_id = ? AND action = ? AND timestamp > ?""",
        (user_id, action, cutoff_time)
    )
    
    recent_attempts = cursor.fetchone()[0]
    
    if recent_attempts >= limit:
        conn.close()
        return False, f"Rate limit exceeded. Try again in {window_minutes} minutes."
    
    # Log this attempt
    cursor.execute(
        "INSERT INTO rate_limits (user_id, action) VALUES (?, ?)",
        (user_id, action)
    )
    
    conn.commit()
    conn.close()
    
    return True, "OK"

def cleanup_old_data():
    """Cleanup old data to maintain database performance"""
    conn = sqlite3.connect('stock_tracker.db')
    cursor = conn.cursor()
    
    # Clean old activity logs (keep last 90 days)
    cursor.execute(
        "DELETE FROM activity_log WHERE timestamp < datetime('now', '-90 days')"
    )
    
    # Clean old rate limit entries (keep last 24 hours)
    cursor.execute(
        "DELETE FROM rate_limits WHERE timestamp < datetime('now', '-1 days')"
    )
    
    conn.commit()
    conn.close()

def send_notification(user_id, title, message, notification_type="info"):
    """Store in-app notification"""
    conn = sqlite3.connect('stock_tracker.db')
    cursor = conn.cursor()
    
    # Create notifications table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    cursor.execute(
        """INSERT INTO notifications (user_id, title, message, notification_type) 
           VALUES (?, ?, ?, ?)""",
        (user_id, title, message, notification_type)
    )
    
    conn.commit()
    conn.close()

def get_user_notifications(user_id, limit=10):
    """Get user notifications"""
    conn = sqlite3.connect('stock_tracker.db')
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT title, message, notification_type, is_read, created_at 
           FROM notifications 
           WHERE user_id = ? 
           ORDER BY created_at DESC 
           LIMIT ?""",
        (user_id, limit)
    )
    
    notifications = cursor.fetchall()
    conn.close()
    
    return notifications

def hash_api_key(api_key):
    """Hash API key for secure storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_market_status():
    """Get market status (open/closed)"""
    now = datetime.now()
    
    # NSE trading hours: 9:00 AM to 3:30 PM IST, Monday to Friday
    # This is a simplified check
    if now.weekday() >= 5:  # Weekend
        return {"status": "closed", "reason": "Weekend"}
    
    hour = now.hour
    if hour < 9 or hour >= 15:
        return {"status": "closed", "reason": "Outside trading hours"}
    
    return {"status": "open", "next_open": None}

def create_backup():
    """Create database backup"""
    import shutil
    backup_filename = f"stock_tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2('stock_tracker.db', backup_filename)
    return backup_filename
