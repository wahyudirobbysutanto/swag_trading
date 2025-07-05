import streamlit as st
import pandas as pd
from db_connector import get_connection
from ai_module import generate_recommendation_from_row

def show_latest_screening():
    st.title("📋 Data Screening: Status 'yes%' dengan AI Reason")

    conn = get_connection()
    tickers = pd.read_sql("""
        SELECT DISTINCT ticker 
        FROM SwingScreeningArchive 
        WHERE status_rekomendasi LIKE 'yes%'
    """, conn)['ticker'].tolist()
    tickers = [''] + tickers

    selected_ticker = st.selectbox("Filter berdasarkan ticker (kosong = semua):", tickers)

    # Ambil tanggal terakhir
    latest_date_df = pd.read_sql("SELECT MAX(tanggal) as max_tanggal FROM SwingScreeningArchive", conn)
    latest_date = latest_date_df['max_tanggal'].iloc[0]

    if selected_ticker == '':
        query = """
            SELECT ArchiveID, tanggal, ticker, harga, ema8, ema20, ema50, rsi, volume, avg_volume, status_rekomendasi, ai_reason FROM SwingScreeningArchive
            WHERE tanggal = ? AND status_rekomendasi LIKE 'yes%'
            ORDER BY tanggal DESC
        """
        df = pd.read_sql(query, conn, params=[latest_date])
    else:
        query = """
            SELECT ArchiveID, tanggal, ticker, harga, ema8, ema20, ema50, rsi, volume, avg_volume, status_rekomendasi, ai_reason FROM SwingScreeningArchive
            WHERE tanggal = ? AND ticker = ? AND status_rekomendasi LIKE 'yes%'
            ORDER BY tanggal DESC
        """
        df = pd.read_sql(query, conn, params=[latest_date, selected_ticker])

    if df.empty:
        st.warning("Data tidak ditemukan.")
        conn.close()
        return

    # Pagination
    page_size = 20
    total_pages = (len(df) - 1) // page_size + 1
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
    subset_df = df.iloc[start_idx:end_idx]
    st.dataframe(subset_df[[
        "tanggal", "ticker", "harga", "ema8", "ema20", "ema50",
        "rsi", "volume", "avg_volume", "status_rekomendasi", "ai_reason"
    ]])

    for i, row in subset_df.iterrows():
        if pd.isna(row['ai_reason']) or str(row['ai_reason']).strip() == "":
            with st.expander(f"🎯 {row['ticker']} belum ada AI Reason (ID {row['ArchiveID']})"):
                if st.button(f"🔍 Generate untuk {row['ticker']}", key=f"gen_{row['ArchiveID']}"):
                    reason = generate_recommendation_from_row(row)
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE SwingScreeningArchive
                            SET ai_reason = ?
                            WHERE ArchiveID = ?
                        """, (reason, int(row['ArchiveID'])))
                        conn.commit()
                        st.success(f"✅ AI Reason disimpan: {reason}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menyimpan: {e}")

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page_number > 1:
            st.button("⬅️ Prev", on_click=prev_page)
    with col3:
        if st.session_state.page_number < total_pages:
            st.button("Next ➡️", on_click=next_page)

    conn.close()
