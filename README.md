# Plus Store Marketing Dashboard (Practice)

> ⚠️ **Practice / demo repo**. 합성 샘플 데이터만 포함 — 실제 회사 데이터 아님.

네이버 플러스 스토어 퍼포먼스 마케팅 분석 대시보드 연습 프로젝트.
채널 광고 데이터 × AppsFlyer 어트리뷰션 데이터를 DuckDB로 조인하고, Streamlit으로 시각화.

## 스택

- **Python 3.11+**
- **DuckDB** — 채널 × AppsFlyer 조인
- **pandas** — 전처리
- **Plotly** — 인터랙티브 차트
- **Streamlit** — 대시보드

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run dashboard_app.py
```

접속: http://localhost:8501

## 프로젝트 구성

| 파일 | 역할 |
|---|---|
| `dashboard_app.py` | Streamlit 대시보드 메인 |
| `_generate_sample.py` | 샘플 데이터 생성 스크립트 |
| `_join_analysis_duckdb.py` | DuckDB 조인 분석 베이스라인 |
| `_join_analysis.py` | pandas 버전 비교용 |
| `channel_data.csv` | 샘플 채널 광고 raw (합성) |
| `appsflyer_data.csv` | 샘플 AppsFlyer raw (합성) |
| `CLAUDE.md` | 프로젝트 네이밍·지표·관행 문서 |

## 대시보드 구성

6개 탭으로 분석 뷰 제공:

1. **📈 전체 추세** — 일별 광고비 vs 매출, 채널별 ROAS
2. **🎯 목적별** — 캠페인 목적별 효율 비교
3. **🎨 소재 속성** — 소재명 5속성 파싱 기반 분석
4. **🅰️🅱️ A/B 테스트** — A vs B 페어 자동 판정
5. **👥 타겟그룹** — 논타겟/유사/리마/윈백/VIP 비교
6. **🏆 캠페인 랭킹** — 전체 캠페인 효율 순위

## 주요 옵션

- 사이드바에서 기간·채널·캠페인목적·타겟그룹·소재 속성 필터링
- **브랜드KW 제외 토글** (기본 ON, ROAS 부풀림 방지)
- **AF 기준 ↔ 채널 보고 기준** 지표 전환
- 자체 매체(네이버) vs 외부 매체 분리 분석

## 데이터 특성 (샘플)

- 기간: 2025-01-01 ~ 2025-03-31 (Q1)
- 채널: 구글 / 메타 / 네이버
- 캠페인 목적: 플러스가입·첫구매·재구매·리타겟팅·신규유저·룩얼라이크·브랜드KW·일반KW
- 소재 네이밍: `{타입}_{카테고리}_{시즌}_{AB}_{버전}` (예: `VID_플러스멤버십_겨울_A_v2`)
- 어트리뷰션 커버리지: ~80% (실무와 유사)
