"""CLAUDE.md §3 네이밍 컨벤션을 따르는 샘플 데이터 생성.

출력:
- channel_data.csv   : 채널분류 컬럼 포함 (외부/자체)
- appsflyer_data.csv : 동일 캠페인·그룹·소재 구조로 조인 가능
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT_DIR = Path(__file__).resolve().parent

# =============================================================================
# CLAUDE.md §3-1 채널 매핑 (외부/자체 구분)
# =============================================================================
CHANNELS = [
    # (채널, AppsFlyer 미디어소스, 분류)
    ("구글",  "googleadwords_int", "외부"),
    ("메타",  "Facebook Ads",      "외부"),
    ("네이버", "naver_search",     "자체"),
]

# §3-2 캠페인 구성: 채널마다 목적별 캠페인 세팅
# (캠페인ID, 목적)
CAMPAIGNS = {
    "구글": [
        ("GGL_CMP_01_플러스가입", "플러스가입"),
        ("GGL_CMP_02_리타겟팅",   "리타겟팅"),
        ("GGL_CMP_03_첫구매",     "첫구매"),
    ],
    "메타": [
        ("META_CMP_01_신규유저",   "신규유저"),
        ("META_CMP_02_룩얼라이크", "룩얼라이크"),
        ("META_CMP_03_재구매",     "재구매"),
    ],
    "네이버": [
        ("NVR_CMP_01_브랜드KW",    "브랜드KW"),
        ("NVR_CMP_02_일반KW",      "일반KW"),
        ("NVR_CMP_03_재구매",      "재구매"),
    ],
}

# §3-4 타겟그룹 매핑 (목적별 적절한 그룹)
GROUPS_BY_OBJECTIVE = {
    "플러스가입": ["논타겟", "유사타겟"],
    "리타겟팅":  ["리마케팅"],
    "첫구매":    ["논타겟", "유사타겟"],
    "신규유저":  ["논타겟"],
    "룩얼라이크": ["유사타겟"],
    "브랜드KW":  ["논타겟"],
    "일반KW":    ["논타겟"],
    "재구매":    ["VIP", "윈백"],
}

# §3-3 소재 네이밍: {타입}_{카테고리}_{시즌}_{AB}_{버전}
# 목적별로 어울리는 소재 조합 정의 (type, category)
CREATIVE_POOL = {
    "플러스가입": [("VID", "플러스멤버십"), ("IMG", "플러스멤버십"),
                ("CRS", "플러스멤버십"), ("IMG", "적립혜택")],
    "첫구매":    [("VID", "적립혜택"), ("IMG", "적립혜택"), ("CRS", "할인쿠폰")],
    "리타겟팅":  [("VID", "할인쿠폰"), ("IMG", "할인쿠폰"), ("CRS", "특가")],
    "재구매":    [("IMG", "배송혜택"), ("VID", "적립혜택"), ("CRS", "신상품")],
    "신규유저":  [("VID", "플러스멤버십"), ("IMG", "적립혜택"), ("CRS", "플러스멤버십")],
    "룩얼라이크": [("VID", "플러스멤버십"), ("IMG", "할인쿠폰"), ("CRS", "특가")],
    "브랜드KW":  [("TXT", "플러스멤버십")],
    "일반KW":    [("TXT", "할인쿠폰"), ("TXT", "플러스멤버십")],
}


def season_for(d: date) -> str:
    """월 기준 시즌. 블프는 11월 20일 이후, 연말은 12월."""
    m, day = d.month, d.day
    if m == 11 and day >= 20: return "블프"
    if m == 12:               return "연말"
    if m in (1, 2):           return "겨울"
    if m == 3:                return "신학기" if day <= 10 else "봄"
    if m in (4, 5):           return "봄"
    if m in (6, 7, 8):        return "여름"
    return "가을"


def build_creative_name(typ: str, cat: str, season: str, ab: str | None, ver: int) -> str:
    """§3-3 포맷: {타입}_{카테고리}_{시즌}_{AB}_{v버전}. AB 없으면 4파트."""
    parts = [typ, cat, season]
    if ab:
        parts.append(ab)
    parts.append(f"v{ver}")
    return "_".join(parts)


# =============================================================================
# 채널·목적별 성과 프로파일 (CPM, CTR, 가입 CVR, 구매 CVR, AOV)
# - 브랜드KW: CTR·CVR 매우 높음 (의도적 검색), CPC 싸서 ROAS 부풀려짐
# - 재구매(VIP·윈백): CVR 높고 AOV 큼
# - 리타겟팅: CVR 중상, CAC 낮음
# =============================================================================
PROFILE_BASE = {
    "구글":  dict(cpm=5500, ctr=0.025, signup_cvr=0.09, buy_cvr=0.30, aov=55000),
    "메타":  dict(cpm=4200, ctr=0.018, signup_cvr=0.07, buy_cvr=0.25, aov=48000),
    "네이버": dict(cpm=8000, ctr=0.045, signup_cvr=0.12, buy_cvr=0.35, aov=62000),
}
OBJ_MULT = {
    # obj: (ctr_mult, signup_cvr_mult, buy_cvr_mult, aov_mult)
    "플러스가입":  (1.1, 1.3, 0.9, 1.0),
    "첫구매":     (1.0, 1.0, 1.3, 1.1),
    "리타겟팅":   (1.4, 1.2, 1.5, 1.0),  # 인지층이라 전환 효율 높음
    "재구매":     (1.3, 0.8, 2.0, 1.4),  # 가입은 이미 했고, 구매·AOV 큼
    "신규유저":   (0.9, 1.0, 0.9, 0.95),
    "룩얼라이크": (1.0, 1.1, 1.0, 1.0),
    "브랜드KW":   (3.0, 2.0, 1.5, 1.1),  # 부풀려진 ROAS 재현
    "일반KW":     (1.8, 1.3, 1.1, 1.0),
}

# AppsFlyer 어트리뷰션 드랍 (채널 대비)
AF_CLICK    = (0.85, 0.98)
AF_SIGNUP   = (0.70, 0.92)
AF_PURCHASE = (0.68, 0.90)
AF_REVENUE  = (0.72, 0.93)

START = date(2025, 1, 1)
END   = date(2025, 3, 31)

channel_rows = []
af_rows = []
d = START
while d <= END:
    dow_mult = 0.75 if d.weekday() >= 5 else 1.0
    boost = 1.25 if d.day <= 3 else 1.0
    # 월급일 (10·15·25) 구매 피크
    payday_buy_mult = 1.4 if d.day in (10, 15, 25) else 1.0
    cur_season = season_for(d)

    for ch, ms, ch_class in CHANNELS:
        prof_ch = PROFILE_BASE[ch]
        for cmp_id, obj in CAMPAIGNS[ch]:
            groups = GROUPS_BY_OBJECTIVE[obj]
            ctr_m, cvr_m, buy_m, aov_m = OBJ_MULT[obj]

            for grp in groups:
                pool = CREATIVE_POOL[obj]
                # 소재 고정 세트 (캠페인·그룹별로 4개)
                for idx, (typ, cat) in enumerate(pool):
                    # 첫 2개는 A/B 테스트 페어, 나머지는 AB 없음
                    ab = "A" if idx == 0 else ("B" if idx == 1 else None)
                    ver = 1 if idx < 2 else (idx - 1)
                    creative = build_creative_name(typ, cat, cur_season, ab, ver)

                    # 노출 스케일: 채널 × 그룹 특성
                    base_impr = {"구글": 55000, "메타": 42000, "네이버": 18000}[ch]
                    if grp in ("VIP",):     base_impr *= 0.3   # 타겟 작음
                    if grp == "윈백":       base_impr *= 0.5
                    if grp == "리마케팅":    base_impr *= 0.6
                    if obj == "브랜드KW":   base_impr *= 0.5
                    if obj == "일반KW":     base_impr *= 0.7

                    impr = int(base_impr * dow_mult * boost *
                               random.uniform(0.7, 1.3))
                    ctr = max(0.002, prof_ch["ctr"] * ctr_m *
                              random.uniform(0.7, 1.3))
                    click = int(impr * ctr)
                    cost = round(impr / 1000 * prof_ch["cpm"] *
                                 random.uniform(0.8, 1.2))

                    signup_cvr = max(0.005, prof_ch["signup_cvr"] * cvr_m *
                                     random.uniform(0.7, 1.3))
                    signup = int(click * signup_cvr)

                    buy_cvr = max(0.05, prof_ch["buy_cvr"] * buy_m *
                                  payday_buy_mult * random.uniform(0.7, 1.3))
                    buy = int(signup * buy_cvr)
                    revenue = int(buy * prof_ch["aov"] * aov_m *
                                  random.uniform(0.8, 1.3))

                    channel_rows.append([
                        d.isoformat(), ch, ch_class, cmp_id, obj, grp, creative,
                        impr, click, cost, signup, buy, revenue,
                    ])
                    af_rows.append([
                        d.isoformat(), ms, cmp_id, grp, creative,
                        int(click   * random.uniform(*AF_CLICK)),
                        int(signup  * random.uniform(*AF_SIGNUP)),
                        int(buy     * random.uniform(*AF_PURCHASE)),
                        int(revenue * random.uniform(*AF_REVENUE)),
                    ])
    d += timedelta(days=1)

# =============================================================================
# Write CSVs
# =============================================================================
ch_path = OUT_DIR / "channel_data.csv"
with ch_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["일", "채널", "채널분류", "캠페인", "캠페인목적", "그룹", "소재",
                "노출", "클릭", "비용", "회원가입", "구매", "구매매출"])
    w.writerows(channel_rows)

af_path = OUT_DIR / "appsflyer_data.csv"
with af_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["일", "미디어소스", "캠페인", "그룹", "소재",
                "클릭", "회원가입", "구매", "구매매출"])
    w.writerows(af_rows)

print(f"channel_data.csv   : {len(channel_rows):,} rows  → {ch_path}")
print(f"appsflyer_data.csv : {len(af_rows):,} rows  → {af_path}")
print()
print("샘플 소재명 예시:")
for r in random.sample(channel_rows, 8):
    print(f"  [{r[4]:>10}] {r[6]}  ({r[1]})")
