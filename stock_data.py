# C:\Users\J\Downloads\StockTrackHub\stock_data.py
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import streamlit as st

# Note: nsetools is included but not used in this version; consider removing if unnecessary
# from nsetools import Nse  # Uncomment and initialize if needed
# nse = Nse()  # Uncomment if using NSE data

# Popular assets including NSE stocks and forex pairs (Yahoo Finance symbols)
POPULAR_ASSETS = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'INFY.NS': 'Infosys',
    'HDFC.NS': 'HDFC Ltd',
    'ICICIBANK.NS': 'ICICI Bank',
    'HDFCBANK.NS': 'HDFC Bank',
    'SBIN.NS': 'State Bank of India',
    'BHARTIARTL.NS': 'Bharti Airtel',
    'ITC.NS': 'ITC Ltd',
    'KOTAKBANK.NS': 'Kotak Mahindra Bank',
    'LT.NS': 'Larsen & Toubro',
    'AXISBANK.NS': 'Axis Bank',
    'MARUTI.NS': 'Maruti Suzuki',
    'SUNPHARMA.NS': 'Sun Pharmaceutical',
    'TITAN.NS': 'Titan Company',
    'WIPRO.NS': 'Wipro',
    'NESTLEIND.NS': 'Nestle India',
    'HCLTECH.NS': 'HCL Technologies',
    'BAJFINANCE.NS': 'Bajaj Finance',
    'ULTRACEMCO.NS': 'UltraTech Cement',
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'USDINR=X': 'USD/INR'
}

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_stock_quote(symbol):
    """Get current stock quote using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[-1]
            high_price = hist['High'].iloc[-1]
            low_price = hist['Low'].iloc[-1]
            volume = hist['Volume'].iloc[-1]
            
            change = current_price - open_price
            change_percent = (change / open_price) * 100 if open_price > 0 else 0
            
            return {
                'symbol': symbol,
                'name': POPULAR_ASSETS.get(symbol, symbol.replace('.NS', '').replace('=X', '')),
                'current_price': float(current_price),
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'volume': int(volume),
                'change': float(change),
                'change_percent': float(change_percent),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_historical_data(symbol, period="1y"):
    """Get historical stock data"""
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            return None
            
        return hist.reset_index()
    except Exception as e:
        st.error(f"Error fetching historical data for {symbol}: {str(e)}")
        return None

def create_price_chart(symbol, period="1y"):
    """Create interactive price chart using Plotly"""
    hist_data = get_historical_data(symbol, period)
    
    if hist_data is None:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=hist_data['Date'],
        open=hist_data['Open'],
        high=hist_data['High'],
        low=hist_data['Low'],
        close=hist_data['Close'],
        name=symbol
    ))
    
    fig.update_layout(
        title=f"{POPULAR_ASSETS.get(symbol, symbol)} - Price Chart",
        yaxis_title="Price (₹)",
        xaxis_title="Date",
        template="plotly_dark",
        height=500
    )
    
    return fig

def create_volume_chart(symbol, period="1y"):
    """Create volume chart"""
    hist_data = get_historical_data(symbol, period)
    
    if hist_data is None:
        return None
    
    fig = px.bar(
        hist_data,
        x='Date',
        y='Volume',
        title=f"{POPULAR_ASSETS.get(symbol, symbol)} - Trading Volume",
        template="plotly_dark",
        height=300
    )
    
    return fig

def get_market_indices():
    """Get major market indices as a list of dictionaries"""
    indices = {
        '^NSEI': 'NIFTY 50',
        '^NSEBANK': 'NIFTY Bank',
        '^NSEIT': 'NIFTY IT'
    }
    
    index_data = []
    
    for symbol, name in indices.items():
        try:
            index = yf.Ticker(symbol)
            hist = index.history(period="1d")
            
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                change = current - open_price
                change_percent = (change / open_price) * 100 if open_price > 0 else 0
                
                index_data.append({
                    'name': name,
                    'value': float(current),
                    'change': float(change),
                    'change_percent': float(change_percent)
                })
        except Exception as e:
            st.error(f"Error fetching index data for {name}: {str(e)}")
    
    return index_data

def search_stocks(query):
    """Search for stocks by name or symbol"""
    query = query.upper()
    results = []
    
    for symbol, name in POPULAR_ASSETS.items():
        if query in symbol.upper() or query in name.upper():
            results.append({'symbol': symbol, 'name': name})
    
    return results[:10]  # Return top 10 results

def convert_inr_to_usd(inr_amount, exchange_rate=83.0):
    """Convert INR to USD (approximate rate)"""
    return inr_amount / exchange_rate

def convert_usd_to_inr(usd_amount, exchange_rate=83.0):
    """Convert USD to INR (approximate rate)"""
    return usd_amount * exchange_rate
