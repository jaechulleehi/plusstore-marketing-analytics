"""채널 데이터 × AppsFlyer 조인 분석.

하는 일:
1. 채널명 ↔ 미디어소스 매핑
2. (일, 채널, 캠페인, 그룹, 소재) 기준으로 조인
3. ROAS, CAC, 어트리뷰션 갭 계산
4. 채널별 / 캠페인별 요약 출력
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent

# 채널명 ↔ 미디어소스 매핑 (실무에서 제일 먼저 잡아야 할 딕셔너리)
CHANNEL_MAP = {
    "구글": "googleadwords_int",
    "메타": "Facebook Ads",
    "네이버": "naver_search",
}

# =============================================================================
# 1) 로드
# =============================================================================
ch = pd.read_csv(BASE / "channel_data.csv", parse_dates=["일"])
af = pd.read_csv(BASE / "appsflyer_data.csv", parse_dates=["일"])

# AppsFlyer 측에 '채널' 컬럼 역매핑해서 조인 키 통일
af["채널"] = af["미디어소스"].map({v: k for k, v in CHANNEL_MAP.items()})

print(f"채널 데이터   : {len(ch):,} 행")
print(f"AppsFlyer     : {len(af):,} 행")
print()

# =============================================================================
# 2) 조인 — (일, 채널, 캠페인, 그룹, 소재) 5개 키로 매칭
# =============================================================================
JOIN_KEYS = ["일", "채널", "캠페인", "그룹", "소재"]

# AppsFlyer 컬럼은 af_* 접두사로 구분 (같은 이름 충돌 방지)
af_renamed = af.rename(columns={
    "클릭": "af_클릭",
    "회원가입": "af_회원가입",
    "구매": "af_구매",
    "구매매출": "af_구매매출",
})[JOIN_KEYS + ["af_클릭", "af_회원가입", "af_구매", "af_구매매출"]]

merged = ch.merge(af_renamed, on=JOIN_KEYS, how="left")

print(f"조인 결과     : {len(merged):,} 행")
print(f"매칭 실패     : {merged['af_회원가입'].isna().sum()} 행")
print()

# =============================================================================
# 3) 파생 지표 계산
# =============================================================================
merged["CTR"]  = merged["클릭"] / merged["노출"]
merged["CPC"]  = merged["비용"] / merged["클릭"].replace(0, pd.NA)
merged["CAC_채널"] = merged["비용"] / merged["회원가입"].replace(0, pd.NA)
merged["CAC_AF"]   = merged["비용"] / merged["af_회원가입"].replace(0, pd.NA)
merged["ROAS_채널"] = merged["구매매출"] / merged["비용"]
merged["ROAS_AF"]   = merged["af_구매매출"] / merged["비용"]
merged["어트리뷰션_갭_가입"] = (
    (merged["회원가입"] - merged["af_회원가입"]) / merged["회원가입"].replace(0, pd.NA)
)

# =============================================================================
# 4) 채널별 요약
# =============================================================================
print("=" * 78)
print("채널별 집계")
print("=" * 78)
ch_summary = merged.groupby("채널").agg(
    비용=("비용", "sum"),
    노출=("노출", "sum"),
    클릭=("클릭", "sum"),
    가입_채널=("회원가입", "sum"),
    가입_AF=("af_회원가입", "sum"),
    매출_채널=("구매매출", "sum"),
    매출_AF=("af_구매매출", "sum"),
).reset_index()

ch_summary["CTR"] = (ch_summary["클릭"] / ch_summary["노출"] * 100).round(2)
ch_summary["CAC_채널"] = (ch_summary["비용"] / ch_summary["가입_채널"]).round(0)
ch_summary["CAC_AF"] = (ch_summary["비용"] / ch_summary["가입_AF"]).round(0)
ch_summary["ROAS_채널"] = (ch_summary["매출_채널"] / ch_summary["비용"]).round(2)
ch_summary["ROAS_AF"] = (ch_summary["매출_AF"] / ch_summary["비용"]).round(2)
ch_summary["어트리뷰션_커버리지_%"] = (
    ch_summary["가입_AF"] / ch_summary["가입_채널"] * 100
).round(1)

# 숫자 보기 좋게
fmt = {
    "비용": "{:,.0f}",
    "노출": "{:,.0f}",
    "클릭": "{:,.0f}",
    "가입_채널": "{:,.0f}",
    "가입_AF": "{:,.0f}",
    "매출_채널": "{:,.0f}",
    "매출_AF": "{:,.0f}",
    "CAC_채널": "{:,.0f}",
    "CAC_AF": "{:,.0f}",
}
print(ch_summary.to_string(index=False, formatters={k: v.format for k, v in fmt.items()}))

# =============================================================================
# 5) 캠페인별 랭킹 (ROAS 기준)
# =============================================================================
print()
print("=" * 78)
print("캠페인별 ROAS 랭킹 (AppsFlyer 기준 매출)")
print("=" * 78)
cmp_summary = merged.groupby(["채널", "캠페인"]).agg(
    비용=("비용", "sum"),
    가입_AF=("af_회원가입", "sum"),
    매출_AF=("af_구매매출", "sum"),
).reset_index()
cmp_summary["ROAS_AF"] = (cmp_summary["매출_AF"] / cmp_summary["비용"]).round(2)
cmp_summary["CAC_AF"] = (cmp_summary["비용"] / cmp_summary["가입_AF"]).round(0)
cmp_summary = cmp_summary.sort_values("ROAS_AF", ascending=False)
print(cmp_summary.to_string(index=False, formatters={k: v.format for k, v in fmt.items()}))

# =============================================================================
# 6) 결과 저장
# =============================================================================
out = BASE / "joined_result.csv"
merged.to_csv(out, index=False, encoding="utf-8-sig")
print(f"\n조인된 raw 결과 저장: {out}")
