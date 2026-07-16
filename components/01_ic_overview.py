import os
import re

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
process_df = pd.read_csv(os.path.join(RAW_DIR, "ic_process_master.csv"))
operating_df = pd.read_csv(os.path.join(RAW_DIR, "ic_operating_assessment.csv"))

# ------------------------------------------------------------------
# ① 왼쪽 차트 데이터: 프로세스별 전체 통제 수 / Key 통제 수
# ------------------------------------------------------------------
total_by_process = control_df.groupby("프로세스명").size()
key_by_process = (
    control_df[control_df["Key여부"] == "Y"].groupby("프로세스명").size()
)

process_summary = pd.DataFrame(
    {"전체통제수": total_by_process, "Key통제수": key_by_process}
).fillna(0).astype(int)

# 전체 통제 수가 많은 순서로 정렬
process_summary = process_summary.sort_values("전체통제수", ascending=False)

# ------------------------------------------------------------------
# ② 오른쪽 차트 데이터: 평가차수별 운영평가 전체 건수 / 미흡 건수
# ------------------------------------------------------------------
unique_results = operating_df["운영평가결과"].unique().tolist()
print("운영평가결과 컬럼 고유값:", unique_results)

# 적정이 아닌 결과를 미흡으로 계산
operating_df["is_미흡"] = operating_df["운영평가결과"] != "적정"


def round_sort_key(value):
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else 0


round_order = sorted(operating_df["평가차수"].unique(), key=round_sort_key)

total_by_round = operating_df.groupby("평가차수").size().reindex(round_order)
fail_by_round = (
    operating_df.groupby("평가차수")["is_미흡"].sum().reindex(round_order).astype(int)
)

# ------------------------------------------------------------------
# 시각화: 하나의 그림, 좌우 2개 차트
# ------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

# ---- 왼쪽: 프로세스별 전체 통제 수 / Key 통제 수 (그룹 세로 막대) ----
x = np.arange(len(process_summary.index))
width = 0.35

bars_total = ax1.bar(
    x - width / 2,
    process_summary["전체통제수"],
    width,
    label="전체 통제 수",
    color="#4C72B0",
)
bars_key = ax1.bar(
    x + width / 2,
    process_summary["Key통제수"],
    width,
    label="Key 통제 수",
    color="#DD8452",
)

ax1.set_title("프로세스별 전체 통제 및 Key 통제 현황", fontsize=15, pad=15)
ax1.set_ylabel("통제 수", fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels(process_summary.index, rotation=45, ha="right")
ax1.legend()
ax1.grid(axis="y", linestyle="--", alpha=0.3)

for bars in (bars_total, bars_key):
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(
            f"{int(height)}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

# ---- 오른쪽: 평가차수별 전체 건수 / 미흡 건수 (꺾은선) ----
ax2.plot(
    round_order,
    total_by_round.values,
    marker="o",
    linewidth=2,
    label="전체 건수",
    color="#4C72B0",
)
ax2.plot(
    round_order,
    fail_by_round.values,
    marker="o",
    linewidth=2,
    label="미흡 건수",
    color="#C44E52",
)

for xi, yi in zip(round_order, total_by_round.values):
    ax2.annotate(
        f"{int(yi)}",
        (xi, yi),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
        fontsize=10,
        color="#4C72B0",
    )
for xi, yi in zip(round_order, fail_by_round.values):
    ax2.annotate(
        f"{int(yi)}",
        (xi, yi),
        textcoords="offset points",
        xytext=(0, -16),
        ha="center",
        fontsize=10,
        color="#C44E52",
    )

ax2.set_title("평가차수별 운영평가 및 미흡 건수 추이", fontsize=15, pad=15)
ax2.set_xlabel("평가차수", fontsize=12)
ax2.set_ylabel("평가 건수", fontsize=12)
ax2.legend()
ax2.grid(axis="y", linestyle="--", alpha=0.3)
ax2.set_ylim(bottom=0)

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "01_ic_overview.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"이미지 저장 완료: {output_path}")
