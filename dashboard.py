import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, format_price, convert_df_to_csv

# 페이지 설정
st.set_page_config(page_title="NemoStore Pro 대시보드", layout="wide", initial_sidebar_state="expanded")

# CSS 커스텀 스타일링
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .css-1r6slb0 { border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화 (찜 목록)
if 'favorites' not in st.session_state:
    st.session_state.favorites = set()

# 데이터 로드
@st.cache_data
def get_processed_data():
    return load_data()

try:
    df = get_processed_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --- 사이드바: 고도화 필터 ---
st.sidebar.header("🗺️ NemoStore Pro")
st.sidebar.markdown("---")

# 1. 업종 필터
business_types = sorted(df['businessMiddleCodeName'].unique().tolist())
selected_business = st.sidebar.multiselect("업종 선택", options=business_types, default=business_types)

# 2. 가격 필터
st.sidebar.subheader("💰 가격 조건")
deposit_range = st.sidebar.slider("보증금 (만원)", 0, int(df['deposit'].max()), (0, int(df['deposit'].max())))
rent_range = st.sidebar.slider("월세 (만원)", 0, int(df['monthlyRent'].max()), (0, int(df['monthlyRent'].max())))

col_side1, col_side2 = st.sidebar.columns(2)
with col_side1:
    no_premium = st.checkbox("무권리만", value=False)
with col_side2:
    is_ground = st.checkbox("지상층만", value=False)

# 3. 정렬 및 검색
st.sidebar.subheader("⚙️ 정렬 및 검색")
sort_options = {
    "최신순": ("createdDateUtc", False),
    "월세 낮은순": ("monthlyRent", True),
    "보증금 낮은순": ("deposit", True),
    "면적 넓은순": ("size_pyung", False),
    "평당 가성비순": ("price_per_pyung", True)
}
selected_sort = st.sidebar.selectbox("정렬 기준", options=list(sort_options.keys()))
search_query = st.sidebar.text_input("지하철역 또는 키워드", "")

# 데이터 필터링 적용
filtered_df = df[
    (df['businessMiddleCodeName'].isin(selected_business)) &
    (df['deposit'] >= deposit_range[0]) & (df['deposit'] <= deposit_range[1]) &
    (df['monthlyRent'] >= rent_range[0]) & (df['monthlyRent'] <= rent_range[1])
]

if no_premium:
    filtered_df = filtered_df[filtered_df['premium'] == 0]
if is_ground:
    filtered_df = filtered_df[filtered_df['floor'] > 0]
if search_query:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_query, case=False, na=False) |
        filtered_df['nearSubwayStation'].str.contains(search_query, case=False, na=False)
    ]

# 정렬 적용
sort_col, ascending = sort_options[selected_sort]
filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending)

# --- 메인 영역 ---
st.title("🏙️ NemoStore 매물 지능형 대시보드")

# KPI 지표 (상단 고정)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("검색 결과", f"{len(filtered_df)}건")
with kpi2:
    avg_rent = int(filtered_df['monthlyRent'].mean() if not filtered_df.empty else 0)
    st.metric("평균 월세", format_price(avg_rent))
with kpi3:
    avg_per_pyung = round(filtered_df['price_per_pyung'].mean() if not filtered_df.empty else 0, 1)
    st.metric("평균 평당월세", f"{avg_per_pyung}만")
with kpi4:
    total_fav = len(st.session_state.favorites)
    st.metric("나의 찜", f"{total_fav}건")

st.divider()

# 메인 탭 구성
tab_map, tab_analysis, tab_list, tab_fav = st.tabs(["🗺️ 매물 지도", "📊 정밀 분석", "📋 매물 목록", "⭐ 관심 매물"])

with tab_map:
    st.subheader("지역별 매물 분포")
    if not filtered_df.empty:
        # Streamlit 기본 지도 사용 (utils에서 생성한 lat, lon 활용)
        st.map(filtered_df[['lat', 'lon']])
    else:
        st.warning("표시할 매물이 없습니다.")

with tab_analysis:
    col_an1, col_an2 = st.columns(2)
    
    with col_an1:
        st.write("#### 💰 월세 분포 히스토그램")
        fig_hist = px.histogram(filtered_df, x="monthlyRent", nbins=20, 
                               labels={'monthlyRent': '월세(만원)'},
                               color_discrete_sequence=['#FF4B4B'],
                               template="plotly_white")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col_an2:
        st.write("#### 📏 평당 월세 vs 면적")
        fig_bubble = px.scatter(filtered_df, x="size_pyung", y="price_per_pyung",
                                size="monthlyRent", color="businessMiddleCodeName",
                                hover_name="title",
                                labels={'size_pyung': '면적(평)', 'price_per_pyung': '평당 월세(만)'},
                                template="plotly_white")
        st.plotly_chart(fig_bubble, use_container_width=True)

with tab_list:
    col_list_h1, col_list_h2 = st.columns([3, 1])
    with col_list_h1:
        view_mode = st.radio("보기 모드", ["리스트 뷰", "갤러리 뷰"], horizontal=True)
    with col_list_h2:
        csv_data = convert_df_to_csv(filtered_df)
        st.download_button("📥 데이터 내보내기 (CSV)", data=csv_data, file_name="nemostore_filtered.csv", mime="text/csv")
    
    if view_mode == "리스트 뷰":
        display_cols = ['title', 'businessMiddleCodeName', 'deposit', 'monthlyRent', 'premium', 'floor', 'size_pyung', 'price_per_pyung', 'nearSubwayStation']
        st.dataframe(filtered_df[display_cols], use_container_width=True)
    else:
        # 갤러리 뷰 (3열 그리드)
        if filtered_df.empty:
            st.info("조건에 맞는 매물이 없습니다.")
        else:
            rows = len(filtered_df) // 3 + 1
            for i in range(rows):
                cols = st.columns(3)
                for j in range(3):
                    idx = i * 3 + j
                    if idx < len(filtered_df):
                        item = filtered_df.iloc[idx]
                        with cols[j]:
                            with st.container(border=True):
                                if item['previewPhotoUrl']:
                                    st.image(item['previewPhotoUrl'], use_container_width=True)
                                st.write(f"**{item['title'][:15]}...**")
                                st.write(f"💵 {format_price(item['deposit'])} / {format_price(item['monthlyRent'])}")
                                st.write(f"📐 {item['size_pyung']}평 | 층: {item['floor']}")
                                # 찜 버튼
                                is_fav = item['id'] in st.session_state.favorites
                                if st.button("⭐ 찜하기" if not is_fav else "❤️ 찜됨", key=f"btn_{item['id']}"):
                                    if is_fav:
                                        st.session_state.favorites.remove(item['id'])
                                    else:
                                        st.session_state.favorites.add(item['id'])
                                    st.rerun()

with tab_fav:
    st.subheader("내가 찜한 매물")
    if not st.session_state.favorites:
        st.info("찜한 매물이 없습니다. 매물 목록에서 별 아이콘을 눌러보세요!")
    else:
        fav_df = df[df['id'].isin(st.session_state.favorites)]
        st.dataframe(fav_df[['title', 'deposit', 'monthlyRent', 'size_pyung', 'nearSubwayStation']], use_container_width=True)
        
        if st.button("🗑️ 찜 목록 비우기"):
            st.session_state.favorites = set()
            st.rerun()

# --- 하단 매물 상세 정보 (고정 선택창) ---
st.divider()
st.subheader("🔎 선택 매물 정밀 분석")
if not filtered_df.empty:
    selected_id = st.selectbox("분석할 매물을 선택하세요", options=filtered_df['id'].tolist(), 
                               format_func=lambda x: filtered_df[filtered_df['id']==x]['title'].values[0])
    detail = df[df['id'] == selected_id].iloc[0]
    
    d_col1, d_col2, d_col3 = st.columns([1, 1.5, 1])
    
    with d_col1:
        if detail['previewPhotoUrl']:
            st.image(detail['previewPhotoUrl'], use_container_width=True)
        st.markdown(f"**매물 번호:** `{detail['id']}`")
        
    with d_col2:
        st.write(f"### {detail['title']}")
        st.write(f"📍 **위치:** {detail['nearSubwayStation']}")
        st.write(f"🏢 **업종:** {detail['businessMiddleCodeName']}")
        st.write(f"📏 **면적:** {detail['size_pyung']}평 ({detail['size']}㎡)")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("보증금", format_price(detail['deposit']))
        c2.metric("월세", format_price(detail['monthlyRent']))
        c3.metric("권리금", format_price(detail['premium']))
        
    with d_col3:
        st.write("#### 📊 가성비 비교")
        # 해당 업종 평균 월세와 비교
        business_avg = df[df['businessMiddleCodeName'] == detail['businessMiddleCodeName']]['monthlyRent'].mean()
        diff = detail['monthlyRent'] - business_avg
        
        fig_gau = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = detail['monthlyRent'],
            title = {'text': "업종 평균 대비 월세"},
            gauge = {
                'axis': {'range': [0, max(business_avg * 2, detail['monthlyRent'] * 1.2)]},
                'bar': {'color': "#FF4B4B" if diff > 0 else "#28a745"},
                'steps': [
                    {'range': [0, business_avg], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': business_avg
                }
            }
        ))
        fig_gau.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gau, use_container_width=True)
        
        if diff > 0:
            st.error(f"업종 평균보다 {format_price(abs(diff))} 비쌉니다.")
        else:
            st.success(f"업종 평균보다 {format_price(abs(diff))} 저렴합니다!")

st.sidebar.markdown("---")
st.sidebar.info("NemoStore Data Dashboard v2.0 (Pro)")
