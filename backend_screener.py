
import yfinance as yf
import pandas as pd
import numpy as np
import pyodbc

from dotenv import load_dotenv
from db_connector import get_connection
from datetime import datetime
from scrap_idx import get_idx_tickers_from_excel
from ai_module import get_ai_recommendation

load_dotenv()


def is_valid_breakout(df):
    if len(df) < 12:
        return False

    # last_5_range = df['Close'].iloc[-6:-1].max() - df['Close'].iloc[-6:-1].min()
    last_5_closes = df['Close'].iloc[-6:-1]
    last_5_range = float(last_5_closes.max() - last_5_closes.min())

    today_close = float(df['Close'].iloc[-1])
    avg_volume = float(df['Volume'].iloc[-11:-1].mean())
    today_volume = float(df['Volume'].iloc[-1])

    breakout_range_ok = last_5_range < 0.03 * today_close
    volume_spike_ok = today_volume > 1.2 * avg_volume

    # print('--------------------')
    # print(breakout_range_ok)
    # print('--------------------')
    # print(volume_spike_ok)
    # print('--------------------')

    return breakout_range_ok and volume_spike_ok

def compute_rsi_tv_style(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rsi = pd.Series(index=series.index, dtype='float64')
    rs = 0

    for i in range(len(series)):
        if i < period:
            rsi.iloc[i] = np.nan
        elif i == period:
            gain_val = avg_gain.iloc[i].item()
            loss_val = avg_loss.iloc[i].item()
            rsi.iloc[i] = 100 - (100 / (1 + rs))
            prev_gain = gain_val
            prev_loss = loss_val
            if prev_loss == 0:
                rs = 0
            else:
                rs = prev_gain / prev_loss
            # rs = 0 if loss_val == 0 else gain_val / loss_val
            
        else:
            gain_i = gain.iloc[i].item()
            loss_i = loss.iloc[i].item()
            prev_gain = (prev_gain * (period - 1) + gain_i) / period
            prev_loss = (prev_loss * (period - 1) + loss_i) / period
            
            if prev_loss == 0:
                rs = 0
            else:
                rs = prev_gain / prev_loss
            # rs = 0 if prev_loss == 0 else prev_gain / prev_loss
            rsi.iloc[i] = 100 - (100 / (1 + rs))

    return rsi

def custom_ema(series, period):
    ema = series.copy()
    sma = series.rolling(window=period).mean()
    multiplier = 2 / (period + 1)

    for i in range(len(series)):
        if i < period:
            ema.iloc[i] = np.nan
        elif i == period:
            ema.iloc[i] = sma.iloc[i]
        else:
            ema.iloc[i] = (series.iloc[i] - ema.iloc[i-1]) * multiplier + ema.iloc[i-1]
    
    return ema

# Hitung indikator teknikal
def calculate_indicators(df):
    # df['EMA8'] = df['Close'].ewm(span=8, adjust=False).mean()
    # df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    # df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    # df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    # df['RSI'] = compute_rsi(df['Close'], 14)
    # df['AvgVolume10'] = df['Volume'].rolling(window=10).mean()

    df['EMA8'] = custom_ema(df['Close'], 8)
    df['EMA20'] = custom_ema(df['Close'], 20)
    df['EMA50'] = custom_ema(df['Close'], 50)
    df['EMA200'] = 0#custom_ema(df['Close'], 200)
    df['RSI'] = compute_rsi_tv_style(df['Close'], 14)
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
        volume > avg_vol and
        volume < 1000000
    ):
        return 'yes-volume-kurang'

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

    conn = get_connection()


    # tickers = get_idx_tickers_from_excel('data/Daftar Saham.xlsx')
    # # tickers = tickers[:10]
    # tickers = ['INDF.JK']
    df_active = pd.read_sql("SELECT ticker FROM ActiveVolumeStocks WHERE active = 1", conn)
    tickers = [f"{t}.JK" for t in df_active['ticker'].tolist()]
    # tickers = ['DIVA.JK']

    cursor = conn.cursor()

    for ticker in tickers:
        df = yf.download(ticker, period='250d', interval='1d')  # jangan terlalu pendek
        # df = yf.download(ticker, start="2022-01-01")
        if df.empty or len(df) < 30:
            continue

        df = calculate_indicators(df)
        
        # print('--------------------')
        # print(ticker.replace(".JK", ""))
        # print('--------------------')
        # print(df)
        # print('--------------------')


        # print(df)
        # exit()
        
        df = df.dropna()

        if df.empty or len(df) < 3:
            print("skip kosong")
        else:

            # print(df)
            # exit()

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            # print(latest)
            # print(prev)
            
            if not is_valid_breakout(df):
                print(f"{ticker}: breakout tidak valid")
                status = 'no'
            else:
                # status = is_swin  g_candidate(df).iloc[-1]
                status = is_swing_candidate(latest, prev)

            # print(df[['Close']].tail(5))
            # print(df.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']])

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

            recommendation = ''
            # if (status = 'yes'):
            #     recommendation = get_ai_recommendation(ticker.replace(".JK", ""), latest.name.date(), round(float(latest['Close'].iloc[0]), 2), round(float(latest['EMA8'].iloc[0]), 2), round(float(latest['EMA20'].iloc[0]), 2), round(float(latest['EMA50'].iloc[0]), 2), round(float(latest['EMA200'].iloc[0]), 2), round(float(latest['RSI'].iloc[0]), 2), int(latest['Volume'].iloc[0]), int(latest['AvgVolume10'].iloc[0]), status)
            
            # print(recommendation)
            # exit()

            
            # Simpan ke archive
            cursor.execute("""
                INSERT INTO SwingScreeningArchive (
                    ticker, tanggal, harga, ema8, ema20, ema50, ema200,
                    rsi, volume, avg_volume, status_rekomendasi, ai_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                status,
                recommendation
            ))

            # Simpan ke tabel utama (update or insert)
            # cursor.execute("""
            #     MERGE SwingScreeningResults AS target
            #     USING (SELECT ? AS ticker) AS source
            #     ON target.ticker = source.ticker
            #     WHEN MATCHED THEN
            #         UPDATE SET
            #             tanggal = ?, harga = ?, ema8 = ?, ema20 = ?, ema50 = ?, ema200 = ?,
            #             rsi = ?, volume = ?, avg_volume = ?, status_rekomendasi = ?
            #     WHEN NOT MATCHED THEN
            #         INSERT (ticker, tanggal, harga, ema8, ema20, ema50, ema200,
            #                 rsi, volume, avg_volume, status_rekomendasi)
            #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            # """, (
            #     ticker.replace(".JK", ""),
            #     latest.name.date(),
            #     round(float(latest['Close']), 2),
            #     round(float(latest['EMA8']), 2),
            #     round(float(latest['EMA20']), 2),
            #     round(float(latest['EMA50']), 2),
            #     round(float(latest['EMA200']), 2),
            #     round(float(latest['RSI']), 2),
            #     int(latest['Volume']),
            #     int(latest['AvgVolume10']),
            #     status,
            #     ticker.replace(".JK", ""),
            #     latest.name.date(),
            #     round(float(latest['Close']), 2),
            #     round(float(latest['EMA8']), 2),
            #     round(float(latest['EMA20']), 2),
            #     round(float(latest['EMA50']), 2),
            #     round(float(latest['EMA200']), 2),
            #     round(float(latest['RSI']), 2),
            #     int(latest['Volume']),
            #     int(latest['AvgVolume10']),
            #     status
            # ))


            conn.commit()

    cursor.close()
    conn.close()
    print("Screening selesai.")

if __name__ == "__main__":
    run_screener()
