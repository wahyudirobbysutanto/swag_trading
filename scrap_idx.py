import pandas as pd

def get_idx_tickers_from_excel(filepath='data/Daftar Saham.xlsx'):
    try:
        df = pd.read_excel(filepath)
        
        # Pastikan kolom 'Kode' ada
        if 'Kode' not in df.columns:
            raise ValueError("Kolom 'Kode' tidak ditemukan di file Excel.")
        
        tickers = df['Kode'].dropna().astype(str).str.strip() + '.JK'
        return tickers.tolist()
    
    except Exception as e:
        print(f"Gagal membaca ticker dari Excel: {e}")
        return []

# Contoh pemanggilan
# if __name__ == "__main__":
#     tickers = get_idx_tickers_from_excel()
#     print(f"Total saham ditemukan: {len(tickers)}")
#     print("Contoh 10 ticker:", tickers[:10])
