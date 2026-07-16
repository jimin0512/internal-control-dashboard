from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="내부회계관리 Dashboard",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"

RAW_FILES = {
    "process": "ic_process_master.csv",
    "control": "ic_control_master.csv",
    "design": "ic_design_assessment.csv",
    "operating": "ic_operating_assessment.csv",
    "deficiency": "ic_deficiency.csv",
    "remediation": "ic_remediation.csv",
}


def safe_rate(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator * 100


@st.cache_data
def load_data():
    data = {}
    for key, filename in RAW_FILES.items():
        path = RAW_DIR / filename
        if not path.exists():
            st.warning(f"원본 파일을 찾을 수 없습니다: {filename}")
            data[key] = pd.DataFrame()
            continue
        data[key] = pd.read_csv(path)
    return data


def require_columns(df: pd.DataFrame, columns: list, label: str) -> bool:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        st.warning(f"'{label}' 데이터에 필요한 컬럼이 없어 해당 항목을 건너뜁니다: {missing}")
        return False
    return True


data = load_data()
process_df = data["process"]
control_df = data["control"]
design_df = data["design"]
operating_df = data["operating"]
deficiency_df = data["deficiency"]
remediation_df = data["remediation"]

# ---------------------------------------------------------------------------
# 사이드바 - 조회 조건
# ---------------------------------------------------------------------------
st.sidebar.title("조회 조건")

if require_columns(process_df, ["프로세스명"], "프로세스 마스터"):
    all_processes = sorted(process_df["프로세스명"].dropna().unique().tolist())
else:
    all_processes = sorted(control_df["프로세스명"].dropna().unique().tolist()) if "프로세스명" in control_df.columns else []

selected_processes = st.sidebar.multiselect(
    "프로세스 선택",
    options=all_processes,
    default=all_processes,
)

if not selected_processes:
    selected_processes = all_processes

filtered_control = control_df[control_df["프로세스명"].isin(selected_processes)].copy() if "프로세스명" in control_df.columns else control_df.copy()
filtered_control_ids = set(filtered_control["통제ID"]) if "통제ID" in filtered_control.columns else set()

filtered_design = design_df[design_df["통제ID"].isin(filtered_control_ids)].copy() if "통제ID" in design_df.columns else design_df.copy()
filtered_operating = operating_df[operating_df["통제ID"].isin(filtered_control_ids)].copy() if "통제ID" in operating_df.columns else operating_df.copy()
filtered_deficiency = deficiency_df[deficiency_df["통제ID"].isin(filtered_control_ids)].copy() if "통제ID" in deficiency_df.columns else deficiency_df.copy()
filtered_remediation = remediation_df[remediation_df["통제ID"].isin(filtered_control_ids)].copy() if "통제ID" in remediation_df.columns else remediation_df.copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    "전체 데이터 건수  \n"
    f"프로세스 {len(process_df)}건 · 통제 {len(control_df)}건  \n"
    f"설계평가 {len(design_df)}건 · 운영평가 {len(operating_df)}건  \n"
    f"미비점 {len(deficiency_df)}건 · 개선조치 {len(remediation_df)}건"
)
if "평가기준일" in operating_df.columns and not operating_df.empty:
    try:
        base_date = pd.to_datetime(operating_df["평가기준일"], errors="coerce").max()
        if pd.notna(base_date):
            st.sidebar.caption(f"데이터 기준일: {base_date.date()}")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# 헤더
# ---------------------------------------------------------------------------
st.title("내부회계관리 Dashboard")
st.caption("설계평가·운영평가·미비점·개선조치 현황을 통합한 내부회계관리제도 분석 대시보드")

# ---------------------------------------------------------------------------
# KPI 카드
# ---------------------------------------------------------------------------
design_total = len(filtered_design)
design_ok = int((filtered_design["설계평가결과"] == "적정").sum()) if "설계평가결과" in filtered_design.columns else 0
design_rate = safe_rate(design_ok, design_total)

operating_total = len(filtered_operating)
operating_ok = int((filtered_operating["운영평가결과"] == "적정").sum()) if "운영평가결과" in filtered_operating.columns else 0
operating_rate = safe_rate(operating_ok, operating_total)

deficiency_total = len(filtered_deficiency)
deficiency_rate = safe_rate(deficiency_total, operating_total)

remediation_total = len(filtered_remediation)
remediation_done = int((filtered_remediation["진행상태"] == "완료").sum()) if "진행상태" in filtered_remediation.columns else 0
remediation_rate = safe_rate(remediation_done, remediation_total)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("설계 적정률", f"{design_rate:.1f}%", f"{design_ok} / {design_total}건")
kpi2.metric("운영 적정률", f"{operating_rate:.1f}%", f"{operating_ok} / {operating_total}건")
kpi3.metric("미비점 발생률", f"{deficiency_rate:.1f}%", f"{deficiency_total} / {operating_total}건")
kpi4.metric("개선 완료율", f"{remediation_rate:.1f}%", f"{remediation_done} / {remediation_total}건")

st.markdown("---")

# ---------------------------------------------------------------------------
# 프로세스별 집계표 (여러 차트 및 AI Insight에서 공용으로 사용)
# ---------------------------------------------------------------------------
proc_stats = pd.DataFrame({"프로세스명": selected_processes})

if not filtered_control.empty and require_columns(filtered_control, ["프로세스명", "Key여부"], "통제 마스터"):
    ctrl_agg = filtered_control.groupby("프로세스명").agg(
        통제수=("통제ID", "count"),
        key수=("Key여부", lambda s: (s == "Y").sum()),
    ).reset_index()
    proc_stats = proc_stats.merge(ctrl_agg, on="프로세스명", how="left")
else:
    proc_stats["통제수"] = 0
    proc_stats["key수"] = 0

proc_stats["통제수"] = proc_stats["통제수"].fillna(0)
proc_stats["key수"] = proc_stats["key수"].fillna(0)
proc_stats["key비율"] = proc_stats.apply(lambda r: safe_rate(r["key수"], r["통제수"]), axis=1)

if not filtered_operating.empty and require_columns(filtered_operating, ["통제ID", "운영평가결과"], "운영평가") and "프로세스명" in filtered_control.columns:
    op_with_proc = filtered_operating.merge(
        filtered_control[["통제ID", "프로세스명"]], on="통제ID", how="left"
    )
    op_agg = op_with_proc.groupby("프로세스명").agg(
        전체건수=("운영평가ID", "count"),
        적정건수=("운영평가결과", lambda s: (s == "적정").sum()),
    ).reset_index()
    proc_stats = proc_stats.merge(op_agg, on="프로세스명", how="left")
else:
    proc_stats["전체건수"] = 0
    proc_stats["적정건수"] = 0

proc_stats["전체건수"] = proc_stats["전체건수"].fillna(0)
proc_stats["적정건수"] = proc_stats["적정건수"].fillna(0)
proc_stats["미흡건수"] = proc_stats["전체건수"] - proc_stats["적정건수"]
proc_stats["운영적정률"] = proc_stats.apply(lambda r: safe_rate(r["적정건수"], r["전체건수"]), axis=1)

if not filtered_deficiency.empty and "프로세스명" in filtered_deficiency.columns:
    def_agg = filtered_deficiency.groupby("프로세스명").agg(미비점건수=("미비점ID", "count")).reset_index()
    proc_stats = proc_stats.merge(def_agg, on="프로세스명", how="left")
else:
    proc_stats["미비점건수"] = 0

proc_stats["미비점건수"] = proc_stats["미비점건수"].fillna(0)
proc_stats["미비점발생률"] = proc_stats.apply(lambda r: safe_rate(r["미비점건수"], r["전체건수"]), axis=1)

# ---------------------------------------------------------------------------
# 섹션 1. 통제 구성 현황
# ---------------------------------------------------------------------------
st.header("통제 구성 현황")
col1, col2 = st.columns(2)

with col1:
    st.subheader("프로세스별 통제 수")
    chart1_df = proc_stats.sort_values("통제수", ascending=False)
    if chart1_df["통제수"].sum() > 0:
        melt1 = chart1_df.melt(
            id_vars="프로세스명", value_vars=["통제수", "key수"],
            var_name="구분", value_name="건수",
        )
        melt1["구분"] = melt1["구분"].map({"통제수": "전체 통제 수", "key수": "Key 통제 수"})
        fig1 = px.bar(
            melt1, x="프로세스명", y="건수", color="구분", barmode="group",
            category_orders={"프로세스명": chart1_df["프로세스명"].tolist()},
        )
        fig1.update_traces(
            hovertemplate="프로세스: %{x}<br>구분: %{fullData.name}<br>건수: %{y}건<extra></extra>"
        )
        fig1.update_layout(legend_title_text="")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("표시할 통제 데이터가 없습니다.")

with col2:
    st.subheader("Key / Non-Key 통제 비율")
    if "Key여부" in filtered_control.columns and len(filtered_control) > 0:
        key_counts = filtered_control["Key여부"].value_counts()
        y_cnt = int(key_counts.get("Y", 0))
        n_cnt = int(key_counts.get("N", 0))
        fig2 = go.Figure(data=[go.Pie(
            labels=["Key 통제", "Non-Key 통제"],
            values=[y_cnt, n_cnt],
            hole=0.5,
        )])
        fig2.update_traces(
            hovertemplate="%{label}<br>건수: %{value}건<br>비율: %{percent}<extra></extra>"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("표시할 통제 데이터가 없습니다.")

st.subheader("관련주장별 통제 분포")
if require_columns(filtered_control, ["관련주장"], "통제 마스터") and len(filtered_control) > 0:
    d7 = filtered_control["관련주장"].value_counts().reset_index()
    d7.columns = ["관련주장", "건수"]
    total7 = d7["건수"].sum()
    d7["비율"] = d7["건수"] / total7 * 100 if total7 else 0
    d7 = d7.sort_values("건수", ascending=True)
    fig7 = px.bar(d7, x="건수", y="관련주장", orientation="h", custom_data=["비율"])
    fig7.update_traces(
        hovertemplate="관련주장: %{y}<br>건수: %{x}건<br>비율: %{customdata[0]:.1f}%<extra></extra>"
    )
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.info("표시할 통제 데이터가 없습니다.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 섹션 2. 설계 및 운영평가
# ---------------------------------------------------------------------------
st.header("설계 및 운영평가")
col3, col4 = st.columns(2)

with col3:
    st.subheader("설계평가 결과")
    if require_columns(filtered_design, ["설계평가결과"], "설계평가") and len(filtered_design) > 0:
        order3 = ["적정", "개선필요", "미적용"]
        d3 = filtered_design["설계평가결과"].value_counts().reindex(order3).fillna(0).reset_index()
        d3.columns = ["설계평가결과", "건수"]
        total3 = d3["건수"].sum()
        d3["비율"] = d3["건수"] / total3 * 100 if total3 else 0
        fig3 = px.bar(d3, x="설계평가결과", y="건수", custom_data=["비율"])
        fig3.update_traces(
            hovertemplate="결과: %{x}<br>건수: %{y}건<br>비율: %{customdata[0]:.1f}%<extra></extra>"
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("표시할 설계평가 데이터가 없습니다.")

with col4:
    st.subheader("운영평가 결과")
    if require_columns(filtered_operating, ["운영평가결과"], "운영평가") and len(filtered_operating) > 0:
        order4 = ["적정", "미흡"]
        d4 = filtered_operating["운영평가결과"].value_counts().reindex(order4).fillna(0).reset_index()
        d4.columns = ["운영평가결과", "건수"]
        fig4 = go.Figure(data=[go.Pie(
            labels=d4["운영평가결과"], values=d4["건수"], hole=0.5,
        )])
        fig4.update_traces(
            hovertemplate="%{label}<br>건수: %{value}건<br>비율: %{percent}<extra></extra>"
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("표시할 운영평가 데이터가 없습니다.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 섹션 3. 미비점 및 개선조치
# ---------------------------------------------------------------------------
st.header("미비점 및 개선조치")
col5, col6 = st.columns(2)

with col5:
    st.subheader("미비점 유형 분포")
    if require_columns(filtered_deficiency, ["미비점유형"], "미비점") and len(filtered_deficiency) > 0:
        d5 = filtered_deficiency["미비점유형"].value_counts().reset_index()
        d5.columns = ["미비점유형", "건수"]
        total5 = d5["건수"].sum()
        d5["비율"] = d5["건수"] / total5 * 100 if total5 else 0
        d5 = d5.sort_values("건수", ascending=True)
        fig5 = px.bar(d5, x="건수", y="미비점유형", orientation="h", custom_data=["비율"])
        fig5.update_traces(
            hovertemplate="유형: %{y}<br>건수: %{x}건<br>비율: %{customdata[0]:.1f}%<extra></extra>"
        )
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("표시할 미비점 데이터가 없습니다.")

with col6:
    st.subheader("개선조치 진행상태")
    if require_columns(filtered_remediation, ["진행상태"], "개선조치") and len(filtered_remediation) > 0:
        d6 = filtered_remediation["진행상태"].value_counts().reset_index()
        d6.columns = ["진행상태", "건수"]
        fig6 = go.Figure(data=[go.Pie(
            labels=d6["진행상태"], values=d6["건수"], hole=0.5,
        )])
        fig6.update_traces(
            hovertemplate="%{label}<br>건수: %{value}건<br>비율: %{percent}<extra></extra>"
        )
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.info("표시할 개선조치 데이터가 없습니다.")

st.markdown("---")

# ---------------------------------------------------------------------------
# 섹션 4. 프로세스 위험 진단
# ---------------------------------------------------------------------------
st.header("프로세스 위험 진단")
col8, col9 = st.columns(2)

with col8:
    st.subheader("프로세스별 운영평가 적정률 진단")
    diag_df = proc_stats[proc_stats["전체건수"] > 0].sort_values("운영적정률", ascending=True)
    if len(diag_df) > 0:
        fig8 = px.bar(
            diag_df, x="프로세스명", y="운영적정률",
            category_orders={"프로세스명": diag_df["프로세스명"].tolist()},
            custom_data=["전체건수", "적정건수", "미흡건수"],
        )
        fig8.update_traces(
            hovertemplate=(
                "프로세스: %{x}<br>운영 적정률: %{y:.1f}%<br>"
                "전체 평가 건수: %{customdata[0]}건<br>적정 건수: %{customdata[1]}건<br>"
                "미흡 건수: %{customdata[2]}건<extra></extra>"
            )
        )
        fig8.add_hline(
            y=operating_rate, line_dash="dash", line_color="red",
            annotation_text=f"전체 운영 적정률 {operating_rate:.1f}%",
            annotation_position="top left",
        )
        fig8.update_yaxes(title_text="운영 적정률 (%)")
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.info("표시할 운영평가 데이터가 없습니다.")

with col9:
    st.subheader("프로세스별 Key 통제 비율 · 미비점 발생률")
    combo_df = proc_stats[proc_stats["통제수"] > 0].sort_values("통제수", ascending=False)
    if len(combo_df) > 0:
        fig9 = make_subplots(specs=[[{"secondary_y": True}]])
        fig9.add_trace(
            go.Bar(
                x=combo_df["프로세스명"], y=combo_df["key비율"], name="Key 통제 비율(%)",
                hovertemplate="프로세스: %{x}<br>Key 통제 비율: %{y:.1f}%<extra></extra>",
            ),
            secondary_y=False,
        )
        fig9.add_trace(
            go.Scatter(
                x=combo_df["프로세스명"], y=combo_df["미비점발생률"], name="미비점 발생률(%)",
                mode="lines+markers",
                hovertemplate="프로세스: %{x}<br>미비점 발생률: %{y:.1f}%<extra></extra>",
            ),
            secondary_y=True,
        )
        fig9.update_yaxes(title_text="Key 통제 비율(%)", secondary_y=False)
        fig9.update_yaxes(title_text="미비점 발생률(%)", secondary_y=True)
        st.plotly_chart(fig9, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다.")

st.markdown("---")

# ---------------------------------------------------------------------------
# AI Insight
# ---------------------------------------------------------------------------
st.header("🤖 AI Insight")
st.caption("외부 AI API를 사용하지 않고, 현재 필터링된 데이터를 기준으로 자동 계산된 인사이트입니다.")

valid_proc = proc_stats[proc_stats["전체건수"] > 0].copy()

if valid_proc.empty:
    st.info("선택된 조건에 해당하는 운영평가 데이터가 없어 인사이트를 계산할 수 없습니다.")
else:
    worst = valid_proc.loc[valid_proc["운영적정률"].idxmin()]
    gap = operating_rate - worst["운영적정률"]
    st.warning(
        f"**운영 적정률 최저 프로세스**: {worst['프로세스명']} "
        f"({worst['운영적정률']:.1f}%, {int(worst['적정건수'])}/{int(worst['전체건수'])}건) "
        f"— 전체 운영 적정률({operating_rate:.1f}%)보다 {gap:.1f}%p 낮습니다."
    )

    if valid_proc["미비점건수"].sum() > 0:
        most_def = valid_proc.loc[valid_proc["미비점건수"].idxmax()]
        st.warning(
            f"**미비점 최다 발생 프로세스**: {most_def['프로세스명']} "
            f"(미비점 {int(most_def['미비점건수'])}건, 발생률 {most_def['미비점발생률']:.1f}%)"
        )
    else:
        st.info("선택된 조건에서 발견된 미비점이 없습니다.")

    incomplete = remediation_total - remediation_done
    st.info(
        f"**개선조치 완료율**: {remediation_rate:.1f}% ({remediation_done} / {remediation_total}건) "
        f"— 미완료 또는 진행 중 {incomplete}건이 남아 있습니다."
    )

    candidates = valid_proc[(valid_proc["미비점발생률"] > 0) | (valid_proc["운영적정률"] < operating_rate)]
    if len(candidates) > 0:
        candidates = candidates.sort_values(["미비점발생률", "운영적정률"], ascending=[False, True])
        top_priority = candidates.iloc[0]
        st.warning(
            f"**우선 점검 프로세스**: {top_priority['프로세스명']} "
            f"(Key 통제 비율 {top_priority['key비율']:.1f}%, 미비점 발생률 {top_priority['미비점발생률']:.1f}%, "
            f"운영 적정률 {top_priority['운영적정률']:.1f}%) — 미비점 발생률이 높거나 운영 적정률이 전체 평균보다 낮은 것으로 확인됩니다."
        )
    else:
        top_priority = None
        st.info("전체 평균 대비 특별히 우선 점검이 필요한 프로세스는 확인되지 않았습니다.")

    st.success(
        f"**경영진 보고용 요약**: 운영 적정률이 가장 낮은 {worst['프로세스명']} 프로세스"
        f"({worst['운영적정률']:.1f}%)와 미완료 개선조치 {incomplete}건을 우선 관리할 필요가 있습니다."
    )
