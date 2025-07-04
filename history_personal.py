import streamlit as st
import pandas as pd
from db_connector import get_connection

def show_history_personal():
    st.title("📜 History Evaluasi Personal")

    conn = get_connection()
    tickers = pd.read_sql("SELECT DISTINCT ticker FROM PersonalRecommendationHistory", conn)['ticker'].tolist()

    ticker = st.selectbox("Pilih saham untuk lihat histori evaluasi", [""] + tickers)

    if ticker != "":
        df = pd.read_sql("""
            SELECT tanggal_evaluasi, tanggal_data, harga_beli, harga_terakhir, 
                   ema8, ema20, ema50, ema200, rsi, volume, avg_volume, 
                   status_screener, hasil_rekomendasi
            FROM PersonalRecommendationHistory
            WHERE ticker = ?
            ORDER BY tanggal_evaluasi DESC
        """, conn, params=[ticker])

        if df.empty:
            st.warning("Data histori evaluasi tidak ditemukan.")
        else:
            st.dataframe(df)

    conn.close()
