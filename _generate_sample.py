"""CLAUDE.md §3 네이밍 컨벤션을 따르는 샘플 데이터 생성 (일자별 파일).

출력 구조:
- raw/channel/{YYYY-MM-DD}.csv   : 날짜별 채널 광고 raw
- raw/appsflyer/{YYYY-MM-DD}.csv : 날짜별 AppsFlyer raw

DuckDB glob 패턴으로 폴더 통째로 자동 병합됨.
"""
from __future__ import annotations

import csv
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
BASE = Path(__file__).resolve().parent
CH_DIR = BASE / "raw" / "channel"
AF_DIR = BASE / "raw" / "appsflyer"

# 매 실행 시 깨끗하게 재생성
if CH_DIR.exists(): shutil.rmtree(CH_DIR)
if AF_DIR.exists(): shutil.rmtree(AF_DIR)
CH_DIR.mkdir(parents=True, exist_ok=True)
AF_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CLAUDE.md §3-1 채널 매핑 (외부/자체 구분)
# =============================================================================
CHANNELS = [
    ("구글",  "googleadwords_int", "외부"),
    ("메타",  "Facebook Ads",      "외부"),
    ("네이버", "naver_search",     "자체"),
]

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
    m, day = d.month, d.day
    if m == 11 and day >= 20: return "블프"
    if m == 12:               return "연말"
    if m in (1, 2):           return "겨울"
    if m == 3:                return "신학기" if day <= 10 else "봄"
    if m in (4, 5):           return "봄"
    if m in (6, 7, 8):        return "여름"
    return "가을"


def build_creative_name(typ: str, cat: str, season: str,
                        ab: str | None, ver: int) -> str:
    parts = [typ, cat, season]
    if ab:
        parts.append(ab)
    parts.append(f"v{ver}")
    return "_".join(parts)


PROFILE_BASE = {
    "구글":  dict(cpm=5500, ctr=0.025, signup_cvr=0.09, buy_cvr=0.30, aov=55000),
    "메타":  dict(cpm=4200, ctr=0.018, signup_cvr=0.07, buy_cvr=0.25, aov=48000),
    "네이버": dict(cpm=8000, ctr=0.045, signup_cvr=0.12, buy_cvr=0.35, aov=62000),
}
OBJ_MULT = {
    "플러스가입":  (1.1, 1.3, 0.9, 1.0),
    "첫구매":     (1.0, 1.0, 1.3, 1.1),
    "리타겟팅":   (1.4, 1.2, 1.5, 1.0),
    "재구매":     (1.3, 0.8, 2.0, 1.4),
    "신규유저":   (0.9, 1.0, 0.9, 0.95),
    "룩얼라이크": (1.0, 1.1, 1.0, 1.0),
    "브랜드KW":   (3.0, 2.0, 1.5, 1.1),
    "일반KW":     (1.8, 1.3, 1.1, 1.0),
}
AF_CLICK    = (0.85, 0.98)
AF_SIGNUP   = (0.70, 0.92)
AF_PURCHASE = (0.68, 0.90)
AF_REVENUE  = (0.72, 0.93)

START = date(2025, 1, 1)
END   = date(2025, 3, 31)

CH_HEADER = ["일", "채널", "채널분류", "캠페인", "캠페인목적", "그룹", "소재",
             "노출", "클릭", "비용", "회원가입", "구매", "구매매출"]
AF_HEADER = ["일", "미디어소스", "캠페인", "그룹", "소재",
             "클릭", "회원가입", "구매", "구매매출"]

total_ch, total_af = 0, 0
d = START
while d <= END:
    dow_mult = 0.75 if d.weekday() >= 5 else 1.0
    boost = 1.25 if d.day <= 3 else 1.0
    payday_buy_mult = 1.4 if d.day in (10, 15, 25) else 1.0
    cur_season = season_for(d)

    ch_rows_today = []
    af_rows_today = []

    for ch, ms, ch_class in CHANNELS:
        prof_ch = PROFILE_BASE[ch]
        for cmp_id, obj in CAMPAIGNS[ch]:
            groups = GROUPS_BY_OBJECTIVE[obj]
            ctr_m, cvr_m, buy_m, aov_m = OBJ_MULT[obj]
            for grp in groups:
                pool = CREATIVE_POOL[obj]
                for idx, (typ, cat) in enumerate(pool):
                    ab = "A" if idx == 0 else ("B" if idx == 1 else None)
                    ver = 1 if idx < 2 else (idx - 1)
                    creative = build_creative_name(typ, cat, cur_season, ab, ver)

                    base_impr = {"구글": 55000, "메타": 42000, "네이버": 18000}[ch]
                    if grp in ("VIP",):     base_impr *= 0.3
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

                    ch_rows_today.append([
                        d.isoformat(), ch, ch_class, cmp_id, obj, grp, creative,
                        impr, click, cost, signup, buy, revenue,
                    ])
                    af_rows_today.append([
                        d.isoformat(), ms, cmp_id, grp, creative,
                        int(click   * random.uniform(*AF_CLICK)),
                        int(signup  * random.uniform(*AF_SIGNUP)),
                        int(buy     * random.uniform(*AF_PURCHASE)),
                        int(revenue * random.uniform(*AF_REVENUE)),
                    ])

    # 일자별 파일 저장 (utf-8-sig 로 엑셀 한글 안 깨지게)
    day_str = d.isoformat()
    with (CH_DIR / f"{day_str}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(CH_HEADER); w.writerows(ch_rows_today)
    with (AF_DIR / f"{day_str}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(AF_HEADER); w.writerows(af_rows_today)

    total_ch += len(ch_rows_today)
    total_af += len(af_rows_today)
    d += timedelta(days=1)

n_files = len(list(CH_DIR.glob("*.csv")))
print(f"채널 파일    : {n_files}개  ({total_ch:,} rows 총합)  → {CH_DIR}")
print(f"AppsFlyer    : {n_files}개  ({total_af:,} rows 총합)  → {AF_DIR}")
print()
print("폴더 첫 3개 파일:")
for p in sorted(CH_DIR.iterdir())[:3]:
    print(f"  {p.relative_to(BASE)}")
print("...")
for p in sorted(CH_DIR.iterdir())[-2:]:
    print(f"  {p.relative_to(BASE)}")
