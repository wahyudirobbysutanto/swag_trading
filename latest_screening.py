import streamlit as st
import pandas as pd
from db_connector import get_connection
from ai_module import generate_recommendation_from_row

def show_latest_screening():
    st.title("📋 Screening Saham (Status 'yes%') + AI Reason")

    conn = get_connection()
    latest_date = pd.read_sql("SELECT MAX(tanggal) as max_tanggal FROM SwingScreeningArchive", conn)['max_tanggal'].iloc[0]

    tickers = pd.read_sql("""
        SELECT DISTINCT ticker 
        FROM SwingScreeningArchive 
        WHERE status_rekomendasi LIKE 'yes%' AND tanggal = ?
        ORDER BY ticker
    """, conn, params=[latest_date])['ticker'].tolist()
    tickers = [''] + tickers

    selected_ticker = st.selectbox("Filter berdasarkan ticker:", tickers)

    if selected_ticker == '':
        df = pd.read_sql("""
            SELECT ArchiveID, tanggal, ticker, harga, ema8, ema20, ema50, rsi, volume, avg_volume, status_rekomendasi, ai_reason
            FROM SwingScreeningArchive
            WHERE tanggal = ? AND status_rekomendasi LIKE 'yes%'
            ORDER BY ticker
        """, conn, params=[latest_date])
    else:
        df = pd.read_sql("""
            SELECT ArchiveID, tanggal, ticker, harga, ema8, ema20, ema50, rsi, volume, avg_volume, status_rekomendasi, ai_reason
            FROM SwingScreeningArchive
            WHERE tanggal = ? AND ticker = ? AND status_rekomendasi LIKE 'yes%'
            ORDER BY ticker
        """, conn, params=[latest_date, selected_ticker])

    if df.empty:
        st.warning("Tidak ada data.")
        conn.close()
        return

    # Pagination
    page_size = 15
    total_pages = (len(df) - 1) // page_size + 1
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1

    start_idx = (st.session_state.page_number - 1) * page_size
    end_idx = start_idx + page_size
    page_df = df.iloc[start_idx:end_idx]

    st.write(f"Menampilkan halaman {st.session_state.page_number} dari {total_pages}")

    for _, row in page_df.iterrows():
        st.subheader(f"{row['ticker']} ({row['status_rekomendasi']}) — {row['tanggal'].strftime('%d-%b-%Y')}")
        st.write(f"Harga: `{row['harga']}` | EMA8: `{row['ema8']}` | EMA20: `{row['ema20']}` | EMA50: `{row['ema50']}`")
        st.write(f"RSI: `{row['rsi']}` | Volume: `{row['volume']}` | Avg Volume: `{row['avg_volume']}`")

        if pd.isna(row['ai_reason']) or str(row['ai_reason']).strip() == "":
            if st.button(f"⚡ Generate AI Reason untuk {row['ticker']}", key=f"gen_{row['ArchiveID']}"):
                reason = generate_recommendation_from_row(row)
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE SwingScreeningArchive
                            SET ai_reason = ?
                            WHERE ArchiveID = ?
                        """, (reason, int(row['ArchiveID'])))
                        conn.commit()
                    st.success("✅ AI Reason berhasil disimpan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan: {e}")
        else:
            with st.expander("📌 AI Reason"):
                st.code(row['ai_reason'], language='markdown')

        st.markdown("---")

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page_number > 1:
            st.button("⬅️ Prev", on_click=lambda: st.session_state.update(page_number=st.session_state.page_number - 1))
    with col3:
        if st.session_state.page_number < total_pages:
            st.button("Next ➡️", on_click=lambda: st.session_state.update(page_number=st.session_state.page_number + 1))

    conn.close()
