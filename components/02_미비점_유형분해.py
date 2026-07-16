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
deficiency_df = pd.read_csv(os.path.join(RAW_DIR, "ic_deficiency.csv"))

unique_types = deficiency_df["미비점유형"].unique().tolist()
print("미비점유형 컬럼 고유값:", unique_types)

type_counts = deficiency_df.groupby("미비점유형").size()

# 건수가 많은 유형이 위로 오도록 오름차순 정렬
# (barh는 첫 항목을 아래, 마지막 항목을 위에 그리므로 오름차순 정렬 시
#  가장 큰 값이 맨 위에 위치한다)
type_counts = type_counts.sort_values(ascending=True)

print("미비점유형별 건수:")
print(type_counts.sort_values(ascending=False))

# ------------------------------------------------------------------
# 시각화: 가로 막대그래프
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 7))

bars = ax.barh(
    type_counts.index,
    type_counts.values,
    color="#4C72B0",
)

ax.set_title("미비점 유형별 발생 현황", fontsize=15, pad=15)
ax.set_xlabel("발생 건수", fontsize=12)
ax.set_ylabel("미비점 유형", fontsize=12)
ax.grid(axis="x", linestyle="--", alpha=0.3)

# 막대 끝 숫자가 잘리지 않도록 x축 여유 공간 확보
max_value = type_counts.values.max()
ax.set_xlim(0, max_value * 1.15)

for bar, value in zip(bars, type_counts.values):
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

output_path = os.path.join(OUTPUT_DIR, "02_미비점_유형분해.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"이미지 저장 완료: {output_path}")
