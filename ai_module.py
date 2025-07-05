import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def get_ai_recommendation(ticker, tanggal, close, ema8, ema20, ema50, ema200, rsi, volume, avg_volume, status):
    prompt = f"""
    Saya ingin kamu bertindak sebagai analis teknikal saham berbasis swing trading EMA crossover.

    Berikut data teknikal saham {ticker} per {tanggal}:
    - Close: {close}
    - EMA8: {ema8}
    - EMA20: {ema20}
    - EMA50: {ema50}
    - RSI: {rsi}
    - Volume: {volume}
    - Avg Volume 10d: {avg_volume}
    - Status Screening: {status}

    Aturan strategi:
    1. Beli jika EMA8 > EMA20 dan harga > EMA50
    2. Volume harus lebih tinggi dari rata-rata
    3. RSI antara 55–75 dianggap ideal
    4. TP = resistance terdekat, CL = support terdekat atau breakdown EMA20
    5. Rasio risk:reward minimal 1:2

    Tugas kamu:
    - Evaluasi apakah setup ini valid untuk swing entry
    - Jika valid, berikan langsung angka pasti untuk Entry, TP, dan CL
    - Jangan jawab "perlu lihat chart", asumsikan kamu bisa melihat resistance dan support dari data historis
    - Jawab tegas dan langsung sesuai format

    Format jawaban:
    1. Validitas Setup: 
    2. Rekomendasi: 
    3. Entry Price: 
    4. Take Profit: 
    5. Cut Loss: 
    6. Alasan Singkat:
    """

    headers = {
        "Content-Type": "application/json"
    }

    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            GEMINI_URL + f"?key={GEMINI_API_KEY}",
            headers=headers,
            json=body,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        output = result["candidates"][0]["content"]["parts"][0]["text"]

        # print(output)
         # Optional: parsing ringan (bisa kamu sesuaikan sendiri)
        return output
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error from Gemini: {e}")
    except Exception as e:
        print(f"❌ Other error from Gemini: {e}")
    
    return None


def generate_recommendation_from_row(row):
    return get_ai_recommendation(
        ticker=row["ticker"],
        tanggal=row["tanggal"],
        close=row["harga"],
        ema8=row["ema8"],
        ema20=row["ema20"],
        ema50=row["ema50"],
        ema200=row.get("ema200", 0),  # jika belum tersedia
        rsi=row["rsi"],
        volume=row["volume"],
        avg_volume=row["avg_volume"],
        status=row["status_rekomendasi"]
    )
