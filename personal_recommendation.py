import streamlit as st
import pandas as pd
from db_connector import get_connection

def evaluate_position(last_close, buy_price, ema20):
    cut_loss_level = 0.95 * buy_price
    take_profit_level = 1.10 * buy_price

    if last_close < cut_loss_level and last_close < ema20:
        result = "🚨 CUT LOSS"
        color = "red"
    elif last_close > take_profit_level and last_close > ema20:
        result = "💰 TAKE PROFIT"
        color = "green"
    else:
        result = "🕰️ HOLD"
        color = "blue"

    return result, color


def show_personal_page():
    st.title("🧠 Personal Recommendation")

    conn = get_connection()
    tickers = pd.read_sql("SELECT DISTINCT ticker FROM SwingScreeningArchive", conn)['ticker'].tolist()

    ticker = st.selectbox("Pilih saham", [""] + tickers)
    buy_price = st.number_input("Masukkan harga beli Anda", min_value=0.0, format="%.2f")

    if ticker != "" and buy_price > 0:
        df = pd.read_sql("""
            SELECT TOP 1 * FROM SwingScreeningArchive 
            WHERE ticker = ? 
            ORDER BY tanggal DESC
        """, conn, params=[ticker])

        if df.empty:
            st.warning("Data tidak ditemukan.")
            return

        latest = df.iloc[0]
        last_close = latest['harga']
        rekom = latest['status_rekomendasi']
        tanggal = latest['tanggal']

        st.write(f"📅 Tanggal data terakhir: `{tanggal}`")
        st.write(f"📊 Harga penutupan terakhir: `{last_close}`")
        st.write(f"📌 Status screener: `{rekom}`")

        # LOGIKA EVALUASI
        result, color = evaluate_position(last_close, buy_price, latest['ema20'])

        # SIMPAN KE DATABASE DENGAN UPSERT (UPDATE JIKA SUDAH ADA)
        try:
            cursor = conn.cursor()
            today = pd.Timestamp.now().date()

            # Cek dulu apakah sudah ada record untuk ticker dan tanggal evaluasi hari ini
            check_sql = """
                SELECT COUNT(*) FROM PersonalRecommendationHistory
                WHERE ticker = ? AND tanggal_evaluasi = ?
            """
            cursor.execute(check_sql, (ticker, today))
            exists = cursor.fetchone()[0] > 0

            if exists:
                update_sql = """
                    UPDATE PersonalRecommendationHistory SET 
                        harga_beli = ?, harga_terakhir = ?, 
                        ema8 = ?, ema20 = ?, ema50 = ?, ema200 = ?,
                        rsi = ?, volume = ?, avg_volume = ?, 
                        status_screener = ?, hasil_rekomendasi = ?
                    WHERE ticker = ? AND tanggal_evaluasi = ? AND tanggal_data = ?
                """
                cursor.execute(update_sql, (
                    buy_price,
                    last_close,
                    latest['ema8'],
                    latest['ema20'],
                    latest['ema50'],
                    latest['ema200'],
                    latest['rsi'],
                    int(latest['volume']),
                    int(latest['avg_volume']),
                    rekom,
                    result.replace("🚨 ", "").replace("💰 ", "").replace("🕰️ ", ""),
                    ticker,
                    today,
                    tanggal
                ))
            else:
                insert_sql = """
                    INSERT INTO PersonalRecommendationHistory (
                        tanggal_evaluasi, tanggal_data, ticker, harga_beli, harga_terakhir, 
                        ema8, ema20, ema50, ema200, rsi, volume, avg_volume, 
                        status_screener, hasil_rekomendasi
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_sql, (
                    today,
                    tanggal,
                    ticker,
                    buy_price,
                    last_close,
                    latest['ema8'],
                    latest['ema20'],
                    latest['ema50'],
                    latest['ema200'],
                    latest['rsi'],
                    int(latest['volume']),
                    int(latest['avg_volume']),
                    rekom,
                    result.replace("🚨 ", "").replace("💰 ", "").replace("🕰️ ", "")
                ))

            conn.commit()
            st.success("📌 Rekomendasi disimpan/diupdate ke histori evaluasi.")
        except Exception as e:
            st.error(f"Gagal menyimpan histori: {e}")

        st.markdown(f"<h3 style='color:{color};'>{result}</h3>", unsafe_allow_html=True)

    conn.close()
