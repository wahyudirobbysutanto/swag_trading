import yfinance as yf
import pandas as pd
from db_connector import get_connection
from datetime import datetime
from scrap_idx import get_idx_tickers_from_excel

def run_volume_filter(threshold=1000000):
    tickers = get_idx_tickers_from_excel('data/Stock_List.xlsx')
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.today().date()

    for ticker in tickers:
        df = yf.download(ticker, period='250d', interval='1d')
        if df.empty or len(df) < 10:
            continue

        avg_vol = df['Volume'].rolling(window=10).mean()
        avg_vol_value = float(avg_vol.iloc[-1])

        if pd.isna(avg_vol_value):
            continue

        print(avg_vol_value)


        is_active = 1 
        if avg_vol_value >= threshold:
            is_active = 1
        else:
            is_active = 0



        last_vol = df['Volume'].iloc[-1]
        last_close = df['Close'].iloc[-1]

        ticker_clean = ticker.replace(".JK", "")

        cursor.execute("""
            MERGE ActiveVolumeStocks AS target
            USING (SELECT ? AS ticker) AS source
            ON target.ticker = source.ticker
            WHEN MATCHED THEN
                UPDATE SET 
                    tanggal = ?, avg_volume = ?, volume = ?, 
                    close_price = ?, active = ?
            WHEN NOT MATCHED THEN
                INSERT (ticker, tanggal, avg_volume, volume, close_price, active)
                VALUES (?, ?, ?, ?, ?, ?);
        """, (
            ticker_clean,
            today, int(avg_vol_value), int(last_vol), float(last_close), is_active,
            ticker_clean,
            today, int(avg_vol_value), int(last_vol), float(last_close), is_active
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Update status aktif saham selesai.")

if __name__ == "__main__":
    run_volume_filter()
