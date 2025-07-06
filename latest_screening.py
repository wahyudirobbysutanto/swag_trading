import streamlit as st
import pandas as pd
from db_connector import get_connection
from ai_module import generate_recommendation_from_row

def show_latest_screening():
    st.title("📋 Screening Saham Harian")

    conn = get_connection()
    latest_date = pd.read_sql("SELECT MAX(tanggal) as max_tanggal FROM SwingScreeningArchive", conn)['max_tanggal'].iloc[0]

    # Ambil semua data di tanggal terbaru
    df = pd.read_sql("""
        SELECT ArchiveID, tanggal, ticker, harga, ema8, ema20, ema50, rsi, volume, avg_volume,
               status_rekomendasi, ai_reason,
               ema8_weekly, ema20_weekly, ema50_weekly, rsi_weekly
        FROM SwingScreeningArchive
        WHERE tanggal = ?
    """, conn, params=[latest_date])

    if df.empty:
        st.warning("Tidak ada data screening ditemukan.")
        conn.close()
        return

    # Ticker dropdown
    ticker_options = sorted(df['ticker'].unique().tolist())
    selected_ticker = st.selectbox("🔍 Pilih Ticker (kosongkan untuk semua):", options=[""] + ticker_options)

    # Filter jika user pilih ticker
    if selected_ticker:
        df = df[df['ticker'] == selected_ticker]

    # Prioritaskan yang status_rekomendasi LIKE 'yes%'
    df['yes_priority'] = df['status_rekomendasi'].str.startswith('yes')
    df = df.sort_values(by=['yes_priority', 'ticker'], ascending=[False, True]).reset_index(drop=True)

    # Pagination setup
    page_size = 10
    total_pages = (len(df) - 1) // page_size + 1
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1

    # Navigasi halaman
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.page_number > 1:
            st.button("⬅️ Prev", on_click=lambda: st.session_state.update(page_number=st.session_state.page_number - 1))
    with col3:
        if st.session_state.page_number < total_pages:
            st.button("Next ➡️", on_click=lambda: st.session_state.update(page_number=st.session_state.page_number + 1))

    start_idx = (st.session_state.page_number - 1) * page_size
    end_idx = start_idx + page_size
    page_df = df.iloc[start_idx:end_idx]

    for _, row in page_df.iterrows():
        st.subheader(f"{row['ticker']} ({row['status_rekomendasi']}) — {row['tanggal'].strftime('%d-%b-%Y')}")
        st.write(f"""
        Harga: `{row['harga']}` | EMA8: `{row['ema8']}` | EMA20: `{row['ema20']}` | EMA50: `{row['ema50']}`  
        RSI: `{row['rsi']}` | Volume: `{row['volume']}` | Avg Volume: `{row['avg_volume']}`  
        📊 **Weekly:** EMA8: `{row['ema8_weekly']}` | EMA20: `{row['ema20_weekly']}` | EMA50: `{row['ema50_weekly']}` | RSI: `{row['rsi_weekly']}`
        """)

        weekly_filled = all(not pd.isna(row.get(col)) for col in ['ema8_weekly', 'ema20_weekly', 'ema50_weekly', 'rsi_weekly'])
        ai_empty = pd.isna(row['ai_reason']) or str(row['ai_reason']).strip() == ""

        if not weekly_filled:
            with st.expander("🛠️ Isi data teknikal mingguan"):
                with st.form(key=f"form_weekly_{row['ArchiveID']}"):
                    ema8_w = st.number_input("EMA8 Weekly", value=row['ema8_weekly'] or 0.0, key=f"ema8_{row['ArchiveID']}")
                    ema20_w = st.number_input("EMA20 Weekly", value=row['ema20_weekly'] or 0.0, key=f"ema20_{row['ArchiveID']}")
                    ema50_w = st.number_input("EMA50 Weekly", value=row['ema50_weekly'] or 0.0, key=f"ema50_{row['ArchiveID']}")
                    rsi_w = st.number_input("RSI Weekly", value=row['rsi_weekly'] or 0.0, key=f"rsi_{row['ArchiveID']}")
                    submit = st.form_submit_button("💾 Simpan Data Weekly")
                    if submit:
                        try:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE SwingScreeningArchive
                                    SET ema8_weekly = ?, ema20_weekly = ?, ema50_weekly = ?, rsi_weekly = ?
                                    WHERE ArchiveID = ?
                                """, (ema8_w, ema20_w, ema50_w, rsi_w, int(row['ArchiveID'])))
                                conn.commit()
                            st.success("✅ Data weekly berhasil disimpan.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal menyimpan: {e}")
        elif ai_empty:
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

    conn.close()
