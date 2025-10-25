# Stock Tracker Hub

## Overview

Stock Tracker Hub is a comprehensive stock market tracking platform built with Streamlit that focuses on NSE (National Stock Exchange) stocks with integrated M-Pesa payment functionality. The application provides real-time stock tracking, portfolio management, and a tiered membership system with varying feature access levels. Users can track their favorite stocks, manage virtual portfolios, and conduct financial transactions through M-Pesa integration, all within a user-friendly web interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based single-page application with multi-page navigation
- **UI Structure**: Page-based architecture with separate modules for dashboard, portfolio, wallet, and admin functionality
- **State Management**: Streamlit session state for user authentication and session persistence
- **Data Visualization**: Plotly integration for interactive charts and financial data visualization

### Backend Architecture
- **Application Framework**: Python-based backend using Streamlit as the web framework
- **Database Layer**: SQLite database with direct SQL queries for data persistence
- **Authentication System**: Custom authentication module with bcrypt password hashing
- **API Integration**: Yahoo Finance (yfinance) for real-time stock data and NSE tools for Indian market data

### Data Storage Solutions
- **Primary Database**: SQLite with the following core tables:
  - `users`: User accounts, tiers, and wallet balances
  - `transactions`: Financial transaction records
  - `watchlists`: User stock tracking preferences
  - `portfolio`: User stock holdings and investments
- **Caching Strategy**: Streamlit's built-in caching (@st.cache_data) for stock data with 60-second TTL
- **File Storage**: Local file system for database storage

### Authentication and Authorization
- **Password Security**: bcrypt hashing for secure password storage
- **Session Management**: Streamlit session state for maintaining user login status
- **User Roles**: Two-tier system with regular users and admin privileges
- **Input Validation**: Custom validation for email, username, and phone number formats

### External Dependencies

- **Stock Data Provider**: Yahoo Finance API via yfinance library for real-time NSE stock prices and historical data
- **Payment Gateway**: M-Pesa Daraja API integration for Kenyan mobile money transactions
- **Market Data**: NSE tools for additional Indian stock market functionality
- **Visualization**: Plotly for interactive financial charts and data visualization
- **Security**: bcrypt for password hashing and requests library for external API calls

The system supports a freemium model with three tiers (Free, Silver, Gold) where higher tiers unlock additional features like portfolio management and advanced stock tracking capabilities.