import os
from dotenv import load_dotenv
load_dotenv()
import bcrypt
import sqlite3
import re

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def register_user(email, username, password):
    """Register a new user"""
    if not validate_email(email):
        return False, "Invalid email format"
    
    if not validate_username(username):
        return False, "Username must be 3-20 characters, letters, numbers, and underscores only"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
        if cursor.fetchone():
            conn.close()
            return False, "Email or username already exists"
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (email, password_hash, username) VALUES (?, ?, ?)",
            (email, password_hash, username)
        )
        
        conn.commit()
        conn.close()
        return True, "Registration successful"
        
    except sqlite3.Error as e:
        conn.close()
        return False, f"Database error: {str(e)}"

def authenticate_user(username, password):
    """Return the full user row (id, email, password_hash, username, tier, balance_usd) or None"""
    conn = sqlite3.connect('stock_tracker.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash, username, tier, balance_usd FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and verify_password(password, user[2]):   # password_hash is column 2
        return user
    return None
