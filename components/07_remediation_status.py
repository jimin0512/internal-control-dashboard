import os

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
# 데이터 로드 및 집계 (raw CSV를 매번 새로 읽어서 계산한다)
#
# 참고: raw/ic_remediation.csv에는 "개선조치상태"라는 컬럼명이 없고,
# 개선조치의 상태값은 "진행상태" 컬럼(완료/진행중/지연)에 들어 있어
# 이 컬럼을 사용한다.
# ------------------------------------------------------------------
remediation_df = pd.read_csv(os.path.join(RAW_DIR, "ic_remediation.csv"))

unique_status = remediation_df["진행상태"].unique().tolist()
print("진행상태 컬럼 고유값:", unique_status)

status_counts = (
    remediation_df.groupby("진행상태").size().sort_values(ascending=False)
)

print("개선조치상태(진행상태)별 건수:")
print(status_counts)

# ------------------------------------------------------------------
# 시각화: 세로 막대그래프
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 7))

bars = ax.bar(
    status_counts.index,
    status_counts.values,
    color="#4C72B0",
)

ax.set_title("개선조치 현황", fontsize=15, pad=15)
ax.set_xlabel("개선조치상태", fontsize=12)
ax.set_ylabel("건수", fontsize=12)
ax.set_xticks(range(len(status_counts.index)))
ax.set_xticklabels(status_counts.index)
ax.grid(axis="y", linestyle="--", alpha=0.3)

# 막대 위 숫자가 잘리지 않도록 y축 여유 공간 확보
max_value = status_counts.values.max()
ax.set_ylim(0, max_value * 1.15)

for bar, value in zip(bars, status_counts.values):
    ax.annotate(
        f"{int(value)}",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=12,
    )

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "07_remediation_status.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"이미지 저장 완료: {output_path}")
