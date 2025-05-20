import yfinance as yf

ticker = yf.Ticker("AAPL")
df = ticker.history(period="1y", interval="1d")
print(df.head()) 