import streamlit as st
import yt_dlp
import os
import glob

# 頁面設定
st.set_page_config(page_title="YouTube Pro Web", page_icon="🎬", layout="centered")

st.title("🎬 YouTube Pro Max Web")
st.markdown("---")

# 1. 輸入與設定
url = st.text_input("🔗 請輸入 YouTube 網址:", placeholder="https://www.youtube.com/watch?v=...")
mode = st.radio("🛠️ 選擇格式:", ["最高音質 MP3", "最高畫質 MP4"], horizontal=True)

# Cookie 檢查
COOKIE_FILE = 'youtube_cookies.txt'
has_cookies = os.path.exists(COOKIE_FILE)

if not has_cookies:
    st.error("⚠️ 缺少 youtube_cookies.txt，下載限制影片可能會失敗！")

# --- 步驟一：獲取資訊 ---
if st.button("🔍 獲取影片資訊"):
    if url:
        with st.spinner("正在解析影片資料..."):
            try:
                # 設定格式以便精準計算大小
                fmt = 'bestaudio/best' if "MP3" in mode else 'bestvideo+bestaudio/best'
                ydl_opts = {
                    'quiet': True,
                    'nocheckcertificate': True,
                    'format': fmt,
                }
                if has_cookies: ydl_opts['cookiefile'] = COOKIE_FILE

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    # 顯示資訊卡片
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.image(info.get('thumbnail'), use_container_width=True)
                    with col2:
                        st.subheader(info.get('title'))
                        st.write(f"👤 上傳者: {info.get('uploader')}")
                        st.write(f"⏰ 時長: {info.get('duration')//60}分{info.get('duration')%60}秒")
                        
                        filesize = info.get('filesize') or info.get('filesize_approx')
                        if filesize:
                            st.info(f"📦 預估大小: {filesize / (1024*1024):.2f} MB")
                        else:
                            st.info("📦 預估大小: 無法計算")

                    # 將資訊暫存在 session_state 供下載按鈕使用
                    st.session_state['download_ready'] = True
                    st.session_state['url'] = url
            except Exception as e:
                st.error(f"解析失敗: {e}")
    else:
        st.warning("請先輸入網址")

# --- 步驟二：執行下載 ---
if st.session_state.get('download_ready'):
    if st.button("🚀 開始轉檔並下載到裝置"):
        with st.spinner("正在下載並處理轉碼（請勿關閉網頁）..."):
            try:
                # 清理舊檔
                for f in glob.glob("temp_file.*"): os.remove(f)
                
                output_name = "temp_file"
                ydl_opts = {
                    'nocheckcertificate': True,
                    'outtmpl': f'{output_name}.%(ext)s',
                }
                if has_cookies: ydl_opts['cookiefile'] = COOKIE_FILE

                if "MP3" in mode:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '0',
                        }],
                    })
                    final_ext = "mp3"
                else:
                    ydl_opts.update({
                        'format': 'bestvideo+bestaudio/best',
                        'merge_output_format': 'mp4',
                    })
                    final_ext = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # 找出最終檔案 (因為轉檔後副檔名會變)
                final_file = f"{output_name}.{final_ext}"
                
                with open(final_file, "rb") as f:
                    st.success("✅ 轉檔完成！請點擊下方按鈕儲存：")
                    st.download_button(
                        label="💾 儲存檔案",
                        data=f,
                        file_name=f"Download_{final_ext}.{final_ext}",
                        mime=f"audio/mpeg" if final_ext == "mp3" else "video/mp4"
                    )
            except Exception as e:
                st.error(f"下載出錯: {e}")