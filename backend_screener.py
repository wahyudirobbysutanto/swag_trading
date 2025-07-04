
import yfinance as yf
import pandas as pd
import numpy as np
import pyodbc

from dotenv import load_dotenv
from db_connector import get_connection
from datetime import datetime
from scrap_idx import get_idx_tickers_from_excel

load_dotenv()


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


# Proses utama
def run_screener():
    tickers = get_idx_tickers_from_excel('data/Daftar Saham.xlsx')
    # tickers = tickers[:10]
    tickers = ['INDF.JK']

    conn = get_connection()
    cursor = conn.cursor()

    for ticker in tickers:
        df = yf.download(ticker, period='90d', interval='1d')  # jangan terlalu pendek
        if df.empty or len(df) < 30:
            continue

        df = calculate_indicators(df)
        
        # print(df)
        # exit()
        
        df = df.dropna()

        # print(df)
        # exit()

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        # print(latest)
        # print(prev)
        
        # status = is_swin  g_candidate(df).iloc[-1]
        status = is_swing_candidate(latest, prev)

        # print('--------------------')
        # print(ticker.replace(".JK", ""))
        # print(latest.name.date())
        # print(round(float(latest['Close'].iloc[0]), 2))
        # print(round(float(latest['EMA8'].iloc[0]), 2))
        # print(round(float(latest['EMA20'].iloc[0]), 2))
        # print(round(float(latest['EMA50'].iloc[0]), 2))
        # print(round(float(latest['EMA200'].iloc[0]), 2))
        # print(round(float(latest['RSI'].iloc[0]), 2))
        # print(int(latest['Volume'].iloc[0]))
        # print(int(latest['AvgVolume10'].iloc[0]))
        # print(status)
        # print('--------------------')

        # exit()

        # Simpan ke archive
        cursor.execute("""
            INSERT INTO SwingScreeningArchive (
                ticker, tanggal, harga, ema8, ema20, ema50, ema200,
                rsi, volume, avg_volume, status_rekomendasi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker.replace(".JK", ""),
            latest.name.date(),
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

        # Simpan ke tabel utama (update or insert)
        cursor.execute("""
            MERGE SwingScreeningResults AS target
            USING (SELECT ? AS ticker) AS source
            ON target.ticker = source.ticker
            WHEN MATCHED THEN
                UPDATE SET
                    tanggal = ?, harga = ?, ema8 = ?, ema20 = ?, ema50 = ?, ema200 = ?,
                    rsi = ?, volume = ?, avg_volume = ?, status_rekomendasi = ?
            WHEN NOT MATCHED THEN
                INSERT (ticker, tanggal, harga, ema8, ema20, ema50, ema200,
                        rsi, volume, avg_volume, status_rekomendasi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            ticker.replace(".JK", ""),
            latest.name.date(),
            round(float(latest['Close']), 2),
            round(float(latest['EMA8']), 2),
            round(float(latest['EMA20']), 2),
            round(float(latest['EMA50']), 2),
            round(float(latest['EMA200']), 2),
            round(float(latest['RSI']), 2),
            int(latest['Volume']),
            int(latest['AvgVolume10']),
            status,
            ticker.replace(".JK", ""),
            latest.name.date(),
            round(float(latest['Close']), 2),
            round(float(latest['EMA8']), 2),
            round(float(latest['EMA20']), 2),
            round(float(latest['EMA50']), 2),
            round(float(latest['EMA200']), 2),
            round(float(latest['RSI']), 2),
            int(latest['Volume']),
            int(latest['AvgVolume10']),
            status
        ))


        conn.commit()

    cursor.close()
    conn.close()
    print("Screening selesai.")

if __name__ == "__main__":
    run_screener()
