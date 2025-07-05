import pandas as pd
from ai_module import generate_recommendation_from_row
from db_connector import get_connection


def ai_recommendation(ticker):
    conn = get_connection()

    # Ambil data terakhir untuk satu ticker
    df = pd.read_sql("""
        SELECT TOP 1 * FROM SwingScreeningArchive 
        WHERE ticker = ? 
        ORDER BY tanggal DESC
    """, conn, params=[ticker])

    if df.empty:
        print(f"❌ Tidak ada data untuk ticker {ticker}")
        return

    row = df.iloc[0]
    recommendation = generate_recommendation_from_row(row)
    print(f"✅ Rekomendasi AI untuk {ticker}:\n{recommendation}")

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE SwingScreeningArchive
            SET ai_reason = ?
            WHERE ArchiveID = ?
        """, (recommendation, int(row['ArchiveID'])))
        conn.commit()
        cursor.close()
        print("✅ Rekomendasi disimpan ke kolom ai_reason.")
    except Exception as e:
        print(f"❌ Gagal menyimpan ke database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    ticker_input = input("Masukkan kode ticker (contoh: DIVA): ").strip().upper()
    ai_recommendation(ticker_input)
