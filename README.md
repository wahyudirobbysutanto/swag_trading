# Swing Trading Prototype

Aplikasi sederhana untuk screening saham dan rekomendasi trading jangka pendek (swing trading) berbasis Python, Streamlit, dan SQL Server.

---

## Fitur

- Screening saham historis dengan indikator teknikal (EMA8, EMA20, EMA50, EMA200, RSI, Volume)
- Penyimpanan hasil screening harian ke database SQL Server
- Filter volume aktif untuk menyaring saham dengan rata-rata volume layak diproses
- Tampilan chart interaktif ala Stockbit dengan plotting harga, EMA, dan volume
- Rekomendasi personal berdasarkan harga beli pengguna dan status teknikal (Cut Loss, Hold, Take Profit)
- Penyimpanan histori rekomendasi personal ke database dengan fitur update otomatis
- Halaman untuk melihat histori evaluasi pribadi per saham

---

## Struktur Folder dan File

```
swing_trading_prototype/
│
├── app.py                     # Entry point aplikasi Streamlit (multi-page)
├── chart_view.py              # Halaman chart saham dan indikator teknikal
├── personal_recommendation.py # Halaman input harga beli dan simpan evaluasi
├── history_personal.py        # Halaman untuk melihat histori evaluasi personal
├── db_connector.py            # Modul koneksi database SQL Server
├── scrap_idx.py               # Script ambil daftar ticker dari file Excel
├── historical_screener.py     # Screening historis (manual)
├── backend_screener.py        # Screening terbaru per hari (dijalankan manual / cron)
├── volume_filter.py           # Filter saham aktif berdasarkan rata-rata volume
├── data/
│   └── Daftar Saham.xlsx      # Daftar ticker saham (misal LQ45)
├── requirements.txt           # Daftar dependency Python
└── README.md                  # Dokumentasi proyek ini
```

---

## Setup dan Instalasi

1. Clone repository ini:

```bash
git clone https://github.com/wahyudirobbysutanto/swing_trading.git
cd swing_trading_prototype
```

2. Buat dan aktifkan virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Buat file `.env` di root folder dan isi konfigurasi database SQL Server:

```env
DB_SERVER=your_server_address
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

5. Jalankan aplikasi Streamlit:

```bash
streamlit run app.py
```

---

## Cara Penggunaan

- **Chart Screening:** Pilih saham untuk melihat harga dan indikator teknikal
- **Personal Recommendation:** Masukkan harga beli, sistem akan memberi saran (Hold, Take Profit, Cut Loss)
- **History Evaluasi:** Cek riwayat rekomendasi pribadi per saham
- **Volume Filter:** Jalankan `volume_filter.py` untuk memperbarui saham aktif
- **Screening Harian:** Jalankan `backend_screener.py` untuk menyimpan hasil screening terbaru ke database

---

## Struktur Database

### Tabel `SwingScreeningArchive`

| Kolom           | Tipe     | Keterangan                      |
|-----------------|----------|---------------------------------|
| ticker          | VARCHAR  | Kode saham                      |
| tanggal         | DATE     | Tanggal data                    |
| harga           | FLOAT    | Harga penutupan terakhir        |
| ema8            | FLOAT    | EMA 8 hari                      |
| ema20           | FLOAT    | EMA 20 hari                     |
| ema50           | FLOAT    | EMA 50 hari                     |
| ema200          | FLOAT    | EMA 200 hari                    |
| rsi             | FLOAT    | RSI (14)                        |
| volume          | BIGINT   | Volume transaksi terakhir       |
| avg_volume      | BIGINT   | Rata-rata volume 10 hari        |
| status_rekomendasi | VARCHAR | Status dari screener (yes, no, dll) |

### Tabel `ActiveVolumeStocks`

| Kolom     | Tipe     | Keterangan                      |
|-----------|----------|---------------------------------|
| ticker    | VARCHAR  | Kode saham                      |
| tanggal   | DATE     | Tanggal update volume terakhir  |
| avg_volume| BIGINT   | Rata-rata volume 10 hari        |
| volume    | BIGINT   | Volume terakhir                 |
| close_price | FLOAT  | Harga terakhir                  |
| active    | BIT      | 1 = aktif, 0 = tidak aktif      |

### Tabel `PersonalRecommendationHistory`

| Kolom              | Tipe     | Keterangan                      |
|--------------------|----------|---------------------------------|
| id                 | INT      | Primary key, auto increment     |
| tanggal_evaluasi   | DATE     | Tanggal evaluasi dilakukan      |
| tanggal_data       | DATE     | Tanggal data harga digunakan    |
| ticker             | VARCHAR  | Kode saham                      |
| harga_beli         | FLOAT    | Harga beli user                 |
| harga_terakhir     | FLOAT    | Harga saat ini                  |
| ema8, ema20, ...   | FLOAT    | Indikator teknikal              |
| rsi, volume, avg_volume | FLOAT | Data teknikal tambahan         |
| status_screener    | VARCHAR  | Status dari screening harian    |
| hasil_rekomendasi  | VARCHAR  | Cut Loss, Hold, Take Profit     |

---

## License

MIT License © Wahyudi Robby Sutanto