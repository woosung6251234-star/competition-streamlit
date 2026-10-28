import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re

st.set_page_config(layout="wide", page_title="유튜브 경쟁 영상 분석기")

# API 키는 스트림릿 클라우드 설정(Secrets)에서 가져옵니다.
API_KEY = st.secrets["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=API_KEY)

# 폰트 경로 (Streamlit Cloud 환경의 나눔고딕)
FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def get_video_stats(video_id):
    request = youtube.videos().list(part="statistics,snippet", id=video_id)
    response = request.execute()
    if not response["items"]:
        return None
    stats = response["items"][0]["statistics"]
    snippet = response["items"][0]["snippet"]
    return {
        "title": snippet["title"],
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0))
    }

def get_comments_text(video_id):
    request = youtube.commentThreads().list(
        part="snippet", videoId=video_id, maxResults=100, order="relevance"
    )
    response = request.execute()
    text_data = ""
    for item in response.get("items", []):
        text_data += item["snippet"]["topLevelComment"]["snippet"]["textOriginal"] + " "
    return text_data

def generate_wordcloud(text):
    wc = WordCloud(font_path=FONT_PATH, background_color="white", width=400, height=300).generate(text)
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig

st.title("📊 유튜브 경쟁 영상 비교 분석 대시보드")

col1, col2 = st.columns(2)
with col1:
    url_a = st.text_input("첫 번째 영상 URL을 입력하세요.")
with col2:
    url_b = st.text_input("두 번째 영상 URL을 입력하세요.")

if st.button("비교 분석 실행") and url_a and url_b:
    id_a = get_video_id(url_a)
    id_b = get_video_id(url_b)

    stats_a = get_video_stats(id_a)
    stats_b = get_video_stats(id_b)

    if stats_a and stats_b:
        st.subheader("1. 성과 비교 (조회수 및 좋아요)")
        
        df_stats = pd.DataFrame([
            {"구분": "영상 A", "제목": stats_a["title"], "조회수": stats_a["views"], "좋아요": stats_a["likes"]},
            {"구분": "영상 B", "제목": stats_b["title"], "조회수": stats_b["views"], "좋아요": stats_b["likes"]}
        ])
        st.dataframe(df_stats, use_container_width=True)

        st.subheader("2. 시청자 반응 워드클라우드 비교")
        wc_col1, wc_col2 = st.columns(2)
        
        with wc_col1:
            st.write(f"**{stats_a['title'][:25]}...**")
            text_a = get_comments_text(id_a)
            if text_a:
                st.pyplot(generate_wordcloud(text_a))
            else:
                st.write("댓글을 가져올 수 없습니다.")

        with wc_col2:
            st.write(f"**{stats_b['title'][:25]}...**")
            text_b = get_comments_text(id_b)
            if text_b:
                st.pyplot(generate_wordcloud(text_b))
            else:
                st.write("댓글을 가져올 수 없습니다.")
