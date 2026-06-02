import time
import schedule
import subprocess
from datetime import datetime # Tambahan untuk timestamp yang lebih presisi
from pymongo import MongoClient
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT

# --- KONFIGURASI MONGODB ---
# Update URI dengan autentikasi admin agar tidak kena error ditolak
MONGO_URI = "mongodb://admin:passwordkuat123@localhost:27017/"
DB_NAME = "mbg_db"
COLLECTION_NAME = "raw_mbg"

# --- KONFIGURASI YOUTUBE ---
keyword = "Makan Bergizi Gratis"
jumlah_video = 15
komentar_per_video = 50

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
downloader = YoutubeCommentDownloader()

def jalankan_crawler():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Memulai Crawling: '{keyword}' ---")
    data_baru_masuk = 0

    # Ambil ID dan Title video menggunakan yt-dlp
    cmd_list = [
        "python", "-m", "yt_dlp",
        f"ytsearch{jumlah_video}:{keyword}",
        "--get-id", "--get-title",
        "--match-filter", "!is_live"
    ]
    process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()

    if error and not output:
        print("⚠️ ADA ERROR DARI YOUTUBE:\n", error)
        return

    lines = output.strip().split('\n')
    video_list = []
    # Parsing output yt-dlp (Title dan ID selang-seling)
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            video_list.append({'title': lines[i], 'id': lines[i+1]})

    for v in video_list:
        video_url = f"https://www.youtube.com/watch?v={v['id']}" # [REKOMENDASI 2: Metadata Video]
        print(f"Mengambil komentar dari: {v['title']}...")

        try:
            comments = downloader.get_comments_from_url(video_url, sort_by=SORT_BY_RECENT)

            count = 0
            for comment in comments:
                # Membersihkan teks dari spasi berlebih
                text = comment.get('text', '').strip()
                
                # [OPTIMASI TAMBAHAN: Filter Komentar Pendek]
                if len(text) < 15:
                    continue

                doc = {
                    'video_title': v['title'],
                    'video_url': video_url,                    # [REKOMENDASI 2: Link Video]
                    'username': comment.get('author', 'Anonim'),
                    'full_text': text,
                    'likes': int(comment.get('votes', 0)),      # [REKOMENDASI 4: Pastikan Integer]
                    'waktu_youtube': comment.get('time', ''),
                    'crawled_at': datetime.now(),               # [REKOMENDASI 3: Timestamp untuk Tren]
                    'status_analisis': 'belum'
                }

                # Simpan ke MongoDB dengan sistem Upsert (Hanya masukkan jika unik)
                hasil = collection.update_one(
                    {
                        'username': doc['username'],
                        'full_text': doc['full_text']
                    },
                    {'$setOnInsert': doc},
                    upsert=True
                )

                if hasil.upserted_id is not None:
                    data_baru_masuk += 1

                count += 1
                if count >= komentar_per_video:
                    break
        except Exception as e:
            print(f"Gagal memproses video {v['title']}: {e}")
            pass

    total_data = collection.count_documents({})
    print(f"✅ Crawling Selesai! Ada {data_baru_masuk} komentar baru.")
    print(f"📊 Total di database: {total_data} baris.")

# Jalankan sekali saat start
jalankan_crawler()

# Schedule setiap 6 jam
schedule.every(6).hours.do(jalankan_crawler)

while True:
    schedule.run_pending()
    time.sleep(1)