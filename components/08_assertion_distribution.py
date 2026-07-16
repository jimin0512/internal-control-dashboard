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

unique_assertions = control_df["관련주장"].unique().tolist()
print("관련주장 컬럼 고유값:", unique_assertions)

assertion_counts = control_df.groupby("관련주장").size()

print("관련주장별 건수:")
print(assertion_counts.sort_values(ascending=False))

# 건수가 많은 관련주장이 위로 오도록 오름차순 정렬
# (barh는 첫 항목을 아래, 마지막 항목을 위에 그리므로 오름차순 정렬 시
#  가장 큰 값이 맨 위에 위치한다)
assertion_counts = assertion_counts.sort_values(ascending=True)

# ------------------------------------------------------------------
# 시각화: 가로 막대그래프
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 7))

bars = ax.barh(
    assertion_counts.index,
    assertion_counts.values,
    color="#4C72B0",
)

ax.set_title("관련주장별 통제 분포", fontsize=15, pad=15)
ax.set_xlabel("통제 수", fontsize=12)
ax.set_ylabel("관련주장", fontsize=12)
ax.grid(axis="x", linestyle="--", alpha=0.3)

# 막대 끝 숫자가 잘리지 않도록 x축 여유 공간 확보
max_value = assertion_counts.values.max()
ax.set_xlim(0, max_value * 1.15)

for bar, value in zip(bars, assertion_counts.values):
    ax.annotate(
        f"{int(value)}",
        xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
        xytext=(6, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=11,
    )

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "08_assertion_distribution.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"이미지 저장 완료: {output_path}")
