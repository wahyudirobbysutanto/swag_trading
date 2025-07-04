import streamlit as st
import pandas as pd
from db_connector import get_connection

def show_latest_screening():
    st.title("📋 Data Screening Lengkap dengan Paging")

    conn = get_connection()
    tickers = pd.read_sql("SELECT DISTINCT ticker FROM SwingScreeningArchive", conn)['ticker'].tolist()
    tickers = [''] + tickers

    selected_ticker = st.selectbox("Filter berdasarkan ticker (kosong = semua):", tickers)

    # Ambil tanggal terakhir di tabel
    latest_date_df = pd.read_sql("SELECT MAX(tanggal) as max_tanggal FROM SwingScreeningArchive", conn)
    latest_date = latest_date_df['max_tanggal'].iloc[0]

    if selected_ticker == '':
        query = """
            SELECT tanggal, ticker, harga, ema8, ema20, ema50, ema200, rsi, volume, avg_volume, status_rekomendasi
            FROM SwingScreeningArchive
            WHERE tanggal = ?
            ORDER BY tanggal DESC
        """
        df = pd.read_sql(query, conn, params=[latest_date])
    else:
        query = """
            SELECT tanggal, ticker, harga, ema8, ema20, ema50, ema200, rsi, volume, avg_volume, status_rekomendasi
            FROM SwingScreeningArchive
            WHERE tanggal = ?
            AND ticker = ?
            ORDER BY tanggal DESC
        """
        df = pd.read_sql(query, conn, params=[latest_date, selected_ticker])

    conn.close()

    if df.empty:
        st.warning("Data tidak ditemukan.")
        return

    # Pagination settings
    page_size = 20
    total_pages = (len(df) - 1) // page_size + 1

    # Simpan page number di session_state
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1

    def next_page():
        if st.session_state.page_number < total_pages:
            st.session_state.page_number += 1

    def prev_page():
        if st.session_state.page_number > 1:
            st.session_state.page_number -= 1

    start_idx = (st.session_state.page_number - 1) * page_size
    end_idx = start_idx + page_size
    st.write(f"Menampilkan halaman {st.session_state.page_number} dari {total_pages}")

    st.dataframe(df.iloc[start_idx:end_idx])

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page_number > 1:
            st.button("⬅️ Prev", on_click=prev_page)
    with col3:
        if st.session_state.page_number < total_pages:
            st.button("Next ➡️", on_click=next_page)