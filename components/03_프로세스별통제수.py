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
# ------------------------------------------------------------------
control_df = pd.read_csv(os.path.join(RAW_DIR, "ic_control_master.csv"))

control_counts = control_df.groupby("프로세스명").size()

# 건수가 많은 순으로 정렬
control_counts = control_counts.sort_values(ascending=False)

print("프로세스별 통제 수:")
print(control_counts)

# ------------------------------------------------------------------
# 시각화: 세로 막대그래프
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 7))

bars = ax.bar(
    control_counts.index,
    control_counts.values,
    color="#4C72B0",
)

ax.set_title("프로세스별 통제 수 현황", fontsize=15, pad=15)
ax.set_xlabel("프로세스명", fontsize=12)
ax.set_ylabel("통제 수", fontsize=12)
ax.set_xticks(range(len(control_counts.index)))
ax.set_xticklabels(control_counts.index, rotation=45, ha="right")
ax.grid(axis="y", linestyle="--", alpha=0.3)

# 막대 위 숫자가 잘리지 않도록 y축 여유 공간 확보
max_value = control_counts.values.max()
ax.set_ylim(0, max_value * 1.15)

for bar, value in zip(bars, control_counts.values):
    ax.annotate(
        f"{int(value)}",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=11,
    )

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "03_프로세스별통제수.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"이미지 저장 완료: {output_path}")
