import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="快速影音下載", layout="centered")

st.title("⚡ 免 Cookie 影音下載器")
url = st.text_input("輸入 YouTube 網址:")
mode = st.radio("格式:", ["MP3", "MP4"], horizontal=True)

if st.button("開始處理"):
    if url:
        with st.spinner("正在嘗試繞過封鎖並下載..."):
            try:
                # 這是目前最強的免 Cookie 偽裝參數
                ydl_opts = {
                    'outtmpl': 'temp_file.%(ext)s',
                    'nocheckcertificate': True,
                    'format': 'bestaudio/best' if mode == "MP3" else 'bestvideo+bestaudio/best',
                    # 關鍵：模擬不同客戶端
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios', 'android', 'web'],
                        }
                    },
                }
                
                if mode == "MP3":
                    ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '0'}]

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    ext = "mp3" if mode == "MP3" else "mp4"
                    filename = f"temp_file.{ext}"
                    
                    with open(filename, "rb") as f:
                        st.download_button("📥 點我存檔", f, file_name=f"{info['title']}.{ext}")
                
                os.remove(filename) # 下載完刪除，省空間
            except Exception as e:
                st.error(f"下載失敗。原因：{e}\n\n這代表該影片被 YouTube 強制要求登入。")