import yfinance as yf
import pandas as pd

ticker = "BBCA.JK"
data = yf.download(ticker, start="2023-01-01", end="2025-07-03")
print(data)
