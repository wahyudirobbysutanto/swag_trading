
# Swing Trading Prototype

Aplikasi sederhana untuk screening saham dan rekomendasi trading jangka pendek (swing trading) berbasis Python, Streamlit, dan SQL Server.

---

## Fitur

- **Screening saham historis** menggunakan data harga dan indikator teknikal (EMA8, EMA20, EMA50, EMA200, RSI, Volume)
- Penyimpanan hasil screening ke database SQL Server
- Tampilan chart interaktif ala Stockbit dengan plot harga, EMA, dan volume
- Personal Recommendation berdasarkan harga beli dan status teknikal (Cut Loss, Hold, Take Profit)
- Penyimpanan histori evaluasi personal ke database dengan fitur update data
- Halaman khusus untuk melihat histori evaluasi personal per saham

---

## Struktur Folder dan File

```
swing_trading_prototype/
│
├── app.py                   # Entry point aplikasi Streamlit (multi-page)
├── chart_view.py            # Halaman chart saham dan plot indikator
├── personal_recommendation.py # Halaman personal recommendation dan simpan evaluasi
├── history_personal.py      # Halaman untuk melihat histori evaluasi personal
├── db_connector.py          # Modul koneksi database SQL Server
├── scrap_idx.py             # Script ambil daftar ticker LQ45 dari Excel
├── historical_screener.py   # Script untuk download data dan screening saham historis
├── latest_screening.py      # Halaman untuk melihat data terakhir yang di cron saat malam (hari kemarin)
├── data/
│   └── Daftar Saham.xlsx    # File Excel daftar ticker LQ45
├── requirements.txt         # Daftar dependency Python
└── README.md                # Dokumentasi proyek (file ini)
```

---

## Setup dan Instalasi

1. Clone repository ini:

```bash
git clone https://github.com/wahyudirobbysutanto/swing_trading.git
cd swing_trading_prototype
```

2. Buat dan aktifkan virtual environment (disarankan):

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

- **Chart Screening:** Pilih ticker saham dari dropdown untuk melihat chart harga dan indikator EMA & volume
- **Personal Recommendation:** Masukkan ticker dan harga beli untuk mendapatkan rekomendasi Cut Loss, Hold, atau Take Profit, lalu simpan ke database
- **History Evaluasi:** Pilih ticker untuk melihat histori rekomendasi yang pernah disimpan

---

## Struktur Database

**Tabel SwingScreeningArchive**

| Kolom           | Tipe       | Keterangan                    |
|-----------------|------------|------------------------------|
| ticker          | VARCHAR    | Kode saham                   |
| tanggal         | DATE       | Tanggal data                 |
| harga           | FLOAT      | Harga penutupan              |
| ema8, ema20,... | FLOAT      | Nilai indikator EMA, RSI, dsb|

**Tabel PersonalRecommendationHistory**

| Kolom            | Tipe       | Keterangan                    |
|------------------|------------|------------------------------|
| id               | INT (PK)   | Primary key auto increment    |
| tanggal_evaluasi | DATE       | Tanggal rekomendasi dibuat    |
| tanggal_data     | DATE       | Tanggal data harga terakhir   |
| ticker           | VARCHAR    | Kode saham                   |
| harga_beli       | FLOAT      | Harga beli pengguna          |
| harga_terakhir   | FLOAT      | Harga terakhir saham         |
| ema8, ema20,...  | FLOAT      | Nilai indikator              |
| status_screener  | VARCHAR    | Status dari screening        |
| hasil_rekomendasi| VARCHAR    | Cut Loss, Hold, Take Profit  |

---

## Catatan

- Pastikan database dan tabel sudah dibuat sesuai dengan script SQL di repo
- Streaming data dan update bisa disesuaikan untuk kebutuhan real-time
- Sesuaikan konfigurasi koneksi database di `.env`

---

## License

MIT License © [Your Name]

---
