
from google_play_scraper import reviews as gplay_reviews, Sort as GPlaySort
from app_store_scraper import AppStore
import pandas as pd
import time

# ==============================
# 1. KONFIGURASI
# ==============================

# --- Play Store ---
PLAYSTORE_APP_ID = "com.erafone.android"
PLAYSTORE_JUMLAH = 200
BAHASA = "id"
NEGARA = "id"

# --- App Store ---
APPSTORE_APP_ID = "6749214274"     # ID numerik dari URL apps.apple.com/.../id6749214274
APPSTORE_APP_NAME = "erafone"       # nama slug di URL App Store
APPSTORE_NEGARA = "id"              # kode negara App Store (id = Indonesia)
APPSTORE_JUMLAH = 200

NAMA_APLIKASI = "Erafone"

# ==============================
# 2. FUNGSI: AMBIL DARI PLAY STORE
# ==============================

def ambil_dari_playstore(jumlah=200):
    """Mengambil ulasan Erafone dari Google Play Store."""
    hasil = []
    token = None
    sisa = jumlah

    print(f"Mengambil ulasan dari Play Store ...")

    while sisa > 0:
        batch_size = min(200, sisa)
        result, token = gplay_reviews(
            PLAYSTORE_APP_ID,
            lang=BAHASA,
            country=NEGARA,
            sort=GPlaySort.NEWEST,
            count=batch_size,
            continuation_token=token
        )

        if not result:
            break

        for r in result:
            hasil.append({
                "teks_ulasan": r["content"],
                "rating": r["score"],
                "tanggal": r["at"].strftime("%Y-%m-%d"),
                "sumber": "Play Store",
                "nama_aplikasi": NAMA_APLIKASI,
            })

        sisa -= len(result)

        if token is None:
            break
        time.sleep(1)

    print(f"  -> Berhasil mengambil {len(hasil)} ulasan dari Play Store.\n")
    return hasil


# ==============================
# 3. FUNGSI: AMBIL DARI APP STORE
# ==============================

def ambil_dari_appstore(jumlah=200):
    """Mengambil ulasan Erafone dari Apple App Store."""
    hasil = []

    print(f"Mengambil ulasan dari App Store ...")

    try:
        app = AppStore(country=APPSTORE_NEGARA, app_name=APPSTORE_APP_NAME, app_id=APPSTORE_APP_ID)
        app.review(how_many=jumlah)

        for r in app.reviews:
            hasil.append({
                "teks_ulasan": r.get("review", ""),
                "rating": r.get("rating"),
                "tanggal": r.get("date").strftime("%Y-%m-%d") if r.get("date") else "",
                "sumber": "App Store",
                "nama_aplikasi": NAMA_APLIKASI,
            })
    except Exception as e:
        print(f"  -> GAGAL mengambil dari App Store: {e}")
        print(f"  -> Catatan: App Store TIDAK punya rating negara Indonesia untuk semua app.")
        print(f"     Kalau APPSTORE_NEGARA='id' gagal, coba ganti ke negara lain (misal 'us').\n")

    print(f"  -> Berhasil mengambil {len(hasil)} ulasan dari App Store.\n")
    return hasil


# ==============================
# 4. EKSEKUSI UTAMA
# ==============================

def main():
    semua_ulasan = []

    semua_ulasan.extend(ambil_dari_playstore(PLAYSTORE_JUMLAH))
    semua_ulasan.extend(ambil_dari_appstore(APPSTORE_JUMLAH))

    df = pd.DataFrame(semua_ulasan)

    if df.empty:
        print("Tidak ada ulasan yang berhasil diambil dari kedua sumber.")
        return

    # Urutkan kolom: teks, rating, tanggal, sumber, nama aplikasi
    df = df[["teks_ulasan", "rating", "tanggal", "sumber", "nama_aplikasi"]]

    output_file = "hasil_ulasan_erafone_multiplatform.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"Selesai! Total {len(df)} ulasan disimpan ke '{output_file}'")
    print(df["sumber"].value_counts())


if __name__ == "__main__":
    main()
