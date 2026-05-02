import time
import schedule
import subprocess
from pymongo import MongoClient
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT

# --- KONFIGURASI MONGODB ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "mbg_db"
COLLECTION_NAME = "raw_mbg"

# --- KONFIGURASI YOUTUBE ---
keyword = "Makan Bergizi Gratis"
jumlah_video = 15
komentar_per_video = 50

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def jalankan_crawler():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Memulai Crawling: '{keyword}' ---")

    cmd_list = [
        "python", "-m", "yt_dlp",
        f"ytsearch{jumlah_video}:{keyword}",
        "--get-id", "--get-title",
        "--match-filter", "!is_live"
    ]
    process = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()

    if error and not output:
        print("⚠️ YAH, ADA ERROR DARI YOUTUBE:\n", error)

    lines = output.strip().split('\n')
    video_list = []

    for i in range(0, len(lines), 2):
        if i+1 < len(lines):
            video_list.append({'title': lines[i], 'id': lines[i+1]})

    if not video_list:
        print("Video tidak ditemukan. Melewati siklus ini.")
        return

    print(f"Ditemukan {len(video_list)} video. Mulai mengambil komentar...")

    downloader = YoutubeCommentDownloader()
    data_baru_masuk = 0

    for v in video_list:
        try:
            url = f"https://www.youtube.com/watch?v={v['id']}"
            comments = downloader.get_comments_from_url(url, sort_by=SORT_BY_RECENT)

            count = 0
            for comment in comments:
                doc = {
                    'video_title': v['title'],
                    'username': comment.get('author', 'Anonim'),
                    'full_text': comment.get('text', ''),
                    'likes': comment.get('votes', 0),
                    'waktu': comment.get('time', ''),
                    'status_analisis': 'belum'
                }

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
    print(f"✅ Crawling Selesai! Ada {data_baru_masuk} komentar baru yang masuk ke MongoDB.")
    print(f"📊 Total seluruh data di database saat ini: {total_data} baris.")
    print("Menunggu jadwal eksekusi berikutnya...")

jalankan_crawler()
schedule.every(6).hours.do(jalankan_crawler)

while True:
    schedule.run_pending()
    time.sleep(1)