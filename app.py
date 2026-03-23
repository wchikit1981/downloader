import streamlit as st
import yt_dlp
import os
import glob
import time

# 1. 頁面配置 (設定標題與 Icon)
st.set_page_config(page_title="YouTube Pro Downloader", page_icon="🎬", layout="wide")

# 修正後的 CSS 注入 (解決之前的 TypeError)
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        height: 3.5em; 
        background-color: #1DB954; 
        color: white; 
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1ed760;
        border: none;
    }
    .stTextInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True) # <-- 這裡已修正為正確的參數名

st.title("🎬 YouTube 專業影音下載器")
st.write("支援最高音質 320k MP3 與 4K/HD MP4 下載 (已優化防封鎖機制)")

# --- 2. 側邊欄：Cookie 與權限設定 ---
with st.sidebar:
    st.header("🔑 權限設定")
    st.markdown("如果遇到 **403 Forbidden** 或 **Sign in to confirm**，請貼上 Netscape 格式的 Cookie。")
    
    cookie_content = st.text_area(
        "貼上 Cookie 內容:", 
        height=300, 
        placeholder="# Netscape HTTP Cookie File\n..."
    )
    
    cookie_path = None
    if cookie_content.strip():
        cookie_path = "session_cookies.txt"
        with open(cookie_path, "w", encoding='utf-8') as f:
            f.write(cookie_content)
        st.success("✅ Cookie 已成功載入")
    
    st.divider()
    st.caption("建議使用 'Get cookies.txt LOCALLY' 外掛導出內容。")

# --- 3. 主介面：網址與格式設定 ---
url = st.text_input("🔗 影片或播放清單網址:", placeholder="https://www.youtube.com/watch?v=...")

col_range, col_format = st.columns(2)
with col_range:
    range_sel = st.selectbox("下載範圍:", ["僅下載此影片 (單片)", "下載整張播放清單"])
with col_format:
    mode_sel = st.radio("輸出格式:", ["最高音質 MP3", "最高畫質 MP4"], horizontal=True)

# --- 4. 步驟一：獲取影片資訊 ---
if st.button("🔍 步驟 1：獲取影片資訊"):
    if not url:
        st.error("請先貼上網址！")
    else:
        with st.spinner("正在偽裝請求並解析數據..."):
            try:
                # 建立偽裝標頭防止 403
                target_fmt = 'bestaudio/best' if "MP3" in mode_sel else 'bestvideo+bestaudio/best'
                common_opts = {
                    'quiet': True,
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                    'noplaylist': True if "單片" in range_sel else False,
                    'format': target_fmt,
                }
                if cookie_path:
                    common_opts['cookiefile'] = cookie_path

                with yt_dlp.YoutubeDL(common_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['info'] = info
                    st.session_state['url'] = url
                    
                    # 顯示資訊卡片
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            st.image(info.get('thumbnail'), use_container_width=True)
                        with c2:
                            st.subheader(info.get('title'))
                            st.write(f"📺 頻道: {info.get('uploader')}")
                            st.write(f"⏰ 時長: {info.get('duration', 0)//60}分{info.get('duration', 0)%60}秒")
                            
                            # 大小計算
                            size = info.get('filesize') or info.get('filesize_approx') or 0
                            if size > 0:
                                st.metric("預估大小", f"{size/(1024*1024):.2f} MB")
                            else:
                                st.info("📦 大小無法預估 (通常為動態碼率)")
            except Exception as e:
                st.error(f"解析出錯！這通常是因為 YouTube 封鎖了伺服器 IP。\n請嘗試在左側貼上有效的 Cookie。\n錯誤訊息: {str(e)}")

# --- 5. 步驟二：執行下載與轉檔 ---
if st.session_state.get('info'):
    if st.button("🚀 步驟 2：開始下載並轉檔到伺服器"):
        with st.spinner("伺服器轉檔中，請勿關閉網頁..."):
            try:
                # 清除舊的暫存
                for f in glob.glob("dl_file.*"): 
                    try: os.remove(f)
                    except: pass
                
                output_name = "dl_file"
                ydl_opts = {
                    'outtmpl': f'{output_name}.%(ext)s',
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'referer': 'https://www.google.com/',
                    'noplaylist': True if "單片" in range_sel else False,
                }
                if cookie_path:
                    ydl_opts['cookiefile'] = cookie_path

                if "MP3" in mode_sel:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '0'
                        }]
                    })
                    final_ext = "mp3"
                else:
                    ydl_opts.update({
                        'format': 'bestvideo+bestaudio/best',
                        'merge_output_format': 'mp4'
                    })
                    final_ext = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([st.session_state['url']])
                
                # 下載成功後提供按鈕給用戶
                target_file = f"{output_name}.{final_ext}"
                if os.path.exists(target_file):
                    with open(target_file, "rb") as file:
                        st.balloons()
                        st.download_button(
                            label="📥 轉檔成功！點擊此處下載到你的裝置",
                            data=file,
                            file_name=f"{st.session_state['info'].get('title')}.{final_ext}",
                            mime="audio/mpeg" if final_ext == "mp3" else "video/mp4"
                        )
                else:
                    st.error("檔案處理成功但找不到路徑，請重新嘗試。")
            except Exception as e:
                st.error(f"下載失敗: {str(e)}")