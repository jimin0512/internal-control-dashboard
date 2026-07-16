import os

import streamlit as st

st.set_page_config(page_title="내부회계관리 Dashboard", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "components", "output")


def image_path(filename: str) -> str:
    return os.path.join(OUTPUT_DIR, filename)


st.title("내부회계관리 Dashboard")

# 가장 위: KPI 카드 이미지
st.subheader("내부회계 핵심 KPI 스코어카드")
st.image(image_path("09_ic_kpi_scorecard.png"), use_container_width=True)

# 이하 순서대로 표시
st.subheader("프로세스별 통제 현황 및 평가차수별 운영평가 추이")
st.image(image_path("01_ic_overview.png"), use_container_width=True)

st.subheader("미비점 유형별 발생 현황")
st.image(image_path("02_미비점_유형분해.png"), use_container_width=True)

st.subheader("프로세스별 통제 수 현황")
st.image(image_path("03_프로세스별통제수.png"), use_container_width=True)

st.subheader("Key 통제 비율")
st.image(image_path("04_key_ratio.png"), use_container_width=True)

st.subheader("설계평가 결과 현황")
st.image(image_path("05_design_assessment.png"), use_container_width=True)

st.subheader("운영평가 결과 현황")
st.image(image_path("06_operating_assessment.png"), use_container_width=True)

st.subheader("개선조치 현황")
st.image(image_path("07_remediation_status.png"), use_container_width=True)

st.subheader("내부회계 핵심 KPI 스코어카드 (요약)")
st.image(image_path("09_ic_kpi_scorecard.png"), use_container_width=True)
