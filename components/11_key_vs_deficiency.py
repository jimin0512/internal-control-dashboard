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
# 데이터 로드 (raw CSV를 매번 새로 읽어서 계산한다)
# ------------------------------------------------------------------
control_df = pd.read_csv(os.path.join(RAW_DIR, "ic_control_master.csv"))
operating_df = pd.read_csv(os.path.join(RAW_DIR, "ic_operating_assessment.csv"))
deficiency_df = pd.read_csv(os.path.join(RAW_DIR, "ic_deficiency.csv"))

control_ref = control_df[["통제ID", "프로세스명", "Key여부"]]

# ------------------------------------------------------------------
# 데이터 연결: 통제ID 기준으로 조인 (ic_control_master -> ic_operating_assessment)
# ------------------------------------------------------------------
before_oper = len(operating_df)
operating_merged = operating_df.merge(
    control_ref[["통제ID", "프로세스명"]], on="통제ID", how="left"
)
after_oper = len(operating_merged)
print(f"[운영평가 조인] 조인 전 행 수: {before_oper} / 조인 후 행 수: {after_oper}")
if after_oper != before_oper:
    raise ValueError(
        f"운영평가 조인 후 행 수가 비정상적으로 변경되었습니다. (전: {before_oper}, 후: {after_oper})"
    )

# ------------------------------------------------------------------
# 데이터 연결: 통제ID 기준으로 조인 (ic_control_master -> ic_deficiency)
# 미비점 파일 자체의 프로세스명 컬럼은 사용하지 않고, 통제ID로 다시 연결한 값을 사용한다.
# ------------------------------------------------------------------
before_defi = len(deficiency_df)
deficiency_merged = deficiency_df.drop(columns=["프로세스명"]).merge(
    control_ref[["통제ID", "프로세스명"]], on="통제ID", how="left"
)
after_defi = len(deficiency_merged)
print(f"[미비점 조인] 조인 전 행 수: {before_defi} / 조인 후 행 수: {after_defi}")
if after_defi != before_defi:
    raise ValueError(
        f"미비점 조인 후 행 수가 비정상적으로 변경되었습니다. (전: {before_defi}, 후: {after_defi})"
    )

# ------------------------------------------------------------------
# 프로세스별 계산
# ------------------------------------------------------------------
# ① 전체 통제 수, ② Key 통제 수, ③ Key 통제 비율
control_summary = control_df.groupby("프로세스명").agg(
    전체통제수=("통제ID", "size"),
    Key통제수=("Key여부", lambda s: (s == "Y").sum()),
)
control_summary["Key통제비율"] = (
    control_summary["Key통제수"] / control_summary["전체통제수"] * 100
)

# ④ 운영평가 건수
operating_summary = operating_merged.groupby("프로세스명").size().rename("운영평가건수")

# ⑤ 미비점 건수
deficiency_summary = deficiency_merged.groupby("프로세스명").size().rename("미비점건수")

summary = control_summary.join(operating_summary, how="left").join(
    deficiency_summary, how="left"
)
summary["미비점건수"] = summary["미비점건수"].fillna(0).astype(int)
summary["운영평가건수"] = summary["운영평가건수"].fillna(0).astype(int)

# ⑥ 미비 발생률
summary["미비발생률"] = summary["미비점건수"] / summary["운영평가건수"] * 100

print("\n프로세스별 집계 결과:")
print(summary)

# 미비 발생률이 높은 순으로 정렬
summary = summary.sort_values("미비발생률", ascending=False)

highest_deficiency_process = summary.index[0]
highest_key_ratio_process = summary["Key통제비율"].idxmax()

print(f"\n미비 발생률이 가장 높은 프로세스: {highest_deficiency_process} "
      f"({summary.loc[highest_deficiency_process, '미비발생률']:.1f}%)")
print(f"Key 통제 비율이 가장 높은 프로세스: {highest_key_ratio_process} "
      f"({summary.loc[highest_key_ratio_process, 'Key통제비율']:.1f}%)")

# ------------------------------------------------------------------
# 시각화: 막대(Key 통제 비율) + 꺾은선(미비 발생률) 결합 차트
# ------------------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(16, 9))
ax2 = ax1.twinx()

x = range(len(summary.index))

bars = ax1.bar(
    x,
    summary["Key통제비율"],
    color="#4C72B0",
    width=0.55,
    label="Key 통제 비율(%)",
)

line = ax2.plot(
    x,
    summary["미비발생률"],
    color="#C44E52",
    marker="o",
    markersize=8,
    linewidth=2.2,
    label="미비 발생률(%)",
)

ax1.set_title("프로세스별 Key 통제 비율과 미비 발생률", fontsize=17, pad=18)
ax1.set_xlabel("프로세스", fontsize=13)
ax1.set_ylabel("Key 통제 비율(%)", fontsize=13, color="#4C72B0")
ax2.set_ylabel("미비 발생률(%)", fontsize=13, color="#C44E52")

ax1.set_xticks(list(x))
ax1.set_xticklabels(summary.index, rotation=40, ha="right")

ax1.set_ylim(0, 100 + 15)
ax2.set_ylim(0, summary["미비발생률"].max() * 1.4 + 5)

ax1.tick_params(axis="y", labelcolor="#4C72B0")
ax2.tick_params(axis="y", labelcolor="#C44E52")

ax1.grid(axis="y", linestyle="--", alpha=0.3)

# 막대와 선의 값이 시각적으로 겹치는 경우에도 읽을 수 있도록
# 각 라벨에 배경 박스를 넣는다.
bar_label_box = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)
line_label_box = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)

# 막대 위 Key 통제 비율(%) 표시
for bar, value in zip(bars, summary["Key통제비율"]):
    ax1.annotate(
        f"{value:.1f}%",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 8),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="#2C4770",
        bbox=bar_label_box,
    )

# 점 위 미비 발생률(%) 표시 (막대 라벨과 겹치지 않도록 더 높은 위치에 표시)
for xi, yi in zip(x, summary["미비발생률"]):
    ax2.annotate(
        f"{yi:.1f}%",
        xy=(xi, yi),
        xytext=(0, 20),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="#8B1E1E",
        bbox=line_label_box,
    )

# 범례: 막대 + 선을 하나로 합쳐서 표시
handles = [bars, line[0]]
labels = ["Key 통제 비율(%)", "미비 발생률(%)"]
ax1.legend(handles, labels, loc="upper right", fontsize=12)

plt.tight_layout()

output_path = os.path.join(OUTPUT_DIR, "11_key_vs_deficiency.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"\n이미지 저장 완료: {output_path}")
