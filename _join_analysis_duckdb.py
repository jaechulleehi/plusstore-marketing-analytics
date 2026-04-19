"""채널 × AppsFlyer 조인 분석 (DuckDB 버전).

DuckDB 장점 (vs pandas):
- CSV 파일을 직접 SQL로 쿼리 (로드 코드 불필요)
- SQL 문법으로 조인·집계·윈도우 함수 표현
- 수백만 행으로 늘어나도 동일 코드, 훨씬 빠름
- 결과는 바로 pandas DataFrame으로 받을 수 있음 (.df())
"""
from pathlib import Path

import duckdb

BASE = Path(__file__).resolve().parent
CH_CSV = BASE / "channel_data.csv"
AF_CSV = BASE / "appsflyer_data.csv"

# 메모리 DB 세션 (파일로 저장하고 싶으면 duckdb.connect("mktg.duckdb"))
con = duckdb.connect(":memory:")

# =============================================================================
# 0) 뷰 등록 — CSV를 "테이블처럼" 쓸 수 있게 매핑 (실제 로드는 쿼리 시점)
# =============================================================================
con.execute(f"""
CREATE VIEW channel AS
SELECT * FROM read_csv_auto('{CH_CSV}');

CREATE VIEW appsflyer AS
SELECT * FROM read_csv_auto('{AF_CSV}');

-- 네이밍 매핑 테이블 (실무에서 이 딕셔너리를 어디에 두느냐가 관건)
CREATE TABLE channel_map (채널 VARCHAR, 미디어소스 VARCHAR);
INSERT INTO channel_map VALUES
    ('구글',  'googleadwords_int'),
    ('메타',  'Facebook Ads'),
    ('네이버', 'naver_search');
""")

print(f"채널 데이터   : {con.execute('SELECT COUNT(*) FROM channel').fetchone()[0]:,} 행")
print(f"AppsFlyer     : {con.execute('SELECT COUNT(*) FROM appsflyer').fetchone()[0]:,} 행")
print()

# =============================================================================
# 1) 조인 — SQL 한 방
# =============================================================================
con.execute("""
CREATE TABLE joined AS
SELECT
    c.일,
    c.채널,
    c.캠페인,
    c.그룹,
    c.소재,
    c.노출,
    c.클릭,
    c.비용,
    c.회원가입,
    c.구매,
    c.구매매출,
    a.클릭      AS af_클릭,
    a.회원가입   AS af_회원가입,
    a.구매      AS af_구매,
    a.구매매출   AS af_구매매출
FROM channel c
LEFT JOIN channel_map m ON c.채널 = m.채널
LEFT JOIN appsflyer  a
    ON a.일          = c.일
    AND a.미디어소스 = m.미디어소스
    AND a.캠페인     = c.캠페인
    AND a.그룹       = c.그룹
    AND a.소재       = c.소재;
""")

stats = con.execute("""
SELECT COUNT(*) total, COUNT(*) FILTER (WHERE af_회원가입 IS NULL) unmatched
FROM joined
""").fetchone()
print(f"조인 결과     : {stats[0]:,} 행")
print(f"매칭 실패     : {stats[1]} 행")
print()

# =============================================================================
# 2) 채널별 집계 — 파생 지표까지 SQL 한 번에
# =============================================================================
print("=" * 86)
print("채널별 집계")
print("=" * 86)
ch_summary = con.execute("""
SELECT
    채널,
    SUM(비용)        AS 비용,
    SUM(노출)        AS 노출,
    SUM(클릭)        AS 클릭,
    SUM(회원가입)     AS 가입_채널,
    SUM(af_회원가입)  AS 가입_AF,
    SUM(구매매출)     AS 매출_채널,
    SUM(af_구매매출)  AS 매출_AF,
    ROUND(SUM(클릭)::DOUBLE / SUM(노출) * 100, 2)                    AS "CTR(%)",
    ROUND(SUM(비용)::DOUBLE / SUM(회원가입), 0)                       AS CAC_채널,
    ROUND(SUM(비용)::DOUBLE / SUM(af_회원가입), 0)                    AS CAC_AF,
    ROUND(SUM(구매매출)::DOUBLE / SUM(비용), 2)                       AS ROAS_채널,
    ROUND(SUM(af_구매매출)::DOUBLE / SUM(비용), 2)                    AS ROAS_AF,
    ROUND(SUM(af_회원가입)::DOUBLE / SUM(회원가입) * 100, 1)           AS "AF커버리지(%)"
FROM joined
GROUP BY 채널
ORDER BY ROAS_AF DESC
""").df()
print(ch_summary.to_string(index=False))

# =============================================================================
# 3) 캠페인 ROAS 랭킹
# =============================================================================
print()
print("=" * 86)
print("캠페인별 ROAS 랭킹 (AF 기준)")
print("=" * 86)
cmp_summary = con.execute("""
SELECT
    채널,
    캠페인,
    SUM(비용)                                                        AS 비용,
    SUM(af_회원가입)                                                  AS 가입_AF,
    SUM(af_구매매출)                                                  AS 매출_AF,
    ROUND(SUM(af_구매매출)::DOUBLE / SUM(비용), 2)                    AS ROAS_AF,
    ROUND(SUM(비용)::DOUBLE / SUM(af_회원가입), 0)                    AS CAC_AF
FROM joined
GROUP BY 채널, 캠페인
ORDER BY ROAS_AF DESC
""").df()
print(cmp_summary.to_string(index=False))

# =============================================================================
# 4) 보너스 — DuckDB 만의 강점: 윈도우 함수로 채널 내 랭킹
# =============================================================================
print()
print("=" * 86)
print("보너스: 채널 내 소재별 ROAS 랭킹 (윈도우 함수)")
print("=" * 86)
creative_rank = con.execute("""
SELECT
    채널,
    소재,
    SUM(비용)                                           AS 비용,
    SUM(af_구매매출)                                    AS 매출_AF,
    ROUND(SUM(af_구매매출)::DOUBLE / SUM(비용), 2)     AS ROAS_AF,
    RANK() OVER (
        PARTITION BY 채널
        ORDER BY SUM(af_구매매출)::DOUBLE / SUM(비용) DESC
    ) AS 채널내_순위
FROM joined
GROUP BY 채널, 소재
ORDER BY 채널, 채널내_순위
""").df()
print(creative_rank.to_string(index=False))

# =============================================================================
# 5) 저장 — 용도별로 2가지 포맷
#    - Parquet: 파이프라인 내부용 (빠름·작음·타입 보존)
#    - CSV:     사람 공유용 (엑셀/VSCode에서 바로 열림)
# =============================================================================
out_parquet = BASE / "joined_result.parquet"
out_csv     = BASE / "joined_result.csv"

con.execute(f"COPY joined TO '{out_parquet}' (FORMAT PARQUET)")
# DuckDB → pandas → CSV (utf-8-sig 로 엑셀에서 한글 안 깨지게)
con.execute("SELECT * FROM joined").df().to_csv(
    out_csv, index=False, encoding="utf-8-sig"
)

pq_size = out_parquet.stat().st_size / 1024
cs_size = out_csv.stat().st_size / 1024
print(f"\n저장 결과")
print(f"  Parquet: {out_parquet.name}  ({pq_size:>7,.0f} KB) ← 내부 파이프라인용")
print(f"  CSV    : {out_csv.name}      ({cs_size:>7,.0f} KB) ← 공유/확인용")
print(f"  압축률: Parquet이 CSV 대비 {cs_size/pq_size:.1f}배 작음")

# 채널별 요약도 별도 CSV로 (발표·리포트용 — 엑셀 한글 깨짐 방지)
ch_summary.to_csv(BASE / "summary_by_channel.csv", index=False, encoding="utf-8-sig")
cmp_summary.to_csv(BASE / "summary_by_campaign.csv", index=False, encoding="utf-8-sig")
print(f"  요약 CSV: summary_by_channel.csv, summary_by_campaign.csv (공유용)")

con.close()
