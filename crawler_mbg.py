import os
import time
import schedule
import subprocess
import pandas as pd
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_RECENT

# --- KONFIGURASI ---
keyword = "Makan Bergizi Gratis"
jumlah_video = 15
komentar_per_video = 50
file_name = 'data_mbg_yt_final.csv'

def jalankan_crawler():
    all_data = []
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Memulai Crawling: '{keyword}' ---")

    # 1. Cari Video ID secara otomatis menggunakan yt-dlp
    print("Sedang mencari di YouTube, mohon tunggu sebentar...")
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

    # 2. Ambil Komentar dari tiap video (DENGAN TAMBAHAN KOLOM)
    downloader = YoutubeCommentDownloader()

    for v in video_list:
        try:
            url = f"https://www.youtube.com/watch?v={v['id']}"
            comments = downloader.get_comments_from_url(url, sort_by=SORT_BY_RECENT)

            count = 0
            for comment in comments:
                # --- BAGIAN YANG DIUBAH: MENAMBAHKAN LIKES & INFO LAIN ---
                all_data.append({
                    'video_title': v['title'],
                    'username': comment.get('author', 'Anonim'), # Nama Akun
                    'full_text': comment.get('text', ''),        # Isi Komentar
                    'likes': comment.get('votes', 0),            # Jumlah Like (Votes)
                    'waktu': comment.get('time', '')             # Kapan dikomentari
                })
                count += 1
                if count >= komentar_per_video:
                    break
        except Exception:
            pass

    # 3. Simpan dan Gabungkan ke CSV (Anti Duplikat)
    if all_data:
        df_new = pd.DataFrame(all_data)
        
        if os.path.exists(file_name):
            df_old = pd.read_csv(file_name)
            df_combined = pd.concat([df_old, df_new])
            df_combined.drop_duplicates(subset=['video_title', 'full_text'], keep='first', inplace=True)
            df_combined.to_csv(file_name, index=False)
            print(f"✅ Update berhasil! Total data saat ini: {len(df_combined)} baris.")
        else:
            df_new.to_csv(file_name, index=False)
            print(f"✅ File baru dibuat! Total data: {len(df_new)} baris.")
    else:
        print("Zonk! Tidak ada komentar baru.")
        
    print("Menunggu jadwal eksekusi berikutnya...")

# --- PENGATURAN JADWAL ---
jalankan_crawler()

schedule.every(6).hours.do(jalankan_crawler)

while True:
    schedule.run_pending()
    time.sleep(1)