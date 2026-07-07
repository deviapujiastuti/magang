import streamlit as st
import pandas as pd
from google_play_scraper import reviews, Sort
import requests
import time

# --- KONFIGURASI ---
PLAY_ID = "com.erafone.android"
APP_ID = "6749214274"
APP_NEGARA = "id"
NAMA = "Erafone"

def get_playstore_data(max_count=1000):
    hasil = []
    token = None
    # Mengambil batch 200 ulasan sampai batas max_count
    while len(hasil) < max_count:
        try:
            rvs, token = reviews(
                PLAY_ID, lang='id', country='id', 
                sort=Sort.NEWEST, count=200, continuation_token=token
            )
            for r in rvs:
                hasil.append({
                    "ulasan": r["content"], "rating": r["score"],
                    "tanggal": r["at"].strftime("%Y-%m-%d"), "sumber": "Play Store"
                })
            if not token: break
        except: break
    return pd.DataFrame(hasil)

def get_appstore_data(max_pages=10):
    hasil = []
    # Loop untuk 10 halaman (setiap halaman biasanya berisi 50 ulasan)
    for p in range(1, max_pages + 1):
        url = f"https://itunes.apple.com/{APP_NEGARA}/rss/customerreviews/page={p}/id={APP_ID}/sortBy=mostRecent/json"
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            entries = resp.json().get("feed", {}).get("entry", [])
            for e in entries:
                if "author" in e: # Hanya ambil ulasan, bukan metadata
                    hasil.append({
                        "ulasan": e.get("content", {}).get("label", ""),
                        "rating": int(e.get("im:rating", {}).get("label", 0)),
                        "tanggal": e.get("updated", {}).get("label", "")[:10],
                        "sumber": "App Store"
                    })
        except: break
        time.sleep(0.5)
    return pd.DataFrame(hasil)

# --- TAMPILAN APP ---
st.set_page_config(page_title="Erafone Review Scraper", layout="wide")
st.title("📊 Erafone Review Scraper")

if st.button("Ambil Data Terbaru"):
    with st.spinner('Scraping data dari App Store & Play Store...'):
        df_play = get_playstore_data(1000)
        df_app = get_appstore_data(10)
        
        df_final = pd.concat([df_play, df_app], ignore_index=True)
        
        if not df_final.empty:
            st.success(f"Berhasil mengumpulkan {len(df_final)} ulasan!")
            st.dataframe(df_final, use_container_width=True)
            
            # Download
            st.download_button("Download CSV", df_final.to_csv(index=False).encode('utf-8'), "data_ulasan.csv", "text/csv")
        else:
            st.warning("Data tidak ditemukan.")
