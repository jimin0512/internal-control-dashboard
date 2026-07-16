import os

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# 한글 폰트 및 마이너스 기호 설정 (Windows)
mpl.rcParams["font.family"] = "Malgun Gothic"
mpl.rcParams["axes.unicode_minus"] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# 데이터 로드 (raw CSV를 매번 새로 읽어서 계산한다)
# ------------------------------------------------------------------
control_df = pd.read_csv(os.path.join(RAW_DIR, "ic_control_master.csv"))
operating_df = pd.read_csv(os.path.join(RAW_DIR, "ic_operating_assessment.csv"))

# ------------------------------------------------------------------
# 데이터 연결: 통제ID 기준으로 조인
# ------------------------------------------------------------------
before_rows = len(operating_df)

merged_df = operating_df.merge(
    control_df[["통제ID", "프로세스명"]], on="통제ID", how="left"
)

after_rows = len(merged_df)

print(f"조인 전 운영평가 행 수: {before_rows}")
print(f"조인 후 행 수: {after_rows}")
if after_rows != before_rows:
    raise ValueError(
        "조인 후 행 수가 조인 전과 달라졌습니다. "
        "통제ID 중복 등을 확인해야 합니다. "
        f"(전: {before_rows}, 후: {after_rows})"
    )
else:
    print("조인 전후 행 수가 동일함을 확인했습니다 (행 증식 없음).")

missing_process = merged_df["프로세스명"].isna().sum()
if missing_process > 0:
    print(f"경고: 프로세스명이 매칭되지 않은 행이 {missing_process}건 있습니다.")

# ------------------------------------------------------------------
# 운영평가결과 고유값 확인
# ------------------------------------------------------------------
unique_results = merged_df["운영평가결과"].unique().tolist()
print("운영평가결과 컬럼 고유값:", unique_results)

merged_df["is_ok"] = merged_df["운영평가결과"] == "적정"

# ------------------------------------------------------------------
# 프로세스별 계산: 전체 건수 / 적정 건수 / 미흡 건수 / 운영 적정률
# ------------------------------------------------------------------
summary = merged_df.groupby("프로세스명").agg(
    전체건수=("운영평가결과", "size"),
    적정건수=("is_ok", "sum"),
)
summary["미흡건수"] = summary["전체건수"] - summary["적정건수"]
summary["운영적정률"] = summary["적정건수"] / summary["전체건수"] * 100

# 전체 운영 적정률
overall_total = len(merged_df)
overall_ok = int(merged_df["is_ok"].sum())
overall_ratio = overall_ok / overall_total * 100

print(f"\n전체 운영 적정률: {overall_ratio:.1f}% ({overall_ok}건 / {overall_total}건)")
print("\n프로세스별 운영 적정률:")
print(summary.sort_values("운영적정률"))

# 운영 적정률이 낮은 순서로 정렬 (왼쪽부터)
summary = summary.sort_values("운영적정률", ascending=True)

lowest_two = summary.index[:2].tolist()
print(f"\n운영 적정률이 가장 낮은 두 프로세스: {lowest_two}")

# ------------------------------------------------------------------
# 시각화: 프로세스별 운영 적정률 세로 막대그래프
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(15, 8))

highlight_color = "#C44E52"
neutral_color = "#B0B0B0"
colors = [
    highlight_color if proc in lowest_two else neutral_color
    for proc in summary.index
]

bars = ax.bar(summary.index, summary["운영적정률"], color=colors, edgecolor="white")

# 전체 평균선 (점선)
ax.axhline(
    overall_ratio,
    color="black",
    linestyle="--",
    linewidth=1.8,
    label=f"전체 운영 적정률 {overall_ratio:.1f}%",
)

ax.set_title("프로세스별 운영평가 적정률 진단", fontsize=17, pad=18)
ax.set_xlabel("프로세스", fontsize=13)
ax.set_ylabel("운영 적정률(%)", fontsize=13)

# y축 범위: 0을 기준으로 하여 실제 값 차이가 왜곡되지 않도록 하고,
# 막대 위 라벨(비율/건수)이 잘리지 않도록 위쪽 여유 공간을 둔다.
ax.set_ylim(0, 100 + 15)
ax.set_yticks(range(0, 101, 10))

ax.set_xticks(range(len(summary.index)))
ax.set_xticklabels(summary.index, rotation=40, ha="right")

ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.legend(loc="upper right", fontsize=12)

for bar, ratio, count in zip(bars, summary["운영적정률"], summary["전체건수"]):
    x = bar.get_x() + bar.get_width() / 2
    top = bar.get_height()
    # 운영 적정률 (소수점 첫째 자리)
    ax.annotate(
        f"{ratio:.1f}%",
        xy=(x, top),
        xytext=(0, 18),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )
    # 전체 평가 건수 (작게 표시)
    ax.annotate(
        f"n={int(count)}건",
        xy=(x, top),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
        color="dimgray",
    )

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "10_process_operating_diagnosis.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"\n이미지 저장 완료: {output_path}")
