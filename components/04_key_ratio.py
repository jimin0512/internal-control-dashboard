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

key_count = int((control_df["Key여부"] == "Y").sum())
non_key_count = int((control_df["Key여부"] != "Y").sum())
total_count = key_count + non_key_count

print("Key 통제 건수:", key_count)
print("Non-Key 통제 건수:", non_key_count)
print("전체 통제 건수:", total_count)

labels = ["Key 통제", "Non-Key 통제"]
counts = [key_count, non_key_count]
colors = ["#DD8452", "#4C72B0"]

# ------------------------------------------------------------------
# 시각화: 도넛 차트 (퍼센트 + 건수 함께 표시)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 8))


def autopct_format(pct, all_values):
    absolute = int(round(pct / 100.0 * sum(all_values)))
    return f"{pct:.1f}%\n({absolute}건)"


wedges, texts, autotexts = ax.pie(
    counts,
    labels=labels,
    colors=colors,
    autopct=lambda pct: autopct_format(pct, counts),
    startangle=90,
    wedgeprops=dict(width=0.4, edgecolor="white"),
    textprops=dict(fontsize=12),
    pctdistance=0.78,
)

for autotext in autotexts:
    autotext.set_fontsize(12)
    autotext.set_color("white")
    autotext.set_fontweight("bold")

ax.set_title("Key 통제 비율", fontsize=16, pad=20)
ax.text(
    0,
    0,
    f"전체\n{total_count}건",
    ha="center",
    va="center",
    fontsize=13,
    fontweight="bold",
)
ax.legend(wedges, labels, loc="upper left", bbox_to_anchor=(-0.15, 1.05), fontsize=11)

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "04_key_ratio.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"이미지 저장 완료: {output_path}")
