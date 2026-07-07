import streamlit as st
import pandas as pd
from google_play_scraper import reviews as gplay_reviews, Sort as GPlaySort
import requests
import time

# --- KONFIGURASI ---
PLAYSTORE_APP_ID = "com.erafone.android"
APPSTORE_APP_ID = "6749214274"
APPSTORE_NEGARA = "id"
NAMA_APLIKASI = "Erafone"

# --- FUNGSI SCRAPING (Dioptimasi untuk Streamlit) ---

def ambil_dari_playstore(jumlah=200):
    hasil = []
    token = None
    sisa = jumlah
    while sisa > 0:
        batch_size = min(200, sisa)
        result, token = gplay_reviews(
            PLAYSTORE_APP_ID, lang="id", country="id", 
            sort=GPlaySort.NEWEST, count=batch_size, continuation_token=token
        )
        if not result: break
        for r in result:
            hasil.append({
                "teks_ulasan": r["content"],
                "rating": r["score"],
                "tanggal": r["at"].strftime("%Y-%m-%d"),
                "sumber": "Play Store",
                "nama_aplikasi": NAMA_APLIKASI,
            })
        sisa -= len(result)
        if token is None: break
        time.sleep(0.5)
    return hasil

def ambil_dari_appstore(jumlah=200):
    hasil = []
    # Apple RSS feed biasanya membatasi jumlah per halaman dan total halaman.
    # Kita coba ambil dari page 1 saja, karena biasanya data terbaru ada di sana.
    url = f"https://itunes.apple.com/{APPSTORE_NEGARA}/rss/customerreviews/id={APPSTORE_APP_ID}/sortBy=mostRecent/json"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} # Apple kadang memblokir request tanpa User-Agent
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        entries = data.get("feed", {}).get("entry", [])
        
        # Saring entri agar hanya mengambil ulasan (melewati entri info aplikasi)
        for e in entries:
            # RSS Apple punya entri 'author' yang tidak ada di objek aplikasi
            if "author" in e:
                hasil.append({
                    "teks_ulasan": e.get("content", {}).get("label", ""),
                    "rating": int(e.get("im:rating", {}).get("label", 0)),
                    "tanggal": e.get("updated", {}).get("label", "")[:10],
                    "sumber": "App Store",
                    "nama_aplikasi": NAMA_APLIKASI,
                })
    except Exception as e:
        print(f"Error App Store: {e}")
        
    return hasil

# --- UI STREAMLIT ---

st.set_page_config(page_title="Scraper Ulasan Erafone", layout="wide")
st.title("📊 Erafone Review Scraper")

if st.button("Mulai Ambil Data"):
    with st.spinner('Sedang mengambil data... Mohon tunggu.'):
        data_play = ambil_dari_playstore(100) # Bisa disesuaikan
        data_app = ambil_dari_appstore(100)
        
        df = pd.DataFrame(data_play + data_app)
        
        if not df.empty:
            st.success(f"Berhasil mendapatkan {len(df)} ulasan!")
            
            # Tampilkan Data
            st.dataframe(df, use_container_width=True)
            
            # Tombol Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data sebagai CSV",
                data=csv,
                file_name='ulasan_erafone.csv',
                mime='text/csv',
            )
        else:
            st.error("Data gagal diambil. Coba periksa koneksi atau ID aplikasi.")
