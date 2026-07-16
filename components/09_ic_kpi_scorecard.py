import os

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

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
design_df = pd.read_csv(os.path.join(RAW_DIR, "ic_design_assessment.csv"))
operating_df = pd.read_csv(os.path.join(RAW_DIR, "ic_operating_assessment.csv"))
deficiency_df = pd.read_csv(os.path.join(RAW_DIR, "ic_deficiency.csv"))
remediation_df = pd.read_csv(os.path.join(RAW_DIR, "ic_remediation.csv"))

# ------------------------------------------------------------------
# 먼저 확인할 사항: 주요 컬럼의 실제 고유값 확인
# ------------------------------------------------------------------
design_result_unique = design_df["설계평가결과"].unique().tolist()
operating_result_unique = operating_df["운영평가결과"].unique().tolist()
remediation_status_unique = remediation_df["진행상태"].unique().tolist()
deficiency_status_unique = deficiency_df["현재상태"].unique().tolist()
key_flag_unique = control_df["Key여부"].unique().tolist()

print("설계평가결과 고유값:", design_result_unique)
print("운영평가결과 고유값:", operating_result_unique)
print("진행상태 고유값:", remediation_status_unique)
print("현재상태 고유값:", deficiency_status_unique)
print("Key여부 고유값:", key_flag_unique)

# 완료를 의미하는 값 결정: 위에서 확인한 고유값 중 "완료"가 실제로 존재하는지 검증한다.
if "완료" in remediation_status_unique:
    complete_value = "완료"
else:
    raise ValueError(
        f"'완료'를 의미하는 값을 진행상태 고유값에서 찾을 수 없습니다: {remediation_status_unique}"
    )

# ------------------------------------------------------------------
# KPI 계산 (raw 데이터 직접 계산, 코드에 숫자 직접 입력 없음)
# ------------------------------------------------------------------

# ① 설계 적정률
design_total = len(design_df)
design_ok = int((design_df["설계평가결과"] == "적정").sum())
design_ratio = design_ok / design_total * 100

# ② 운영 적정률
operating_total = len(operating_df)
operating_ok = int((operating_df["운영평가결과"] == "적정").sum())
operating_ratio = operating_ok / operating_total * 100

# ③ 미비점 발생률 (분자: 미비점 전체 건수, 분모: 운영평가 전체 건수)
deficiency_total = len(deficiency_df)
deficiency_ratio = deficiency_total / operating_total * 100

# ④ 개선 완료율
remediation_total = len(remediation_df)
remediation_ok = int((remediation_df["진행상태"] == complete_value).sum())
remediation_ratio = remediation_ok / remediation_total * 100

print("\n[KPI 계산 결과]")
print(f"① 설계 적정률: {design_ratio:.1f}% ({design_ok}건 / {design_total}건)")
print(f"② 운영 적정률: {operating_ratio:.1f}% ({operating_ok}건 / {operating_total}건)")
print(
    f"③ 미비점 발생률: {deficiency_ratio:.1f}% ({deficiency_total}건 / {operating_total}건)"
)
print(
    f"④ 개선 완료율: {remediation_ratio:.1f}% ({remediation_ok}건 / {remediation_total}건)"
)

# ------------------------------------------------------------------
# 카드에 사용할 데이터 정리
# ------------------------------------------------------------------
cards = [
    {
        "title": "설계 적정률",
        "value": design_ratio,
        "sub": f"{design_ok}건 / {design_total}건",
        "bg": "#EAF2FB",
        "border": "#4C72B0",
        "text": "#1F3B5C",
    },
    {
        "title": "운영 적정률",
        "value": operating_ratio,
        "sub": f"{operating_ok}건 / {operating_total}건",
        "bg": "#E7F6F8",
        "border": "#2E86AB",
        "text": "#154A57",
    },
    {
        "title": "미비점 발생률",
        "value": deficiency_ratio,
        "sub": f"{deficiency_total}건 / {operating_total}건",
        "bg": "#FDECEA",
        "border": "#C44E52",
        "text": "#8B1E1E",
    },
    {
        "title": "개선 완료율",
        "value": remediation_ratio,
        "sub": f"{remediation_ok}건 / {remediation_total}건",
        "bg": "#EAF7EC",
        "border": "#55A868",
        "text": "#1E5631",
    },
]

# ------------------------------------------------------------------
# 시각화: 가로로 나열된 4개의 KPI 카드
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 6))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

fig.suptitle("내부회계 핵심 KPI 스코어카드", fontsize=22, fontweight="bold", y=0.98)

n_cards = len(cards)
margin = 0.035
card_w = 0.21
gap = (1 - 2 * margin - n_cards * card_w) / (n_cards - 1)
card_h = 0.62
y0 = 0.15

for i, card in enumerate(cards):
    x0 = margin + i * (card_w + gap)

    box = FancyBboxPatch(
        (x0, y0),
        card_w,
        card_h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=2.5,
        edgecolor=card["border"],
        facecolor=card["bg"],
        transform=ax.transAxes,
    )
    ax.add_patch(box)

    cx = x0 + card_w / 2

    # 1. KPI 제목
    ax.text(
        cx,
        y0 + card_h - 0.10,
        card["title"],
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=card["text"],
        transform=ax.transAxes,
    )

    # 2. 핵심 숫자 (큰 백분율)
    ax.text(
        cx,
        y0 + card_h * 0.52,
        f"{card['value']:.1f}%",
        ha="center",
        va="center",
        fontsize=36,
        fontweight="bold",
        color=card["text"],
        transform=ax.transAxes,
    )

    # 3. 분자 / 분모 설명
    ax.text(
        cx,
        y0 + 0.12,
        card["sub"],
        ha="center",
        va="center",
        fontsize=13,
        color=card["text"],
        transform=ax.transAxes,
    )

plt.tight_layout(rect=[0, 0, 1, 0.94])

output_path = os.path.join(OUTPUT_DIR, "09_ic_kpi_scorecard.png")
plt.savefig(output_path, dpi=150)
plt.close(fig)

print(f"\n이미지 저장 완료: {output_path}")
