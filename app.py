import streamlit as st
import pandas as pd
from google_play_scraper import reviews, Sort
import requests
import time

# --- KONFIGURASI ---
PLAY_ID = "com.erafone.android"
APP_ID = "6749214274"
APP_NEGARA = "id"

# --- UI STREAMLIT ---
st.set_page_config(page_title="Erafone Review Scraper", layout="wide")
st.title("📊 Erafone Review Scraper")

# Pengaturan di Sidebar
st.sidebar.header("Pengaturan Scraping")
limit_play = st.sidebar.slider("Jumlah Play Store (maks)", 100, 1000, 200)
limit_app = st.sidebar.slider("Jumlah Halaman App Store", 1, 10, 2)

# --- FUNGSI (Sama seperti sebelumnya, hanya disesuaikan) ---
def get_playstore_data(max_count):
    hasil = []
    token = None
    while len(hasil) < max_count:
        try:
            rvs, token = reviews(PLAY_ID, lang='id', country='id', sort=Sort.NEWEST, count=200, continuation_token=token)
            for r in rvs:
                hasil.append({"ulasan": r["content"], "rating": r["score"], "tanggal": r["at"].strftime("%Y-%m-%d"), "sumber": "Play Store"})
            if not token: break
        except: break
    return pd.DataFrame(hasil)

def get_appstore_data(max_pages):
    hasil = []
    for p in range(1, max_pages + 1):
        url = f"https://itunes.apple.com/{APP_NEGARA}/rss/customerreviews/page={p}/id={APP_ID}/sortBy=mostRecent/json"
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            entries = resp.json().get("feed", {}).get("entry", [])
            for e in entries:
                if "author" in e:
                    hasil.append({"ulasan": e.get("content", {}).get("label", ""), "rating": int(e.get("im:rating", {}).get("label", 0)), "tanggal": e.get("updated", {}).get("label", "")[:10], "sumber": "App Store"})
        except: break
        time.sleep(0.3)
    return pd.DataFrame(hasil)

# --- LOGIKA EKSEKUSI ---
if st.button("Ambil Data Terbaru"):
    with st.spinner('Sedang mengumpulkan ulasan...'):
        df_play = get_playstore_data(limit_play)
        df_app = get_appstore_data(limit_app)
        
        df_final = pd.concat([df_play, df_app], ignore_index=True)
        
        if not df_final.empty:
            st.success(f"Berhasil mengambil {len(df_final)} ulasan!")
            st.dataframe(df_final, use_container_width=True)
            st.download_button("Download CSV", df_final.to_csv(index=False).encode('utf-8'), "data_ulasan.csv", "text/csv")
        else:
            st.warning("Data tidak ditemukan atau koneksi terputus.")
