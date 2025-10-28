import sqlite3
import os

def init_database():
    """Initialize the SQLite database with required tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'stock_tracker.db')
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    
    # Check if users table exists and has 'id' column; drop if corrupted
    try:
        cursor.execute("SELECT 1 FROM users LIMIT 1")
        # Table exists; check columns
        columns = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
        if 'id' not in columns:
            cursor.execute("DROP TABLE users")
            print("Dropped corrupted users table.")
    except sqlite3.OperationalError:
        # Table doesn't exist; that's fine, we'll create it
        pass
    
    # === CREATE ALL TABLES ===
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            tier TEXT DEFAULT 'Free',
            balance_usd REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            amount_ksh REAL,
            mpesa_receipt TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_symbol TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, stock_symbol)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_symbol TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            threshold_price REAL NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # === NOW CREATE ADMIN USER (after tables exist) ===
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", ('adminyoo', 'kingmumo15@gmail.com'))
    if not cursor.fetchone():
        from auth import hash_password
        admin_hash = hash_password('adminyoopassword')
        cursor.execute(
            "INSERT INTO users (email, password_hash, username, tier, balance_usd) VALUES (?, ?, ?, ?, ?)",
            ('kingmumo15@gmail.com', admin_hash, 'adminyoo', 'Diamond', 10000.0)
        )

    conn.commit()
    conn.close()

def get_user_tier_limits(tier):
    """Get tier-specific limits and features"""
    tier_config = {
        'Free': {
            'watchlist_limit': 5,
            'portfolio_limit': 0,
            'alerts_limit': 0,
            'real_time_data': False,
            'price': 0
        },
        'Silver': {
            'watchlist_limit': 20,
            'portfolio_limit': 10,
            'alerts_limit': 5,
            'real_time_data': True,
            'price': 10  # USD
        },
        'Gold': {
            'watchlist_limit': 50,
            'portfolio_limit': 25,
            'alerts_limit': 15,
            'real_time_data': True,
            'price': 25  # USD
        },
        'Diamond': {
            'watchlist_limit': 100,
            'portfolio_limit': 50,
            'alerts_limit': 30,
            'real_time_data': True,
            'price': 50  # USD
        }
    }
    return tier_config.get(tier, tier_config['Free'])
