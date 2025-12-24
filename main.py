# ===============================
# 🌱 극지식물 최적 EC 농도 연구 대시보드
# Streamlit Cloud / 한글 파일명 / 한글 폰트 완전 대응
# ===============================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# -------------------------------
# 기본 설정
# -------------------------------
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# -------------------------------
# 한글 폰트 깨짐 방지 (CSS)
# -------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

PLOTLY_FONT = "Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, sans-serif"

# -------------------------------
# 경로 설정
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# -------------------------------
# 유틸: 한글 파일명 NFC/NFD 안전 비교
# -------------------------------
def normalize_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)

def find_file_safe(directory: Path, target_name: str):
    target_nfc = normalize_name(target_name)
    for file in directory.iterdir():
        if normalize_name(file.name) == target_nfc:
            return file
    return None

# -------------------------------
# 데이터 로딩
# -------------------------------
@st.cache_data
def load_environment_data():
    env_data = {}
    csv_targets = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    for name in csv_targets:
        file_path = find_file_safe(DATA_DIR, name)
        if file_path is None:
            st.error(f"환경 데이터 파일을 찾을 수 없습니다: {name}")
            continue

        df = pd.read_csv(file_path)
        df["school"] = name.split("_")[0]
        env_data[df["school"].iloc[0]] = df

    return env_data

@st.cache_data
def load_growth_data():
    xlsx_name = "4개교_생육결과데이터.xlsx"
    file_path = find_file_safe(DATA_DIR, xlsx_name)

    if file_path is None:
        st.error("생육 결과 데이터 파일을 찾을 수 없습니다.")
        return {}

    xls = pd.ExcelFile(file_path)
    growth_data = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["school"] = sheet
        growth_data[sheet] = df

    return growth_data

# -------------------------------
# 데이터 불러오기
# -------------------------------
with st.spinner("📂 데이터 로딩 중..."):
    env_data = load_environment_data()
    growth_data = load_growth_data()

if not env_data or not growth_data:
    st.stop()

# -------------------------------
# EC 조건 정의
# -------------------------------
EC_MAP = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

COLOR_MAP = {
    "송도고": "#1f77b4",
    "하늘고": "#2ca02c",
    "아라고": "#ff7f0e",
    "동산고": "#d62728",
}

# -------------------------------
# 사이드바
# -------------------------------
st.sidebar.title("🏫 학교 선택")
school_option = st.sidebar.selectbox(
    "분석 대상",
    ["전체", "송도고", "하늘고", "아라고", "동산고"]
)

selected_schools = (
    list(env_data.keys()) if school_option == "전체" else [school_option]
)

# ===============================
# 메인 제목
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ===============================
# 📖 Tab 1: 실험 개요
# ===============================
with tab1:
    st.subheader("🔬 연구 배경 및 목적")
    st.write(
        """
        본 연구는 서로 다른 EC(전기전도도) 조건에서 극지식물의 생육 반응을 비교하여  
        **최적의 EC 농도**를 도출하는 것을 목표로 한다.
        """
    )

    overview_rows = []
    total_plants = 0
    for school, df in growth_data.items():
        count = len(df)
        total_plants += count
        overview_rows.append([
            school,
            EC_MAP.get(school),
            count,
            COLOR_MAP.get(school)
        ])

    overview_df = pd.DataFrame(
        overview_rows,
        columns=["학교명", "EC 목표", "개체수", "색상"]
    )

    st.subheader("🏫 학교별 EC 조건")
    st.dataframe(overview_df, use_container_width=True)

    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    weight_means = {
        school: df["생중량(g)"].mean()
        for school, df in growth_data.items()
    }
    optimal_school = max(weight_means, key=weight_means.get)
    optimal_ec = EC_MAP[optimal_school]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 개체수", f"{total_plants} 개")
    col2.metric("평균 온도", f"{avg_temp:.1f} ℃")
    col3.metric("평균 습도", f"{avg_hum:.1f} %")
    col4.metric("최적 EC", f"{optimal_ec} ({optimal_school})")

# ===============================
# 🌡️ Tab 2: 환경 데이터
# ===============================
with tab2:
    st.subheader("📊 학교별 환경 평균 비교")

    avg_rows = []
    for school in selected_schools:
        df = env_data[school]
        avg_rows.append([
            school,
            df["temperature"].mean(),
            df["humidity"].mean(),
            df["ph"].mean(),
            df["ec"].mean(),
            EC_MAP[school]
        ])

    avg_df = pd.DataFrame(
        avg_rows,
        columns=["학교", "온도", "습도", "pH", "실측 EC", "목표 EC"]
    )

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "EC 비교"]
    )

    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["온도"]), 1, 1)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["습도"]), 1, 2)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["pH"]), 2, 1)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["실측 EC"], name="실측"), 2, 2)
    fig.add_trace(go.Bar(x=avg_df["학교"], y=avg_df["목표 EC"], name="목표"), 2, 2)

    fig.update_layout(font=dict(family=PLOTLY_FONT), height=700)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("⏱️ 학교별 시계열 변화")
    for school in selected_schools:
        df = env_data[school]

        fig_ts = px.line(
            df,
            x="time",
            y=["temperature", "humidity", "ec"],
            title=f"{school} 환경 변화"
        )
        fig_ts.add_hline(y=EC_MAP[school], line_dash="dash", annotation_text="목표 EC")
        fig_ts.update_layout(font=dict(family=PLOTLY_FONT))
        st.plotly_chart(fig_ts, use_container_width=True)

    with st.expander("📥 환경 데이터 원본"):
        full_env = pd.concat(env_data.values())
        st.dataframe(full_env, use_container_width=True)

        buffer = io.BytesIO()
        full_env.to_csv(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "CSV 다운로드",
            data=buffer,
            file_name="환경데이터_전체.csv",
            mime="text/csv"
        )

# ===============================
# 📊 Tab 3: 생육 결과
# ===============================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    ec_weight = []
    for school, df in growth_data.items():
        ec_weight.append([school, EC_MAP[school], df["생중량(g)"].mean()])

    ec_df = pd.DataFrame(ec_weight, columns=["학교", "EC", "평균 생중량"])
    fig_w = px.bar(
        ec_df,
        x="EC",
        y="평균 생중량",
        color="학교",
        title="EC별 평균 생중량 비교"
    )
    fig_w.update_layout(font=dict(family=PLOTLY_FONT))
    st.plotly_chart(fig_w, use_container_width=True)

    st.subheader("📦 학교별 생중량 분포")
    all_growth = pd.concat(growth_data.values())
    fig_box = px.box(
        all_growth,
        x="school",
        y="생중량(g)",
        color="school"
    )
    fig_box.update_layout(font=dict(family=PLOTLY_FONT))
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("🔗 상관관계 분석")
    col1, col2 = st.columns(2)

    with col1:
        fig_sc1 = px.scatter(
            all_growth,
            x="잎 수(장)",
            y="생중량(g)",
            color="school"
        )
        fig_sc1.update_layout(font=dict(family=PLOTLY_FONT))
        st.plotly_chart(fig_sc1, use_container_width=True)

    with col2:
        fig_sc2 = px.scatter(
            all_growth,
            x="지상부 길이(mm)",
            y="생중량(g)",
            color="school"
        )
        fig_sc2.update_layout(font=dict(family=PLOTLY_FONT))
        st.plotly_chart(fig_sc2, use_container_width=True)

    with st.expander("📥 생육 데이터 원본"):
        st.dataframe(all_growth, use_container_width=True)

        buffer = io.BytesIO()
        all_growth.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
