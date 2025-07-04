import yfinance as yf
import pandas as pd
import numpy as np
import pyodbc

from dotenv import load_dotenv
from db_connector import get_connection
from scrap_idx import get_idx_tickers_from_excel

load_dotenv()

# ================================
# INDICATOR CALCULATION
# ================================

# Hitung indikator teknikal
def calculate_indicators(df):
    df['EMA8'] = df['Close'].ewm(span=8, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['RSI'] = compute_rsi(df['Close'], 14)
    df['AvgVolume10'] = df['Volume'].rolling(window=10).mean()
    return df


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def is_swing_candidate(latest, prev):
    close = latest['Close'].iloc[0]
    ema8 = latest['EMA8'].iloc[0]
    ema20 = latest['EMA20'].iloc[0]
    ema50 = latest['EMA50'].iloc[0]
    ema200 = latest['EMA200'].iloc[0]
    rsi = round(latest['RSI'].iloc[0], 2)
    volume = latest['Volume'].iloc[0]
    avg_vol = latest['AvgVolume10'].iloc[0]


    ema8_prev = prev['EMA8'].iloc[0]
    ema20_prev = prev['EMA20'].iloc[0]


    cross_today = ema8 > ema20
    cross_yesterday = ema8_prev < ema20_prev
    momentum = ema8_prev > ema20_prev

    volume_ok = volume > (0.8 * avg_vol)

    # MODE AGRESIF
    if (
        close > ema50 and
        (cross_today and (cross_yesterday or momentum)) and
        rsi >= 70 and
        volume > avg_vol
    ):
        return 'yes-agresif'

    # MODE NORMAL
    if (
        close > ema50 and
        (cross_today and (cross_yesterday or momentum)) and
        50 < rsi < 70 and
        volume_ok
    ):
        return 'yes'

    return 'no'





# ================================
# MAIN PROCESS
# ================================

def run_historical_screening(days=60):
    tickers = get_idx_tickers_from_excel('data/Daftar Saham.xlsx')
    conn = get_connection()
    cursor = conn.cursor()

    today = pd.Timestamp.now().normalize()



    for ticker in tickers:
        print(f"🔍 Processing {ticker}...")
        df = yf.download(ticker, period=f"{days + 90}d", interval="1d")  # include buffer
        if df.empty or len(df) < days:
            print(f"⛔ Not enough data for {ticker}")
            continue

        df = calculate_indicators(df)
        df = df.dropna()
        
        
        for i in range(1, len(df)):
            latest = df.iloc[i]
            prev = df.iloc[i - 1]

            tanggal = tanggal = df.index[i].date()

            if df.index[i] >= today:
                continue

            status = is_swing_candidate(latest, prev)
            
            try:
                cursor.execute("""
                    INSERT INTO SwingScreeningArchive (
                        ticker, tanggal, harga, ema8, ema20, ema50, ema200,
                        rsi, volume, avg_volume, status_rekomendasi
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker.replace(".JK", ""),
                    tanggal,
                    round(float(latest['Close'].iloc[0]), 2),
                    round(float(latest['EMA8'].iloc[0]), 2),
                    round(float(latest['EMA20'].iloc[0]), 2),
                    round(float(latest['EMA50'].iloc[0]), 2),
                    round(float(latest['EMA200'].iloc[0]), 2),
                    round(float(latest['RSI'].iloc[0]), 2),
                    int(latest['Volume'].iloc[0]),
                    int(latest['AvgVolume10'].iloc[0]),
                    status
                ))
            except Exception as e:
                print(f"⚠ Error inserting {ticker} {tanggal}: {e}")

        conn.commit()

    cursor.close()
    conn.close()
    print("✅ Historical screening complete.")

if __name__ == "__main__":
    run_historical_screening(days=60)
