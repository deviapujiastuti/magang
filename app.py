
import streamlit as st
import pandas as pd
import plotly.express as px
from google_play_scraper import reviews, Sort
import json
import os
import time

# ==============================
# KONFIGURASI
# ==============================

APP_LIST = [
    ("com.eraspace.app", "Eraspace"),
    ("com.erafone.android", "Erafone"),
]

BAHASA = "id"
NEGARA = "id"
OUTPUT_CSV = "hasil_ulasan_playstore.csv"
FILE_MEMORI = "sudah_diambil.json"

st.set_page_config(page_title="Dashboard Ulasan Play Store", layout="wide")

# ==============================
# FUNGSI BANTUAN (sama seperti versi command-line, cuma dibungkus ulang)
# ==============================

def muat_memori():
    if os.path.exists(FILE_MEMORI):
        with open(FILE_MEMORI, "r") as f:
            return json.load(f)
    return {}


def simpan_memori(memori):
    with open(FILE_MEMORI, "w") as f:
        json.dump(memori, f)


def muat_data_lama():
    if os.path.exists(OUTPUT_CSV):
        return pd.read_csv(OUTPUT_CSV)
    return pd.DataFrame(columns=["teks_ulasan", "rating", "tanggal", "nama_aplikasi"])


def ambil_ulasan_baru(app_id, nama_app, id_yang_sudah_ada, progress_callback=None):
    hasil_baru, id_baru = [], []
    token = None

    while True:
        result, token = reviews(
            app_id, lang=BAHASA, country=NEGARA,
            sort=Sort.NEWEST, count=200, continuation_token=token
        )
        if not result:
            break

        ketemu_data_lama = False
        for r in result:
            if r["reviewId"] in id_yang_sudah_ada:
                ketemu_data_lama = True
                break
            hasil_baru.append({
                "teks_ulasan": r["content"],
                "rating": r["score"],
                "tanggal": r["at"].strftime("%Y-%m-%d"),
                "nama_aplikasi": nama_app,
            })
            id_baru.append(r["reviewId"])

        if progress_callback:
            progress_callback(nama_app, len(hasil_baru))

        if ketemu_data_lama or token is None:
            break
        time.sleep(1)

    return hasil_baru, id_baru


# ==============================
# TAMPILAN DASHBOARD
# ==============================

st.title("📱 Dashboard Ulasan Play Store")
st.caption("Eraspace & Erafone")

# --- Tombol crawling ---
col1, col2 = st.columns([1, 3])
with col1:
    tombol_crawl = st.button("🔄 Ambil Ulasan Terbaru", type="primary", use_container_width=True)

status_area = st.empty()

if tombol_crawl:
    memori = muat_memori()
    semua_ulasan_baru = []

    progress_bar = st.progress(0, text="Memulai...")

    for i, (app_id, nama_app) in enumerate(APP_LIST):
        status_area.info(f"Mengecek ulasan baru: **{nama_app}** ...")
        id_yang_sudah_ada = set(memori.get(app_id, []))

        hasil_baru, id_baru = ambil_ulasan_baru(app_id, nama_app, id_yang_sudah_ada)
        semua_ulasan_baru.extend(hasil_baru)
        memori[app_id] = list(id_yang_sudah_ada.union(id_baru))

        progress_bar.progress((i + 1) / len(APP_LIST), text=f"Selesai: {nama_app} ({len(hasil_baru)} baru)")

    simpan_memori(memori)

    if semua_ulasan_baru:
        df_baru = pd.DataFrame(semua_ulasan_baru)
        df_baru = df_baru[["teks_ulasan", "rating", "tanggal", "nama_aplikasi"]]

        file_sudah_ada = os.path.exists(OUTPUT_CSV)
        df_baru.to_csv(
            OUTPUT_CSV,
            mode="a" if file_sudah_ada else "w",
            header=not file_sudah_ada,
            index=False,
            encoding="utf-8-sig"
        )
        status_area.success(f"✅ Berhasil! {len(df_baru)} ulasan baru ditambahkan.")
    else:
        status_area.warning("Tidak ada ulasan baru sejak terakhir kali dicek.")

    progress_bar.empty()

st.divider()

# --- Muat semua data (lama + baru) untuk ditampilkan ---
df = muat_data_lama()

if df.empty:
    st.info("Belum ada data. Klik tombol 'Ambil Ulasan Terbaru' di atas untuk mulai.")
else:
    df["tanggal"] = pd.to_datetime(df["tanggal"])

    # --- Filter sederhana ---
    aplikasi_terpilih = st.multiselect(
        "Filter aplikasi:",
        options=df["nama_aplikasi"].unique(),
        default=df["nama_aplikasi"].unique()
    )
    df_filtered = df[df["nama_aplikasi"].isin(aplikasi_terpilih)]

    # --- Ringkasan angka ---
    kolom1, kolom2, kolom3 = st.columns(3)
    kolom1.metric("Total Ulasan", len(df_filtered))
    kolom2.metric("Rata-rata Rating", f"{df_filtered['rating'].mean():.2f} ⭐")
    kolom3.metric("Jumlah Aplikasi", df_filtered["nama_aplikasi"].nunique())

    # --- Grafik ---
    grafik1, grafik2 = st.columns(2)

    with grafik1:
        rata_rata = df_filtered.groupby("nama_aplikasi")["rating"].mean().reset_index()
        fig1 = px.bar(
            rata_rata, x="nama_aplikasi", y="rating",
            title="Rata-rata Rating per Aplikasi",
            range_y=[0, 5], text_auto=".2f"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with grafik2:
        distribusi = df_filtered.groupby(["nama_aplikasi", "rating"]).size().reset_index(name="jumlah")
        fig2 = px.bar(
            distribusi, x="rating", y="jumlah", color="nama_aplikasi",
            barmode="group", title="Distribusi Rating (1-5 bintang)"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --- Tren waktu ---
    tren = df_filtered.groupby([pd.Grouper(key="tanggal", freq="W"), "nama_aplikasi"]).size().reset_index(name="jumlah_ulasan")
    fig3 = px.line(
        tren, x="tanggal", y="jumlah_ulasan", color="nama_aplikasi",
        title="Tren Jumlah Ulasan per Minggu", markers=True
    )
    st.plotly_chart(fig3, use_container_width=True)

    # --- Tabel data ---
    st.subheader("Data Ulasan")
    st.dataframe(
        df_filtered.sort_values("tanggal", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # --- Download ---
    st.download_button(
        "⬇️ Download CSV",
        data=df_filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="ulasan_playstore.csv",
        mime="text/csv"
    )
