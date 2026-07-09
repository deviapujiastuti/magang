import streamlit as st
import pandas as pd
import os
import time
import requests
from google_play_scraper import reviews as gp_reviews, Sort
from datetime import datetime

# --- KONFIGURASI ---
PLAY_ID = "com.erafone.android"
APP_ID = "6749214274"

st.set_page_config(page_title="Erafone Scraper", layout="wide")
st.title("📊 Erafone Review Scraper")

# --- FUNGSI CRAWLER ---

def scrape_playstore(app_id, count=200):
    # Mengambil data
    result, _ = gp_reviews(app_id, lang='id', country='id', sort=Sort.NEWEST, count=count)
    df = pd.DataFrame(result)
    
    if df.empty: return pd.DataFrame()
    
    # Menyesuaikan kolom
    df = df.rename(columns={
        'userName': 'nama_pengguna',
        'score': 'rating',
        'at': 'tanggal',
        'content': 'konten'
    })
    df = df[['nama_pengguna', 'rating', 'tanggal', 'konten']]
    df['sumber'] = 'Play Store'
    df['tanggal'] = df['tanggal'].dt.strftime('%Y-%m-%d') # Format tanggal
    return df

def scrape_appstore(app_id, pages=2):
    reviews_list = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for p in range(1, pages + 1):
        url = f"https://itunes.apple.com/id/rss/customerreviews/page={p}/id={app_id}/sortBy=mostRecent/json"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            entries = data.get("feed", {}).get("entry", [])
            
            # Skip entry pertama karena biasanya berisi info aplikasi, bukan review
            for entry in entries[1:]:
                reviews_list.append({
                    'nama_pengguna': entry.get('author', {}).get('name', {}).get('label'),
                    'rating': int(entry.get('im:rating', {}).get('label', 0)),
                    'tanggal': entry.get('updated', {}).get('label', "")[:10],
                    'konten': entry.get('content', {}).get('label', ""),
                    'sumber': 'App Store'
                })
        time.sleep(0.3)
    
    return pd.DataFrame(reviews_list)

# --- UI & LOGIKA ---

st.sidebar.header("Pengaturan")
limit_play = st.sidebar.slider("Jumlah Play Store", 100, 1000, 200)
limit_app = st.sidebar.slider("Halaman App Store", 1, 10, 2)

if st.button("Ambil Data Terbaru"):
    with st.spinner('Sedang mengumpulkan ulasan...'):
        df_play = scrape_playstore(PLAY_ID, limit_play)
        df_app = scrape_appstore(APP_ID, limit_app)
        
        df_final = pd.concat([df_play, df_app], ignore_index=True)
        
        if not df_final.empty:
            st.success(f"Berhasil mendapatkan {len(df_final)} ulasan!")
            # Menampilkan 5 kolom yang diminta
            st.dataframe(df_final[['nama_pengguna', 'rating', 'tanggal', 'konten', 'sumber']], use_container_width=True)
            
            # Download CSV
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, f"data_ulasan_{datetime.now().strftime('%Y-%m-%d')}.csv", "text/csv")
        else:
            st.warning("Data tidak ditemukan.")
