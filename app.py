
from google_play_scraper import reviews as gplay_reviews, Sort as GPlaySort
import requests
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
    """
    Mengambil ulasan Erafone dari Apple App Store lewat RSS feed publik resmi Apple.
    Endpoint ini tidak butuh API key, tapi punya beberapa batasan:
      - Maksimal sekitar 10 halaman x 50 ulasan = 500 ulasan per negara
      - Hanya menampilkan ulasan yang tersedia untuk negara (APPSTORE_NEGARA) tertentu
    """
    hasil = []
    halaman = 1
    maks_halaman = (jumlah // 50) + 1

    print(f"Mengambil ulasan dari App Store ...")

    while halaman <= maks_halaman:
        url = (
            f"https://itunes.apple.com/{APPSTORE_NEGARA}/rss/customerreviews/"
            f"page={halaman}/id={APPSTORE_APP_ID}/sortby=mostrecent/json"
        )

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  -> Gagal ambil halaman {halaman}: {e}")
            break

        entries = data.get("feed", {}).get("entry", [])

        # Entry pertama di halaman 1 biasanya cuma info aplikasi (bukan ulasan), bukan selalu ada
        entries = [e for e in entries if "im:rating" in e]

        if not entries:
            break  # sudah tidak ada ulasan lagi di halaman ini

        for e in entries:
            hasil.append({
                "teks_ulasan": e.get("content", {}).get("label", ""),
                "rating": int(e.get("im:rating", {}).get("label", 0)),
                "tanggal": e.get("updated", {}).get("label", "")[:10],  # ambil YYYY-MM-DD saja
                "sumber": "App Store",
                "nama_aplikasi": NAMA_APLIKASI,
            })

        halaman += 1
        time.sleep(1)

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
