import streamlit as st
import yt_dlp
import os
import glob
import time

# 1. 頁面配置
st.set_page_config(page_title="YouTube Pro Downloader", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1DB954; color: white; }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_mode=True)

st.title("🎬 YouTube 專業影音下載器")
st.write("支援最高音質 320k MP3 與 4K MP4 下載")

# --- 2. 側邊欄：進階設定 (解決 403 關鍵) ---
with st.sidebar:
    st.header("🔑 權限與偽裝設定")
    st.warning("若遇到 403 錯誤，請務必貼上最新的 Cookie。")
    
    cookie_content = st.text_area(
        "貼上 Netscape 格式 Cookie:", 
        height=300, 
        placeholder="# Netscape HTTP Cookie File\n..."
    )
    
    cookie_path = None
    if cookie_content.strip():
        cookie_path = "session_cookies.txt"
        with open(cookie_path, "w", encoding='utf-8') as f:
            f.write(cookie_content)
        st.success("✅ Cookie 已載入")

# --- 3. 主介面：輸入區 ---
url = st.text_input("🔗 影片或播放清單網址:", placeholder="https://www.youtube.com/watch?v=...")
col_range, col_format = st.columns(2)

with col_range:
    range_sel = st.selectbox("下載範圍:", ["僅下載此影片", "下載整張播放清單"])
with col_format:
    mode_sel = st.radio("輸出格式:", ["最高音質 MP3", "最高畫質 MP4"], horizontal=True)

# --- 4. 預覽功能 ---
if st.button("🔍 步驟 1：獲取影片資訊"):
    if not url:
        st.error("請輸入網址")
    else:
        with st.spinner("正在偽裝請求並解析中..."):
            try:
                # 核心設定：偽裝成真實瀏覽器避免 403
                common_opts = {
                    'quiet': True,
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                    'noplaylist': True if "僅下載" in range_sel else False,
                }
                if cookie_path: common_opts['cookiefile'] = cookie_path

                with yt_dlp.YoutubeDL(common_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['info'] = info
                    st.session_state['url'] = url
                    
                    # 顯示卡片
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            st.image(info.get('thumbnail'), use_container_width=True)
                        with c2:
                            st.subheader(info.get('title'))
                            st.write(f"📺 頻道: {info.get('uploader')}")
                            st.write(f"⏱️ 時長: {info.get('duration')//60}分{info.get('duration')%60}秒")
                            
                            # 大小計算
                            size = info.get('filesize') or info.get('filesize_approx') or 0
                            if size > 0:
                                st.metric("預估大小", f"{size/(1024*1024):.2f} MB")
                            else:
                                st.info("📦 無法預估大小")
            except Exception as e:
                st.error(f"解析失敗 (403 錯誤通常是 Cookie 失效): \n{str(e)}")

# --- 5. 下載功能 ---
if st.session_state.get('info'):
    if st.button("🚀 步驟 2：開始下載並轉檔"):
        with st.spinner("伺服器處理中，請稍候..."):
            try:
                # 清理
                for f in glob.glob("dl_temp.*"): 
                    try: os.remove(f)
                    except: pass
                
                out_name = "dl_temp"
                ydl_opts = {
                    'outtmpl': f'{out_name}.%(ext)s',
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                }
                if cookie_path: ydl_opts['cookiefile'] = cookie_path

                if "MP3" in mode_sel:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '0'}]
                    })
                    ext = "mp3"
                else:
                    ydl_opts.update({'format': 'bestvideo+bestaudio/best','merge_output_format': 'mp4'})
                    ext = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([st.session_state['url']])
                
                final_file = f"{out_name}.{ext}"
                if os.path.exists(final_file):
                    with open(final_file, "rb") as f:
                        st.balloons()
                        st.download_button(
                            label="📥 點擊儲存檔案至手機/電腦",
                            data=f,
                            file_name=f"{st.session_state['info'].get('title')}.{ext}",
                            mime="audio/mpeg" if ext=="mp3" else "video/mp4"
                        )
            except Exception as e:
                st.error(f"下載失敗: {e}")