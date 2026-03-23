import streamlit as st
import yt_dlp
import os
import glob

# 1. 頁面配置
st.set_page_config(page_title="YouTube Ultimate Downloader", page_icon="🎵", layout="wide")

# CSS 美化介面
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #FF0000; color: white; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1DB954; color: white; font-weight: bold; }
    .info-box { padding: 20px; border-radius: 10px; border: 1px solid #444; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📺 YouTube 究極下載器 (雲端修復版)")
st.info("💡 如果出現 403 錯誤，請在側邊欄貼上最新的 Netscape Cookie。")

# --- 2. 側邊欄：Cookie 管理 ---
with st.sidebar:
    st.header("🔑 權限認證")
    st.markdown("當雲端 IP 被擋時，這是唯一的解藥。")
    cookie_data = st.text_area("在此貼上 Cookie 內容:", height=400, placeholder="# Netscape HTTP Cookie File\n...")
    
    cookie_path = None
    if cookie_data.strip():
        cookie_path = "google_cookies.txt"
        with open(cookie_path, "w", encoding='utf-8') as f:
            f.write(cookie_data)
        st.success("✅ Cookie 已備妥")
    else:
        st.caption("暫未提供 Cookie，僅能下載部分公開影片。")

# --- 3. 主畫面：功能設定 ---
url = st.text_input("🔗 YouTube 網址:", placeholder="貼上影片或播放清單網址...")
col1, col2 = st.columns(2)
with col1:
    range_mode = st.selectbox("下載模式:", ["單一影片", "整張播放清單"])
with col2:
    format_mode = st.radio("輸出格式:", ["最高音質 MP3", "最高畫質 MP4"], horizontal=True)

# --- 4. 步驟一：解析資訊 ---
if st.button("🔍 步驟 1：解析影片資訊"):
    if not url:
        st.warning("請先輸入網址")
    else:
        with st.spinner("正在穿透 YouTube 防護網..."):
            try:
                # 終極偽裝設定
                ydl_opts = {
                    'quiet': True,
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                    'noplaylist': True if "單一" in range_mode else False,
                    'extract_flat': False,
                }
                if cookie_path: ydl_opts['cookiefile'] = cookie_path

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['video_info'] = info
                    st.session_state['active_url'] = url
                    
                    # 顯示資訊卡
                    with st.container():
                        st.markdown(f"### 🎬 {info.get('title')}")
                        c1, c2, c3 = st.columns([1, 1, 1])
                        c1.image(info.get('thumbnail'), use_container_width=True)
                        c2.write(f"**上傳者:** {info.get('uploader')}")
                        c2.write(f"**時長:** {info.get('duration', 0)//60}分{info.get('duration', 0)%60}秒")
                        
                        size = info.get('filesize') or info.get('filesize_approx') or 0
                        c3.metric("預估大小", f"{size/(1024*1024):.2f} MB")
            except Exception as e:
                st.error(f"❌ 解析失敗：HTTP 403 Forbidden\n\n這代表 Streamlit 的伺服器 IP 被 YouTube 暫時封鎖了。請更新左側的 Cookie 內容再試一次。")

# --- 5. 步驟二：執行下載 ---
if st.session_state.get('video_info'):
    if st.button("🚀 步驟 2：開始轉檔下載"):
        with st.spinner("伺服器正在處理中，請稍候..."):
            try:
                # 清理舊檔
                for f in glob.glob("final_out.*"): 
                    try: os.remove(f)
                    except: pass
                
                out_base = "final_out"
                ydl_opts = {
                    'outtmpl': f'{out_base}.%(ext)s',
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                }
                if cookie_path: ydl_opts['cookiefile'] = cookie_path

                if "MP3" in format_mode:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '0'}]
                    })
                    f_ext = "mp3"
                else:
                    ydl_opts.update({'format': 'bestvideo+bestaudio/best','merge_output_format': 'mp4'})
                    f_ext = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([st.session_state['active_url']])
                
                # 提供下載按鈕
                final_path = f"{out_base}.{f_ext}"
                if os.path.exists(final_path):
                    with open(final_path, "rb") as f:
                        st.balloons()
                        st.download_button(
                            label="📥 轉檔完成！點擊儲存檔案到裝置",
                            data=f,
                            file_name=f"{st.session_state['video_info'].get('title')}.{f_ext}",
                            mime="audio/mpeg" if f_ext=="mp3" else "video/mp4"
                        )
            except Exception as e:
                st.error(f"下載失敗: {str(e)}")