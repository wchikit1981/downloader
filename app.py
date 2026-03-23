import streamlit as st
import yt_dlp
import os
import glob

# 1. 頁面設定
st.set_page_config(page_title="YouTube Pro Max Web", page_icon="🚀", layout="wide")

st.title("🚀 YouTube Pro Max (自備 Cookie 版)")
st.markdown("---")

# --- 2. 側邊欄：Cookie 設定 (讓用家自行輸入) ---
with st.sidebar:
    st.header("🔑 權限設定")
    st.write("若遇到『機器人驗證』或想下載『私人清單』，請提供 Netscape 格式的 Cookie。")
    
    cookie_method = st.radio("提供方式:", ["不使用 (僅限公開影片)", "上傳 .txt 檔案", "直接貼上文字內容"])
    
    user_cookies = None
    if cookie_method == "上傳 .txt 檔案":
        uploaded_file = st.file_uploader("上傳 youtube_cookies.txt", type="txt")
        if uploaded_file:
            # 存為暫存檔
            with open("temp_cookies.txt", "wb") as f:
                f.write(uploaded_file.getbuffer())
            user_cookies = "temp_cookies.txt"
            
    elif cookie_method == "直接貼上文字內容":
        cookie_text = st.text_area("在此貼上 Cookie 內容:", height=200, placeholder="# Netscape HTTP Cookie File...")
        if cookie_text:
            with open("temp_cookies.txt", "w", encoding='utf-8') as f:
                f.write(cookie_text)
            user_cookies = "temp_cookies.txt"

# --- 3. 主介面：解析與下載 ---
url = st.text_input("🔗 YouTube 網址:", placeholder="https://...")
mode = st.radio("🛠️ 格式:", ["最高音質 MP3", "最高畫質 MP4"], horizontal=True)

if st.button("🔍 獲取資訊"):
    if not url:
        st.warning("請先輸入網址")
    else:
        with st.spinner("解析中..."):
            try:
                ydl_opts = {
                    'quiet': True,
                    'nocheckcertificate': True,
                    'noplaylist': True,
                    'format': 'bestaudio/best' if "MP3" in mode else 'bestvideo+bestaudio/best'
                }
                if user_cookies: ydl_opts['cookiefile'] = user_cookies

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state['ready_info'] = info
                    st.session_state['target_url'] = url
                    
                    st.success(f"✅ 找到影片: {info.get('title')}")
                    filesize = info.get('filesize') or info.get('filesize_approx') or 0
                    st.info(f"📦 預估大小: {filesize / (1024*1024):.2f} MB")
            except Exception as e:
                st.error(f"解析失敗: {str(e)}")

# --- 4. 執行下載 ---
if st.session_state.get('ready_info'):
    if st.button("🚀 下載並存入手機/電腦"):
        with st.spinner("轉檔中，請稍候..."):
            try:
                # 清理
                for f in glob.glob("web_out.*"): os.remove(f)
                
                output_name = "web_out"
                ydl_opts = {
                    'outtmpl': f'{output_name}.%(ext)s',
                    'nocheckcertificate': True,
                }
                if user_cookies: ydl_opts['cookiefile'] = user_cookies

                if "MP3" in mode:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '0'}]
                    })
                    ext = "mp3"
                else:
                    ydl_opts.update({'format': 'bestvideo+bestaudio/best','merge_output_format': 'mp4'})
                    ext = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([st.session_state['target_url']])
                
                # 提供下載按鈕
                with open(f"{output_name}.{ext}", "rb") as f:
                    st.download_button(
                        label="📥 點擊儲存檔案",
                        data=f,
                        file_name=f"{st.session_state['ready_info'].get('title')}.{ext}",
                        mime="audio/mpeg" if ext=="mp3" else "video/mp4"
                    )
            except Exception as e:
                st.error(f"下載出錯: {e}")