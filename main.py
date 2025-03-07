from fastapi import FastAPI, HTTPException, Query
import requests
import os
import uvicorn
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# تعیین مسیر دقیق فایل .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

# دریافت API key
API_KEY = os.getenv("TWELVEDATA_API_KEY")
if not API_KEY:
    # استفاده از مقدار پیش‌فرض اگر متغیر محیطی پیدا نشد
    API_KEY = "d363621cb93c4a6eaf755513f0d754e5"
    print("⚠️ Using default API key")

app = FastAPI(
    title="Twelve Data API",
    description="API for retrieving financial market data including stocks, forex, cryptocurrencies, and more",
    version="1.0.0"
)

BASE_URL = "https://api.twelvedata.com"

@app.get("/")
def home():
    return {"message": "✅ Twelve Data API is running!", "version": "1.0.0"}

# Helper function to send requests to Twelve Data
async def fetch_from_twelvedata(endpoint: str, params: Optional[Dict[str, Any]] = None):
    url = f"{BASE_URL}/{endpoint}"
    
    # Always include the API key in params
    if params is None:
        params = {}
    
    params["apikey"] = API_KEY
    
    print(f"🔍 Sending request to: {url}")
    print(f"🔍 With params: {params}")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print(f"❌ Bad Request: {response.text}")
            raise HTTPException(status_code=400, detail=f"❌ Bad Request: {response.text}")
        elif response.status_code == 401:
            print(f"❌ Unauthorized: {response.text}")
            raise HTTPException(status_code=401, detail="❌ Invalid API key or unauthorized access")
        elif response.status_code == 429:
            print(f"❌ Too Many Requests: {response.text}")
            raise HTTPException(status_code=429, detail="❌ Rate limit exceeded. Please try again later.")
        else:
            print(f"⚠ Unexpected Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"⚠ Unexpected Error: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"❌ Connection Error: {str(e)}")

# 1️⃣ Time Series Data
@app.get("/time_series")
async def get_time_series(
    symbol: str = Query(..., description="Symbol to get data for (e.g., AAPL, EUR/USD, BTC/USD)"),
    interval: str = Query("1day", description="Time interval (e.g., 1min, 5min, 15min, 30min, 1h, 1day, 1week, 1month)"),
    outputsize: int = Query(30, description="Number of data points to return (1-5000)"),
    start_date: Optional[str] = Query(None, description="Start date in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    end_date: Optional[str] = Query(None, description="End date in format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"),
    format: str = Query("JSON", description="Output format (JSON, CSV)"),
    timezone: Optional[str] = Query(None, description="Timezone for the returned data (e.g., America/New_York)")
):
    """
    Get time series data for a specific symbol
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "format": format
    }
    
    # Add optional parameters if provided
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if timezone:
        params["timezone"] = timezone
    
    return await fetch_from_twelvedata("time_series", params)

# 2️⃣ Real-time Price
@app.get("/price")
async def get_price(
    symbol: str = Query(..., description="Symbol to get data for (e.g., AAPL, EUR/USD, BTC/USD)"),
    exchange: Optional[str] = Query(None, description="Exchange name (e.g., NASDAQ, FOREX, BINANCE)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get real-time price for a specific symbol
    """
    params = {
        "symbol": symbol,
        "format": format
    }
    
    if exchange:
        params["exchange"] = exchange
    
    return await fetch_from_twelvedata("price", params)

# 3️⃣ Quote
@app.get("/quote")
async def get_quote(
    symbol: str = Query(..., description="Symbol to get data for (e.g., AAPL, EUR/USD, BTC/USD)"),
    interval: Optional[str] = Query(None, description="Time interval (e.g., 1min, 5min, 15min, 30min, 1h, 1day, 1week, 1month)"),
    exchange: Optional[str] = Query(None, description="Exchange name (e.g., NASDAQ, FOREX, BINANCE)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get quote data for a specific symbol
    """
    params = {
        "symbol": symbol,
        "format": format
    }
    
    if interval:
        params["interval"] = interval
    if exchange:
        params["exchange"] = exchange
    
    return await fetch_from_twelvedata("quote", params)

# 4️⃣ Symbol Search
@app.get("/symbol_search")
async def search_symbol(
    symbol: str = Query(..., description="Symbol or keyword to search for"),
    outputsize: int = Query(30, description="Number of results to return (1-120)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Search for symbols by name or ticker
    """
    params = {
        "symbol": symbol,
        "outputsize": outputsize,
        "format": format
    }
    
    return await fetch_from_twelvedata("symbol_search", params)

# 5️⃣ Exchanges
@app.get("/exchanges")
async def get_exchanges(
    type: Optional[str] = Query(None, description="Exchange type (e.g., stock, forex, crypto)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    List all available exchanges
    """
    params = {
        "format": format
    }
    
    if type:
        params["type"] = type
    
    return await fetch_from_twelvedata("exchanges", params)

# 6️⃣ Stocks List
@app.get("/stocks")
async def get_stocks(
    symbol: Optional[str] = Query(None, description="Filter by specific symbol"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    country: Optional[str] = Query(None, description="Filter by country"),
    type: Optional[str] = Query(None, description="Stock type (e.g., common, preferred, etf, etc.)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get list of stocks with optional filtering
    """
    params = {
        "format": format
    }
    
    if symbol:
        params["symbol"] = symbol
    if exchange:
        params["exchange"] = exchange
    if country:
        params["country"] = country
    if type:
        params["type"] = type
    
    return await fetch_from_twelvedata("stocks", params)

# 7️⃣ Forex Pairs
@app.get("/forex_pairs")
async def get_forex_pairs(
    symbol: Optional[str] = Query(None, description="Filter by specific symbol"),
    currency_base: Optional[str] = Query(None, description="Filter by base currency (e.g., USD, EUR)"),
    currency_quote: Optional[str] = Query(None, description="Filter by quote currency (e.g., USD, EUR)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get list of forex pairs with optional filtering
    """
    params = {
        "format": format
    }
    
    if symbol:
        params["symbol"] = symbol
    if currency_base:
        params["currency_base"] = currency_base
    if currency_quote:
        params["currency_quote"] = currency_quote
    
    return await fetch_from_twelvedata("forex_pairs", params)

# 8️⃣ Cryptocurrencies
@app.get("/cryptocurrencies")
async def get_cryptocurrencies(
    symbol: Optional[str] = Query(None, description="Filter by specific symbol"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    currency_base: Optional[str] = Query(None, description="Filter by base currency (e.g., BTC, ETH)"),
    currency_quote: Optional[str] = Query(None, description="Filter by quote currency (e.g., USD, EUR)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get list of cryptocurrencies with optional filtering
    """
    params = {
        "format": format
    }
    
    if symbol:
        params["symbol"] = symbol
    if exchange:
        params["exchange"] = exchange
    if currency_base:
        params["currency_base"] = currency_base
    if currency_quote:
        params["currency_quote"] = currency_quote
    
    return await fetch_from_twelvedata("cryptocurrencies", params)

# 9️⃣ ETFs
@app.get("/etf")
async def get_etfs(
    symbol: Optional[str] = Query(None, description="Filter by specific symbol"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    country: Optional[str] = Query(None, description="Filter by country"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get list of ETFs with optional filtering
    """
    params = {
        "format": format
    }
    
    if symbol:
        params["symbol"] = symbol
    if exchange:
        params["exchange"] = exchange
    if country:
        params["country"] = country
    
    return await fetch_from_twelvedata("etf", params)

# 🔟 Technical Indicators
@app.get("/indicators/{indicator}")
async def get_technical_indicator(
    indicator: str,
    symbol: str = Query(..., description="Symbol to get data for (e.g., AAPL, EUR/USD, BTC/USD)"),
    interval: str = Query("1day", description="Time interval (e.g., 1min, 5min, 15min, 30min, 1h, 1day, 1week, 1month)"),
    outputsize: int = Query(30, description="Number of data points to return (1-5000)"),
    time_period: int = Query(20, description="Time period for the indicator calculation"),
    series_type: str = Query("close", description="Series type to use (open, high, low, close)"),
    format: str = Query("JSON", description="Output format (JSON, CSV)")
):
    """
    Get technical indicator data for a specific symbol
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "time_period": time_period,
        "series_type": series_type,
        "format": format
    }
    
    return await fetch_from_twelvedata(f"technical_indicators/{indicator}", params)

# Run the server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8093))  # Using port 8093 as requested
    print(f"🚀 Starting Twelve Data API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
