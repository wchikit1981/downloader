import streamlit as st
import yt_dlp
import os
import glob

# 1. 基本頁面設定
st.set_page_config(page_title="YouTube 下載器", page_icon="📺", layout="wide")

st.title("📺 YouTube 影音下載工具")
st.markdown("---")

# --- 2. Cookie 設定區 (側邊欄) ---
with st.sidebar:
    st.header("🔑 權限設定")
    st.info("如需下載私人影片或避開機器人驗證，請在此提供 Cookie。")
    
    cookie_input = st.text_area(
        "貼上 Netscape 格式 Cookie 內容:", 
        height=250, 
        placeholder="# Netscape HTTP Cookie File\n..."
    )
    
    cookie_path = None
    if cookie_input.strip():
        cookie_path = "youtube_cookies.txt"
        with open(cookie_path, "w", encoding='utf-8') as f:
            f.write(cookie_input)

# --- 3. 主畫面設定 ---
url = st.text_input("🔗 YouTube 網址:", placeholder="請貼上影片連結...")
format_type = st.radio("🛠️ 選擇下載格式:", ["最高音質 MP3", "最高畫質 MP4"], horizontal=True)

# --- 4. 預覽階段 ---
if st.button("🔍 獲取影片資訊"):
    if not url:
        st.warning("請先輸入網址")
    else:
        with st.spinner("正在解析影片資料..."):
            try:
                # 預設格式以便估計大小
                target_fmt = 'bestaudio/best' if "MP3" in format_type else 'bestvideo+bestaudio/best'
                ydl_opts = {
                    'quiet': True,
                    'nocheckcertificate': True,
                    'format': target_fmt
                }
                if cookie_path: ydl_opts['cookiefile'] = cookie_path

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.session_state['download_url'] = url
                    
                    # 顯示資訊介面
                    with st.container(border=True):
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(info.get('thumbnail'), use_container_width=True)
                        with col2:
                            st.subheader(info.get('title'))
                            st.write(f"👤 上傳者: {info.get('uploader')}")
                            st.write(f"⏰ 影片時長: {info.get('duration')//60}分{info.get('duration')%60}秒")
                            
                            # 大小計算
                            size = info.get('filesize') or info.get('filesize_approx') or 0
                            if size > 0:
                                st.success(f"📦 預估檔案大小: {size / (1024*1024):.2f} MB")
                            else:
                                st.info("📦 預估檔案大小: 無法預計")

            except Exception as e:
                st.error(f"解析失敗，請檢查網址或 Cookie: {str(e)}")

# --- 5. 下載與儲存階段 ---
if st.session_state.get('video_info'):
    if st.button("🚀 開始下載到裝置"):
        with st.spinner("正在下載並轉檔，請稍候..."):
            try:
                # 清除舊的暫存檔案
                for f in glob.glob("temp_video.*") + glob.glob("temp_audio.*"):
                    try: os.remove(f)
                    except: pass
                
                output_filename = "download_file"
                ydl_opts = {
                    'outtmpl': f'{output_filename}.%(ext)s',
                    'nocheckcertificate': True,
                    'noplaylist': True,
                }
                if cookie_path: ydl_opts['cookiefile'] = cookie_path

                if "MP3" in format_type:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '0'}]
                    })
                    ext = "mp3"
                else:
                    ydl_opts.update({'format': 'bestvideo+bestaudio/best','merge_output_format': 'mp4'})
                    ext = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([st.session_state['download_url']])
                
                # 最終提供檔案下載
                final_file = f"{output_filename}.{ext}"
                if os.path.exists(final_file):
                    with open(final_file, "rb") as f:
                        st.balloons()
                        st.download_button(
                            label="📥 點擊此處儲存檔案",
                            data=f,
                            file_name=f"{st.session_state['video_info'].get('title')}.{ext}",
                            mime="audio/mpeg" if ext=="mp3" else "video/mp4"
                        )
            except Exception as e:
                st.error(f"下載過程中發生錯誤: {e}")