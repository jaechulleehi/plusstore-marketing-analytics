"""네이버 플러스 스토어 퍼포먼스 마케팅 대시보드 v2.

CLAUDE.md 규칙 반영 + UI 리뉴얼:
- §3 네이밍 (채널분류·목적·소재 5속성)
- §5 CAC/ROAS = AppsFlyer 기준
- §5-4 ROAS 임계값: 양호 4.0 / 불량 2.0
- §6-1 자체매체 분리·브랜드KW 제외
- §8 DuckDB · plotly · 한국식 축약

v2 개선:
- Pretendard 폰트 + 미니멀/카드 하이브리드 테마
- 🏠 Overview 탭 (자동 인사이트 요약)
- 🔍 Raw 데이터 탭 (검색·정렬·export)
- 주간 WoW delta 표시
- 폴더 기반 자동 병합 (raw/channel/*.csv, raw/appsflyer/*.csv)
"""
from datetime import timedelta
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# Config
# =============================================================================
st.set_page_config(
    page_title="플러스스토어 퍼마 대시보드",
    page_icon=":material/storefront:",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).resolve().parent
CH_GLOB = str(BASE / "raw" / "channel" / "*.csv")
AF_GLOB = str(BASE / "raw" / "appsflyer" / "*.csv")

# CLAUDE.md §3-1
CHANNEL_COLOR = {"구글": "#4285F4", "메타": "#1877F2", "네이버": "#03C75A"}
CHANNEL_MAP_AF = {"구글": "googleadwords_int", "메타": "Facebook Ads",
                  "네이버": "naver_search"}

# §5-4 임계값
ROAS_GOOD = 4.0
ROAS_BAD = 2.0

# §6-4 A/B 최소 노출
AB_MIN_IMPR = 100_000

# 디자인 토큰
COLOR_GREEN = "#03C75A"
COLOR_GREEN_DARK = "#00A641"
COLOR_GOOD = "#10B981"
COLOR_WARN = "#F59E0B"
COLOR_BAD = "#EF4444"
COLOR_GRAY_900 = "#1F2937"
COLOR_GRAY_500 = "#6B7280"
COLOR_GRAY_100 = "#F3F4F6"
COLOR_BORDER = "#E5E7EB"


# =============================================================================
# Custom CSS — Pretendard + 카드 스타일 + 타이포
# =============================================================================
CUSTOM_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css');

/* 텍스트 엘리먼트만 Pretendard. 아이콘 span 은 Streamlit 기본 icon font 유지 */
.stApp, .stMarkdown, .stText, .stCaption,
h1, h2, h3, h4, h5, h6, p, label, li, td, th,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
[data-testid="stMetricDelta"], [data-testid="stDataFrame"] {
    font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont,
                 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
}

/* KPI 카드 - 둥글고 hover 효과 */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 18px 20px;
    transition: border-color .2s, box-shadow .2s;
}
[data-testid="stMetric"]:hover {
    border-color: #03C75A;
    box-shadow: 0 4px 14px rgba(3,199,90,0.08);
}
[data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    color: #1F2937;
    letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    color: #6B7280;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricDelta"] {
    font-size: 0.85rem !important;
    font-weight: 600;
}

/* 일반 컨테이너 카드 */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border-color: #E5E7EB !important;
}

/* 탭 강조 */
[data-testid="stTabs"] button[role="tab"] {
    font-weight: 600;
    font-size: 0.95rem;
    color: #6B7280;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #03C75A;
}

/* 인사이트 배지 */
.insight-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.insight-card .badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 999px;
    margin-right: 8px;
    letter-spacing: 0.02em;
}
.badge-good { background: #DCFCE7; color: #059669; }
.badge-warn { background: #FEF3C7; color: #B45309; }
.badge-bad  { background: #FEE2E2; color: #DC2626; }
.badge-info { background: #DBEAFE; color: #1D4ED8; }

.insight-card .msg {
    font-size: 0.95rem;
    color: #1F2937;
    line-height: 1.5;
}
.insight-card .sub {
    font-size: 0.8rem;
    color: #6B7280;
    margin-top: 4px;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #F7F8FA;
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-weight: 700;
}

/* 섹션 subheader 간격 */
h3 { margin-top: 0.5rem; font-weight: 700; }

/* Streamlit 기본 여백 축소 */
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 포맷 헬퍼
# =============================================================================
def fmt_won(v):
    if v is None or pd.isna(v): return "-"
    if abs(v) >= 1e8: return f"₩{v/1e8:.2f}억"
    if abs(v) >= 1e4: return f"₩{v/1e4:.0f}만"
    return f"₩{v:,.0f}"


def fmt_num(v):
    if v is None or pd.isna(v): return "-"
    if abs(v) >= 1e8: return f"{v/1e8:.2f}억"
    if abs(v) >= 1e4: return f"{v/1e4:.1f}만"
    return f"{v:,.0f}"


def fmt_pct_delta(curr, prev):
    if not prev or pd.isna(prev) or prev == 0:
        return None
    pct = (curr - prev) / prev * 100
    return f"{pct:+.1f}%"


def roas_status(r):
    if r >= ROAS_GOOD: return "🟢 양호", "good"
    if r < ROAS_BAD:   return "🔴 개선 필요", "bad"
    return "🟡 관찰", "warn"


# =============================================================================
# 데이터 로딩 + 소재명 파싱
# =============================================================================
@st.cache_data(ttl=3600, show_spinner="데이터 로딩 중…")
def load_joined() -> pd.DataFrame:
    con = duckdb.connect(":memory:")
    con.execute(f"""
    CREATE VIEW channel AS
    SELECT DISTINCT * FROM read_csv_auto('{CH_GLOB}', union_by_name=true);

    CREATE VIEW appsflyer AS
    SELECT DISTINCT * FROM read_csv_auto('{AF_GLOB}', union_by_name=true);

    CREATE TABLE channel_map (채널 VARCHAR, 미디어소스 VARCHAR);
    INSERT INTO channel_map VALUES
        ('구글', 'googleadwords_int'), ('메타', 'Facebook Ads'),
        ('네이버', 'naver_search');
    """)
    df = con.execute("""
    SELECT c.일, c.채널, c.채널분류, c.캠페인, c.캠페인목적, c.그룹, c.소재,
           c.노출, c.클릭, c.비용,
           c.회원가입 AS 가입_채널, c.구매 AS 구매_채널, c.구매매출 AS 매출_채널,
           a.클릭 AS af_클릭, a.회원가입 AS 가입_AF,
           a.구매 AS 구매_AF, a.구매매출 AS 매출_AF
    FROM channel c
    LEFT JOIN channel_map m ON c.채널 = m.채널
    LEFT JOIN appsflyer a ON a.일 = c.일 AND a.미디어소스 = m.미디어소스
        AND a.캠페인 = c.캠페인 AND a.그룹 = c.그룹 AND a.소재 = c.소재
    """).df()
    con.close()
    df["일"] = pd.to_datetime(df["일"])

    def parse_creative(name: str) -> dict:
        parts = str(name).split("_")
        if len(parts) == 5:
            return dict(소재타입=parts[0], 소재카테고리=parts[1],
                        시즌=parts[2], AB=parts[3], 버전=parts[4])
        if len(parts) == 4:
            return dict(소재타입=parts[0], 소재카테고리=parts[1],
                        시즌=parts[2], AB="없음", 버전=parts[3])
        return dict(소재타입="?", 소재카테고리="?",
                    시즌="?", AB="없음", 버전="?")

    parsed = df["소재"].apply(parse_creative).apply(pd.Series)
    return pd.concat([df, parsed], axis=1)


# =============================================================================
# RFM 세그먼트 데이터 + 색상 (CLAUDE.md §13)
# =============================================================================
# §3-1 브랜드 컬러 일부 + 의미 기반 보조 색상
RFM_COLORS = {
    "Champion":    "#FFB800",   # 골드 — 최고 가치
    "Loyal":       "#03C75A",   # 네이버 그린 (§3-1 브랜드)
    "At-Risk":     "#FF6B6B",   # 위험 빨강
    "Hibernating": "#FF9F43",   # 주황 (At-Risk 변형)
    "Lost":        "#999999",   # 회색
    "New":         "#4285F4",   # 구글 블루 (§3-1 브랜드) — 신규/신선
    "Potential":   "#9775FA",   # 보라 — 실험 풀
}
RFM_SEG_ORDER = ["Champion", "Loyal", "At-Risk", "Hibernating", "Lost", "New", "Potential"]


@st.cache_data(ttl=3600, show_spinner="RFM 세그먼트 로딩 중…")
def load_rfm() -> pd.DataFrame:
    """`outputs/segmented_users.csv` 로드. 없으면 빈 DataFrame 반환."""
    p = Path("outputs/segmented_users.csv")
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, encoding="utf-8-sig")


df_all = load_joined()

# =============================================================================
# Sidebar filters
# =============================================================================
with st.sidebar:
    st.header("필터")

    min_d, max_d = df_all["일"].min().date(), df_all["일"].max().date()
    d_range = st.date_input("기간", (min_d, max_d),
                            min_value=min_d, max_value=max_d)

    st.divider()
    with st.expander("채널 & 캠페인", expanded=True):
        ch_classes = st.multiselect("채널분류", ["외부", "자체"],
                                    default=["외부", "자체"])
        sel_ch = st.multiselect("채널", sorted(df_all["채널"].unique()),
                                default=sorted(df_all["채널"].unique()))
        sel_obj = st.multiselect("캠페인 목적",
                                 sorted(df_all["캠페인목적"].unique()),
                                 default=sorted(df_all["캠페인목적"].unique()))
        sel_grp = st.multiselect("타겟그룹", sorted(df_all["그룹"].unique()),
                                 default=sorted(df_all["그룹"].unique()))

    with st.expander("소재 속성 (§3-3)", expanded=False):
        sel_type = st.multiselect("소재타입",
                                  sorted(df_all["소재타입"].unique()),
                                  default=sorted(df_all["소재타입"].unique()))
        sel_cat = st.multiselect("카테고리",
                                 sorted(df_all["소재카테고리"].unique()),
                                 default=sorted(df_all["소재카테고리"].unique()))
        sel_season = st.multiselect("시즌", sorted(df_all["시즌"].unique()),
                                    default=sorted(df_all["시즌"].unique()))

    st.divider()
    exclude_brand = st.toggle("브랜드KW 제외 (§6-1)", value=True)
    basis = st.radio("지표 기준", ["AF (MMP, 권장)", "채널 보고"], index=0)
    use_af = basis.startswith("AF")

    st.divider()
    st.caption("👥 RFM 세그먼트 (§12-13)")
    snapshot_date = st.date_input(
        "스냅샷 기준일",
        value=pd.Timestamp("2025-03-31").date(),
        help="§12 R/F/M 계산의 기준 시점. 변경 시 segmented_users.csv 재계산 필요.",
    )


# =============================================================================
# Apply filters
# =============================================================================
if not (isinstance(d_range, (tuple, list)) and len(d_range) == 2):
    st.info("📅 시작일·종료일 둘 다 선택해줘.")
    st.stop()
d_from, d_to = d_range

mask = (
    (df_all["일"] >= pd.Timestamp(d_from)) & (df_all["일"] <= pd.Timestamp(d_to))
    & df_all["채널분류"].isin(ch_classes)
    & df_all["채널"].isin(sel_ch)
    & df_all["캠페인목적"].isin(sel_obj)
    & df_all["그룹"].isin(sel_grp)
    & df_all["소재타입"].isin(sel_type)
    & df_all["소재카테고리"].isin(sel_cat)
    & df_all["시즌"].isin(sel_season)
)
if exclude_brand:
    mask &= df_all["캠페인목적"] != "브랜드KW"

df = df_all[mask].copy()
if df.empty:
    st.warning("선택한 필터에 해당하는 데이터가 없어.")
    st.stop()

signup_col = "가입_AF" if use_af else "가입_채널"
revenue_col = "매출_AF" if use_af else "매출_채널"
basis_label = "AF" if use_af else "채널"


# =============================================================================
# 자동 인사이트 생성 (오버뷰 탭용)
# =============================================================================
def generate_insights(df: pd.DataFrame) -> list[dict]:
    """규칙 기반 자동 인사이트."""
    out = []
    if df.empty or len(df["일"].unique()) < 2:
        return out

    # 기간 분할: 뒤쪽 절반 vs 앞쪽 절반 (또는 최근 7일 vs 직전 7일)
    max_d = df["일"].max()
    split = max_d - timedelta(days=7)
    recent = df[df["일"] > split]
    prev_split = split - timedelta(days=7)
    prev = df[(df["일"] <= split) & (df["일"] > prev_split)]

    if recent.empty or prev.empty:
        # 기간 짧으면 전체 평균으로 단순 리포트
        roas_all = (df[revenue_col].sum() / df["비용"].sum()
                    if df["비용"].sum() else 0)
        status, sev = roas_status(roas_all)
        out.append(dict(badge=status, sev=sev,
                        msg=f"전체 기간 ROAS {roas_all:.2f}",
                        sub=f"{basis_label} 기준 · {d_from}~{d_to}"))
        return out

    # 1) ROAS WoW
    r_recent = (recent[revenue_col].sum() / recent["비용"].sum()
                if recent["비용"].sum() else 0)
    r_prev = (prev[revenue_col].sum() / prev["비용"].sum()
              if prev["비용"].sum() else 0)
    delta = (r_recent - r_prev) / r_prev * 100 if r_prev else 0
    if abs(delta) >= 5:
        if delta > 0:
            out.append(dict(badge="▲ 상승", sev="good",
                            msg=f"최근 7일 ROAS {r_recent:.2f} — 직전 7일 대비 {delta:+.1f}%",
                            sub="AF 매출 기반. 효율 개선 중."))
        else:
            out.append(dict(badge="▼ 하락", sev="bad",
                            msg=f"최근 7일 ROAS {r_recent:.2f} — 직전 7일 대비 {delta:+.1f}%",
                            sub="원인 분석 필요. 소재 교체 또는 예산 재분배 검토."))

    # 2) 채널별 최고/최저 ROAS
    ch_sum = df.groupby("채널")[[revenue_col, "비용"]].sum()
    ch_roas = (ch_sum[revenue_col] / ch_sum["비용"].replace(0, pd.NA)).dropna()
    if len(ch_roas) >= 2:
        top_ch = ch_roas.idxmax()
        bot_ch = ch_roas.idxmin()
        out.append(dict(badge="🏆 Top", sev="info",
                        msg=f"{top_ch} ROAS {ch_roas[top_ch]:.2f} — 최고 효율 채널",
                        sub="예산 증액 검토 여지"))
        if ch_roas[bot_ch] < ROAS_BAD:
            out.append(dict(badge="⚠️ 주의", sev="warn",
                            msg=f"{bot_ch} ROAS {ch_roas[bot_ch]:.2f} — 임계값 {ROAS_BAD} 미만",
                            sub="소재 리프레시 또는 일시중단 검토"))

    # 3) 비용 스파이크 (최근 3일 평균 vs 이전 평균)
    daily_spend = df.groupby("일")["비용"].sum().sort_index()
    if len(daily_spend) >= 7:
        recent3 = daily_spend.tail(3).mean()
        prior = daily_spend.head(len(daily_spend) - 3).mean()
        if prior > 0:
            spike = (recent3 - prior) / prior * 100
            if abs(spike) >= 30:
                sev = "warn" if spike > 0 else "info"
                icon = "📈" if spike > 0 else "📉"
                out.append(dict(badge=f"{icon} 비용", sev=sev,
                                msg=f"최근 3일 평균 광고비 {fmt_won(recent3)} — 평시 대비 {spike:+.0f}%",
                                sub="캠페인 증설 또는 pause 확인"))

    # 4) 어트리뷰션 커버리지 이상치
    cov = (df["가입_AF"].sum() / df["가입_채널"].sum() * 100
           if df["가입_채널"].sum() else 0)
    if cov < 70:
        out.append(dict(badge="AF 커버리지", sev="warn",
                        msg=f"AppsFlyer 커버리지 {cov:.1f}% — 70% 미만",
                        sub="SKAdNetwork·네이버 로그인 기여 누락 확인"))
    elif cov > 95:
        out.append(dict(badge="AF 커버리지", sev="info",
                        msg=f"AppsFlyer 커버리지 {cov:.1f}% — 비정상적으로 높음",
                        sub="채널 보고 누락 가능성"))

    return out[:5]  # 최대 5개


# =============================================================================
# Header
# =============================================================================
st.title("🛒 플러스스토어 퍼마 대시보드")
notes = []
if exclude_brand: notes.append("브랜드KW 제외")
if len(ch_classes) < 2: notes.append(f"채널분류: {', '.join(ch_classes)}")
st.caption(
    f"📅 {d_from} ~ {d_to}  ·  📊 {len(df):,}행  ·  📐 기준: **{basis_label}**"
    + (f"  ·  ⚙️ {' / '.join(notes)}" if notes else "")
)


# =============================================================================
# KPI row (WoW delta 포함)
# =============================================================================
def compute_kpis(df: pd.DataFrame) -> dict:
    return dict(
        spend=df["비용"].sum(),
        impr=df["노출"].sum(),
        click=df["클릭"].sum(),
        signup=df[signup_col].sum(),
        revenue=df[revenue_col].sum(),
    )


k = compute_kpis(df)
ctr = (k["click"] / k["impr"] * 100) if k["impr"] else 0
cac = (k["spend"] / k["signup"]) if k["signup"] else 0
roas = (k["revenue"] / k["spend"]) if k["spend"] else 0
af_cov = (df["가입_AF"].sum() / df["가입_채널"].sum() * 100
          if df["가입_채널"].sum() else 0)

# WoW 비교: 최근 7일 vs 직전 7일 (전체 기간이 14일 이상일 때만 의미)
max_date = df["일"].max()
min_date_in_df = df["일"].min()
delta_roas = None
delta_cac = None
delta_spend = None
if (max_date - min_date_in_df).days >= 14:
    split_date = max_date - timedelta(days=7)
    prev_start = split_date - timedelta(days=7)
    df_recent = df[df["일"] > split_date]
    df_prev = df[(df["일"] <= split_date) & (df["일"] > prev_start)]
    if not df_prev.empty and not df_recent.empty:
        kr = compute_kpis(df_recent)
        kp = compute_kpis(df_prev)
        rr = kr["revenue"] / kr["spend"] if kr["spend"] else 0
        rp = kp["revenue"] / kp["spend"] if kp["spend"] else 0
        delta_roas = fmt_pct_delta(rr, rp)
        cr = kr["spend"] / kr["signup"] if kr["signup"] else 0
        cp = kp["spend"] / kp["signup"] if kp["signup"] else 0
        delta_cac = fmt_pct_delta(cr, cp)
        delta_spend = fmt_pct_delta(kr["spend"], kp["spend"])

with st.container(horizontal=True):
    st.metric("총 광고비", fmt_won(k["spend"]), delta=delta_spend,
              delta_color="off")
    st.metric("노출", fmt_num(k["impr"]))
    st.metric("CTR", f"{ctr:.2f}%")
    st.metric(f"가입 ({basis_label})", fmt_num(k["signup"]))
    st.metric(f"CAC ({basis_label})", fmt_won(cac), delta=delta_cac,
              delta_color="inverse")
    st.metric(f"ROAS ({basis_label})", f"{roas:.2f}", delta=delta_roas,
              delta_color="normal")
    st.metric("AF 커버리지", f"{af_cov:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# Tabs
# =============================================================================
tab_home, tab_trend, tab_obj, tab_creative, tab_ab, tab_group, tab_rank, tab_rfm, tab_raw = st.tabs([
    "🏠 Overview",
    "📈 전체 추세",
    "🎯 목적별",
    "🎨 소재 속성",
    "🅰️🅱️ A/B",
    "👤 타겟그룹",
    "🏆 랭킹",
    "👥 RFM 세그먼트",
    "🔍 Raw 데이터",
])

# -----------------------------------------------------------------------------
# 🏠 Overview — 자동 인사이트 + 핵심 요약
# -----------------------------------------------------------------------------
with tab_home:
    left, right = st.columns([2, 3], gap="large")

    with left:
        st.subheader("💡 자동 인사이트")
        insights = generate_insights(df)
        if not insights:
            st.info("인사이트를 뽑기엔 기간이 짧아. 더 많은 일자가 필요해.")
        for ins in insights:
            badge_cls = {
                "good": "badge-good", "bad": "badge-bad",
                "warn": "badge-warn", "info": "badge-info"
            }.get(ins["sev"], "badge-info")
            st.markdown(f"""
            <div class="insight-card">
              <span class="badge {badge_cls}">{ins['badge']}</span>
              <span class="msg">{ins['msg']}</span>
              <div class="sub">{ins['sub']}</div>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.subheader("📊 채널별 스냅샷")
        ch_kpi = df.groupby(["채널", "채널분류"]).agg(
            비용=("비용", "sum"), 매출=(revenue_col, "sum"),
            가입=(signup_col, "sum"),
        ).reset_index()
        ch_kpi["ROAS"] = ch_kpi["매출"] / ch_kpi["비용"].replace(0, pd.NA)
        ch_kpi["CAC"] = ch_kpi["비용"] / ch_kpi["가입"].replace(0, pd.NA)

        def render_ch_card(r):
            color = CHANNEL_COLOR.get(r["채널"], "#888")
            tag = "자체" if r["채널분류"] == "자체" else "외부"
            status, _ = roas_status(r["ROAS"]) if not pd.isna(r["ROAS"]) else ("-", "info")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.markdown(
                    f"<div style='font-weight:700;font-size:1.05rem;color:{color};"
                    f"border-left:3px solid {color};padding-left:8px'>"
                    f"{r['채널']}</div>"
                    f"<div style='color:#6B7280;font-size:0.8rem;"
                    f"padding-left:11px'>{tag} 매체</div>",
                    unsafe_allow_html=True)
                c2.metric("ROAS", f"{r['ROAS']:.2f}" if not pd.isna(r["ROAS"]) else "-")
                c3.metric("CAC", fmt_won(r["CAC"]))
                c4.markdown(f"<div style='margin-top:18px'>{status}</div>",
                            unsafe_allow_html=True)

        # §6-1: 외부와 자체 분리 표기
        ext = ch_kpi[ch_kpi["채널분류"] == "외부"].sort_values("ROAS", ascending=False)
        own = ch_kpi[ch_kpi["채널분류"] == "자체"].sort_values("ROAS", ascending=False)

        if not ext.empty:
            st.caption("외부 매체")
            for _, r in ext.iterrows(): render_ch_card(r)
        if not own.empty:
            st.caption("자체 매체 (외부 비교에서 분리, §6-1)")
            for _, r in own.iterrows(): render_ch_card(r)

    st.divider()

    # 빠른 시계열 요약
    with st.container(border=True):
        st.subheader("📅 일별 요약")
        daily = df.groupby("일").agg(
            비용=("비용", "sum"), 매출=(revenue_col, "sum"),
            가입=(signup_col, "sum"),
        ).reset_index()
        daily["ROAS"] = daily["매출"] / daily["비용"]

        fig = go.Figure()
        fig.add_bar(x=daily["일"], y=daily["비용"], name="광고비",
                    marker_color="#E5E7EB", yaxis="y")
        fig.add_scatter(x=daily["일"], y=daily["매출"], name="매출",
                        mode="lines",
                        line=dict(color=COLOR_GREEN, width=2.5), yaxis="y2")
        fig.update_layout(
            height=340, margin=dict(l=10, r=10, t=20, b=10),
            yaxis=dict(title="광고비(₩)", showgrid=False),
            yaxis2=dict(title="매출(₩)", overlaying="y", side="right",
                        showgrid=True, gridcolor="#F3F4F6"),
            legend=dict(orientation="h", y=1.1),
            hovermode="x unified",
            plot_bgcolor="white",
        )
        st.plotly_chart(fig, width='stretch')


# -----------------------------------------------------------------------------
# 📈 전체 추세
# -----------------------------------------------------------------------------
with tab_trend:
    col_ts, col_ch = st.columns([3, 2])

    with col_ts:
        with st.container(border=True):
            st.subheader("일별 광고비 vs 매출 (채널별)")
            daily = df.groupby(["일", "채널"]).agg(
                비용=("비용", "sum"), 매출=(revenue_col, "sum"),
            ).reset_index()
            fig = go.Figure()
            daily_spend = daily.groupby("일")["비용"].sum().reset_index()
            fig.add_bar(x=daily_spend["일"], y=daily_spend["비용"],
                        name="광고비(₩)", marker_color="#E5E7EB",
                        opacity=0.8, yaxis="y")
            for ch in sorted(daily["채널"].unique()):
                sub = daily[daily["채널"] == ch]
                fig.add_scatter(
                    x=sub["일"], y=sub["매출"], name=f"{ch} 매출",
                    mode="lines",
                    line=dict(color=CHANNEL_COLOR.get(ch, "#888"), width=2.2),
                    yaxis="y2")
            fig.update_layout(
                height=420, margin=dict(l=10, r=10, t=30, b=10),
                yaxis=dict(title="광고비"),
                yaxis2=dict(title="매출", overlaying="y", side="right"),
                legend=dict(orientation="h", y=1.12),
                hovermode="x unified", plot_bgcolor="white")
            st.plotly_chart(fig, width='stretch')

    with col_ch:
        with st.container(border=True):
            st.subheader("채널별 ROAS")
            by_ch = df.groupby(["채널", "채널분류"]).agg(
                비용=("비용", "sum"), 매출=(revenue_col, "sum"),
            ).reset_index()
            by_ch["ROAS"] = by_ch["매출"] / by_ch["비용"].replace(0, pd.NA)
            by_ch = by_ch.dropna(subset=["ROAS"]).sort_values("ROAS", ascending=True)

            fig = go.Figure()
            fig.add_bar(
                x=by_ch["ROAS"], y=by_ch["채널"], orientation="h",
                marker=dict(
                    color=[CHANNEL_COLOR.get(c, "#888") for c in by_ch["채널"]],
                    pattern=dict(
                        shape=["/" if cls == "자체" else ""
                               for cls in by_ch["채널분류"]]),
                ),
                text=[f"{v:.2f}" for v in by_ch["ROAS"]],
                textposition="outside",
            )
            fig.add_vline(x=ROAS_GOOD, line_dash="dash", line_color=COLOR_GOOD)
            fig.add_vline(x=ROAS_BAD, line_dash="dash", line_color=COLOR_BAD)
            fig.update_layout(
                height=420, margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title=f"ROAS ({basis_label})",
                plot_bgcolor="white", showlegend=False)
            st.plotly_chart(fig, width='stretch')


# -----------------------------------------------------------------------------
# 🎯 목적별
# -----------------------------------------------------------------------------
with tab_obj:
    st.caption("§3-2 캠페인 목적별 효율 비교 — 예산 재분배 의사결정 근거")
    by_obj = df.groupby("캠페인목적").agg(
        비용=("비용", "sum"), 가입=(signup_col, "sum"),
        매출=(revenue_col, "sum"), 노출=("노출", "sum"),
    ).reset_index()
    by_obj["ROAS"] = (by_obj["매출"] / by_obj["비용"].replace(0, pd.NA)).round(2)
    by_obj["CAC"] = (by_obj["비용"] / by_obj["가입"].replace(0, pd.NA)).round(0)
    by_obj["비용비중(%)"] = (by_obj["비용"] / by_obj["비용"].sum() * 100).round(1)
    by_obj["매출비중(%)"] = (by_obj["매출"] / by_obj["매출"].sum() * 100).round(1)
    by_obj = by_obj.sort_values("ROAS", ascending=False)

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.subheader("목적별 ROAS")
        fig = px.bar(by_obj, x="ROAS", y="캠페인목적", orientation="h",
                     color="ROAS", color_continuous_scale="RdYlGn",
                     color_continuous_midpoint=ROAS_GOOD, text="ROAS")
        fig.add_vline(x=ROAS_GOOD, line_dash="dash", line_color=COLOR_GOOD)
        fig.add_vline(x=ROAS_BAD, line_dash="dash", line_color=COLOR_BAD)
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10),
                          coloraxis_showscale=False, yaxis_title=None,
                          plot_bgcolor="white")
        st.plotly_chart(fig, width='stretch')

    with c2, st.container(border=True):
        st.subheader("비용 배분 vs 매출 배분")
        fig = go.Figure()
        fig.add_bar(x=by_obj["캠페인목적"], y=by_obj["비용비중(%)"],
                    name="비용 비중(%)", marker_color="#F59E0B")
        fig.add_bar(x=by_obj["캠페인목적"], y=by_obj["매출비중(%)"],
                    name="매출 비중(%)", marker_color=COLOR_GREEN)
        fig.update_layout(barmode="group", height=420,
                          margin=dict(l=10, r=10, t=30, b=10),
                          legend=dict(orientation="h", y=1.15),
                          plot_bgcolor="white")
        st.plotly_chart(fig, width='stretch')

    with st.container(border=True):
        st.subheader("목적별 상세")
        st.dataframe(
            by_obj[["캠페인목적", "비용", "비용비중(%)", "가입", "CAC", "매출", "ROAS"]],
            hide_index=True, width='stretch',
            column_config={
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "CAC": st.column_config.NumberColumn(format="₩%d"),
                "매출": st.column_config.NumberColumn(format="₩%d"),
                "ROAS": st.column_config.ProgressColumn(
                    "ROAS", format="%.2f", min_value=0,
                    max_value=float(by_obj["ROAS"].max() * 1.1)),
            })


# -----------------------------------------------------------------------------
# 🎨 소재 속성
# -----------------------------------------------------------------------------
with tab_creative:
    st.caption("§3-3 소재명 파싱 기반 분석")

    c1, c2, c3 = st.columns(3)

    def agg_by(col: str, label: str):
        g = df.groupby(col).agg(비용=("비용", "sum"),
                                매출=(revenue_col, "sum")).reset_index()
        g["ROAS"] = (g["매출"] / g["비용"]).round(2)
        return g.sort_values("ROAS", ascending=False)

    for col_st, col_key, title in [
        (c1, "소재타입", "소재타입별"),
        (c2, "소재카테고리", "카테고리별"),
        (c3, "시즌", "시즌별"),
    ]:
        with col_st, st.container(border=True):
            st.subheader(title)
            g = agg_by(col_key, title)
            fig = px.bar(
                g, x="ROAS", y=col_key, orientation="h",
                color="ROAS", color_continuous_scale="RdYlGn",
                color_continuous_midpoint=ROAS_GOOD, text="ROAS")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=360, margin=dict(l=5, r=5, t=10, b=10),
                              yaxis=dict(title=None, autorange="reversed"),
                              coloraxis_showscale=False, plot_bgcolor="white")
            st.plotly_chart(fig, width='stretch')

    with st.container(border=True):
        st.subheader("카테고리 × 소재타입 ROAS")
        pivot_rev = df.pivot_table(index="소재카테고리", columns="소재타입",
                                   values=revenue_col, aggfunc="sum", fill_value=0)
        pivot_spend = df.pivot_table(index="소재카테고리", columns="소재타입",
                                     values="비용", aggfunc="sum", fill_value=0)
        pivot_roas = (pivot_rev / pivot_spend.replace(0, pd.NA)).round(2)
        fig = px.imshow(pivot_roas, text_auto=".2f",
                        color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=ROAS_GOOD, aspect="auto")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10),
                          coloraxis_colorbar=dict(title="ROAS"))
        st.plotly_chart(fig, width='stretch')


# -----------------------------------------------------------------------------
# 🅰️🅱️ A/B 테스트
# -----------------------------------------------------------------------------
with tab_ab:
    st.caption(
        f"§6-4 A/B 테스트 — 최소 노출 {AB_MIN_IMPR:,} 필요. "
        "같은 (채널, 캠페인, 카테고리, 시즌) 내 A vs B 비교."
    )

    ab = df[df["AB"].isin(["A", "B"])].copy()
    grouping = ["채널", "캠페인목적", "소재카테고리", "시즌"]
    pair = ab.groupby(grouping + ["AB"]).agg(
        노출=("노출", "sum"), 클릭=("클릭", "sum"),
        가입=(signup_col, "sum"), 매출=(revenue_col, "sum"),
        비용=("비용", "sum"),
    ).reset_index()

    wide = pair.pivot_table(
        index=grouping, columns="AB",
        values=["노출", "클릭", "가입", "매출", "비용"],
    ).reset_index()
    # MultiIndex 평탄화 (NaN·빈 문자열 모두 안전)
    wide.columns = [
        f"{m}_{l}" if (isinstance(l, str) and l) else m
        for m, l in wide.columns
    ]

    required_cols = ["노출_A", "노출_B", "클릭_A", "클릭_B",
                     "비용_A", "비용_B", "매출_A", "매출_B"]
    missing = [c for c in required_cols if c not in wide.columns]
    rows = []
    if missing:
        st.info(
            "현재 필터 조건에 A·B 양쪽 데이터가 모두 있는 페어가 없어. "
            f"(누락 컬럼: {', '.join(missing)}) 필터를 넓혀봐."
        )
        wide = wide.iloc[0:0]  # empty, skip loop safely
    else:
        wide = wide.dropna(subset=required_cols)
        wide = wide[(wide["비용_A"] > 0) & (wide["비용_B"] > 0)
                    & (wide["노출_A"] > 0) & (wide["노출_B"] > 0)]

    for _, r in wide.iterrows():
        roas_a = r["매출_A"] / r["비용_A"]
        roas_b = r["매출_B"] / r["비용_B"]
        ctr_a = r["클릭_A"] / r["노출_A"] * 100
        ctr_b = r["클릭_B"] / r["노출_B"] * 100
        total_impr = r["노출_A"] + r["노출_B"]
        enough = total_impr >= AB_MIN_IMPR
        winner = "A" if roas_a > roas_b else ("B" if roas_b > roas_a else "tie")
        rows.append({
            "채널": r["채널"], "목적": r["캠페인목적"],
            "카테고리": r["소재카테고리"], "시즌": r["시즌"],
            "노출합": int(total_impr),
            "CTR_A(%)": round(ctr_a, 2), "CTR_B(%)": round(ctr_b, 2),
            "ROAS_A": round(roas_a, 2), "ROAS_B": round(roas_b, 2),
            "Δ ROAS": round(roas_b - roas_a, 2),
            "샘플충분": "✓" if enough else "✗",
            "우세": winner,
        })

    if not rows:
        st.info("A/B 페어가 없어. 필터 조건을 완화해봐.")
    else:
        ab_df = pd.DataFrame(rows).sort_values("Δ ROAS", key=abs, ascending=False)
        c1, c2 = st.columns(2)
        c1.metric("A/B 페어 총수", len(ab_df))
        c2.metric("샘플 충분 페어",
                  f"{(ab_df['샘플충분'] == '✓').sum()} / {len(ab_df)}")

        with st.container(border=True):
            st.subheader("ROAS 차이 Top")
            ok = ab_df[ab_df["샘플충분"] == "✓"].head(15)
            if not ok.empty:
                fig = go.Figure()
                labels = (ok["채널"] + " / " + ok["카테고리"] + " / " + ok["시즌"]).tolist()
                fig.add_bar(x=ok["ROAS_A"], y=labels, orientation="h",
                            name="A", marker_color="#6BAED6")
                fig.add_bar(x=ok["ROAS_B"], y=labels, orientation="h",
                            name="B", marker_color="#FD8D3C")
                fig.update_layout(
                    barmode="group", height=500,
                    margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", y=1.08),
                    plot_bgcolor="white")
                st.plotly_chart(fig, width='stretch')

        with st.container(border=True):
            st.subheader("A/B 전체 표")
            st.dataframe(ab_df, hide_index=True, width='stretch')


# -----------------------------------------------------------------------------
# 👥 타겟그룹
# -----------------------------------------------------------------------------
with tab_group:
    by_grp = df.groupby("그룹").agg(
        비용=("비용", "sum"), 가입=(signup_col, "sum"),
        매출=(revenue_col, "sum"), 노출=("노출", "sum"),
    ).reset_index()
    by_grp["ROAS"] = (by_grp["매출"] / by_grp["비용"].replace(0, pd.NA)).round(2)
    by_grp["CAC"] = (by_grp["비용"] / by_grp["가입"].replace(0, pd.NA)).round(0)

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.subheader("그룹별 ROAS")
        fig = px.bar(by_grp.sort_values("ROAS"), x="ROAS", y="그룹",
                     orientation="h", color="ROAS",
                     color_continuous_scale="RdYlGn",
                     color_continuous_midpoint=ROAS_GOOD, text="ROAS")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10),
                          coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig, width='stretch')

    with c2, st.container(border=True):
        st.subheader("그룹별 CAC")
        grp_sorted = by_grp.sort_values("CAC")
        fig = px.bar(grp_sorted, x="CAC", y="그룹", orientation="h",
                     color="CAC", color_continuous_scale="RdYlGn_r",
                     text=grp_sorted["CAC"].apply(fmt_won))
        fig.update_traces(textposition="outside")
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10),
                          coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig, width='stretch')

    with st.container(border=True):
        st.dataframe(
            by_grp[["그룹", "비용", "노출", "가입", "CAC", "매출", "ROAS"]],
            hide_index=True, width='stretch',
            column_config={
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "CAC": st.column_config.NumberColumn(format="₩%d"),
                "매출": st.column_config.NumberColumn(format="₩%d"),
            })


# -----------------------------------------------------------------------------
# 🏆 랭킹
# -----------------------------------------------------------------------------
with tab_rank:
    rank = df.groupby(["채널", "채널분류", "캠페인목적", "캠페인"]).agg(
        비용=("비용", "sum"), 클릭=("클릭", "sum"), 노출=("노출", "sum"),
        가입=(signup_col, "sum"), 매출=(revenue_col, "sum"),
    ).reset_index()
    rank["CTR(%)"] = (rank["클릭"] / rank["노출"].replace(0, pd.NA) * 100).round(2)
    rank["CAC"] = (rank["비용"] / rank["가입"].replace(0, pd.NA)).round(0)
    rank["ROAS"] = (rank["매출"] / rank["비용"].replace(0, pd.NA)).round(2)
    rank["상태"] = rank["ROAS"].apply(
        lambda r: "🟢 양호" if r >= ROAS_GOOD
        else ("🔴 개선 필요" if r < ROAS_BAD else "🟡 관찰"))
    rank = rank.sort_values("ROAS", ascending=False)[
        ["채널분류", "채널", "캠페인목적", "캠페인", "비용", "노출", "클릭",
         "CTR(%)", "가입", "CAC", "매출", "ROAS", "상태"]]

    with st.container(border=True):
        st.dataframe(
            rank, hide_index=True, width='stretch',
            column_config={
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "CAC": st.column_config.NumberColumn(format="₩%d"),
                "매출": st.column_config.NumberColumn(format="₩%d"),
                "ROAS": st.column_config.ProgressColumn(
                    "ROAS", format="%.2f", min_value=0,
                    max_value=float(rank["ROAS"].max() * 1.1)),
            })


# -----------------------------------------------------------------------------
# 👥 RFM 세그먼트 (CLAUDE.md §12-13)
# -----------------------------------------------------------------------------
with tab_rfm:
    df_rfm = load_rfm()

    if df_rfm.empty:
        st.warning(
            "🚨 `outputs/segmented_users.csv` 가 없어. "
            "RFM 분류부터 실행해줘 (§12-13 기준)."
        )
        st.code(
            "# Claude Code 에 다음 프롬프트 실행:\n"
            '"users_2025-03-31.csv 와 purchases_2025-Q1.csv 보고\n'
            ' CLAUDE.md 기준으로 RFM 점수 + 세그먼트 분류 해줘.\n'
            ' 결과를 outputs/segmented_users.csv 로 저장해줘."',
            language="bash",
        )
    else:
        st.caption(
            f"📅 스냅샷 기준일: **{snapshot_date}** · "
            f"{len(df_rfm):,}명 · CLAUDE.md §12-13 적용"
        )

        # ===== KPI 카드 =====
        seg_counts_kpi = df_rfm["segment"].value_counts()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("전체", fmt_num(len(df_rfm)))
        c2.metric("Champion 🥇", fmt_num(seg_counts_kpi.get("Champion", 0)))
        c3.metric("Loyal 🟢", fmt_num(seg_counts_kpi.get("Loyal", 0)))
        c4.metric("At-Risk 🔴", fmt_num(seg_counts_kpi.get("At-Risk", 0)))
        c5.metric("평균 RFM", f"{df_rfm['RFM_total'].mean():.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ===== 1. 파이차트 + 2. 히트맵 =====
        col_pie, col_heat = st.columns([1, 1.2], gap="large")

        with col_pie:
            st.markdown("**🥧 세그먼트 분포 파이차트**")
            seg_counts = df_rfm["segment"].value_counts()
            pie_colors = [RFM_COLORS.get(s, "#cccccc") for s in seg_counts.index]
            fig_pie = go.Figure(data=[go.Pie(
                labels=seg_counts.index,
                values=seg_counts.values,
                marker=dict(colors=pie_colors, line=dict(color='white', width=2)),
                hole=0.4,
                textinfo='label+percent',
                textposition='outside',
                pull=[0.05 if s == "Champion" else 0 for s in seg_counts.index],
            )])
            fig_pie.update_layout(
                height=420,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(orientation='v', x=1.02, y=0.5, font=dict(size=11)),
                annotations=[dict(text=f'{len(df_rfm):,}명', x=0.5, y=0.5,
                                  font=dict(size=18, color='#333'), showarrow=False)],
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_heat:
            st.markdown("**🔥 R × F_recent 히트맵 (셀 = M 평균)**")
            heat_m = df_rfm.groupby(["R", "F_recent"])["M"].mean().unstack(fill_value=0)
            heat_m = heat_m.reindex(index=[5, 4, 3, 2, 1],
                                    columns=[1, 2, 3, 4, 5], fill_value=0)
            heat_n = df_rfm.groupby(["R", "F_recent"]).size().unstack(fill_value=0)
            heat_n = heat_n.reindex(index=[5, 4, 3, 2, 1],
                                    columns=[1, 2, 3, 4, 5], fill_value=0)
            text_combined = [
                [f"M={heat_m.values[i, j]:.1f}<br>n={heat_n.values[i, j]:,}"
                 for j in range(heat_m.shape[1])]
                for i in range(heat_m.shape[0])
            ]
            fig_heat = go.Figure(data=go.Heatmap(
                z=heat_m.values,
                x=[f"F={c}" for c in heat_m.columns],
                y=[f"R={r}" for r in heat_m.index],
                colorscale='YlOrRd',
                text=text_combined,
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="M 평균", thickness=12),
                hovertemplate='%{y} × %{x}<br>%{text}<extra></extra>',
            ))
            fig_heat.update_layout(
                height=420,
                margin=dict(t=10, b=20, l=40, r=40),
                xaxis=dict(side='bottom'),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ===== 3. 3D 스캐터 =====
        st.markdown("**🌐 3D 스캐터 — R × F_recent × M (세그먼트별 색)**")
        st.caption(
            "🖱️ 회전·확대 가능 · 성능 위해 1,500명 샘플링 (전체 "
            f"{len(df_rfm):,}명)"
        )
        df_sample = df_rfm.sample(min(1500, len(df_rfm)), random_state=42)
        # 약간의 jitter 로 점 겹침 완화 (정수 격자라 기본은 모두 겹침)
        import numpy as _np
        jitter = _np.random.default_rng(42)
        df_sample = df_sample.assign(
            R_j=df_sample["R"] + jitter.uniform(-0.2, 0.2, len(df_sample)),
            F_j=df_sample["F_recent"] + jitter.uniform(-0.2, 0.2, len(df_sample)),
            M_j=df_sample["M"] + jitter.uniform(-0.2, 0.2, len(df_sample)),
        )
        fig_3d = px.scatter_3d(
            df_sample,
            x="R_j", y="F_j", z="M_j",
            color="segment",
            color_discrete_map=RFM_COLORS,
            category_orders={"segment": RFM_SEG_ORDER},
            hover_data={
                "external_id": True, "R": True, "F_recent": True, "M": True,
                "RFM_total": True, "M_amount": ":,.0f",
                "R_j": False, "F_j": False, "M_j": False,
            },
            opacity=0.75,
            height=620,
        )
        fig_3d.update_traces(marker=dict(size=4, line=dict(width=0)))
        fig_3d.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            scene=dict(
                xaxis=dict(title="R (Recency)", range=[0.5, 5.5]),
                yaxis=dict(title="F_recent (Frequency)", range=[0.5, 5.5]),
                zaxis=dict(title="M (Monetary)", range=[0.5, 5.5]),
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)),
            ),
            legend=dict(title="세그먼트", font=dict(size=11)),
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ===== 4. 세그먼트별 다운로드 =====
        st.markdown("**📥 세그먼트별 CSV 다운로드**")
        st.caption(
            "각 세그먼트별 user 목록 다운로드 → Braze Canvas 타겟 업로드용. "
            "1차 액션 톤은 §13 매트릭스 따름."
        )
        dl_cols = st.columns(len(RFM_SEG_ORDER))
        for col, seg in zip(dl_cols, RFM_SEG_ORDER):
            with col:
                sub = df_rfm[df_rfm["segment"] == seg]
                count = len(sub)
                seg_color = RFM_COLORS.get(seg, "#cccccc")
                st.markdown(
                    f"<div style='border-left: 4px solid {seg_color}; "
                    f"padding-left: 8px; margin-bottom: 4px;'>"
                    f"<b style='color:{seg_color};'>{seg}</b><br>"
                    f"<span style='font-size:1.2rem; font-weight:bold;'>{count:,}</span>"
                    f"<span style='color:#888; font-size:0.85rem;'> 명</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if count > 0:
                    csv_data = sub.to_csv(index=False, encoding="utf-8-sig"
                                          ).encode("utf-8-sig")
                    st.download_button(
                        "📥 CSV",
                        data=csv_data,
                        file_name=f"segment_{seg}_{snapshot_date}.csv",
                        mime="text/csv",
                        key=f"dl_seg_{seg}",
                        use_container_width=True,
                    )
                else:
                    st.caption("_없음_")

        # 전체 다운로드
        st.markdown("---")
        all_csv = df_rfm.to_csv(index=False, encoding="utf-8-sig"
                                ).encode("utf-8-sig")
        st.download_button(
            "📥 전체 segmented_users.csv 다운로드",
            data=all_csv,
            file_name=f"segmented_users_{snapshot_date}.csv",
            mime="text/csv",
            type="primary",
        )


# -----------------------------------------------------------------------------
# 🔍 Raw 데이터
# -----------------------------------------------------------------------------
with tab_raw:
    st.caption(
        f"조인된 raw 데이터 · {len(df):,}행 · "
        "모든 컬럼 정렬·필터 가능 · 다운로드는 오른쪽 위 ⋮ 메뉴"
    )

    # 검색 박스
    search = st.text_input(
        "🔍 검색 (캠페인·소재·채널·목적 등 텍스트 컬럼 대상)",
        placeholder="예: 플러스가입, VID_플러스멤버십, META_CMP_02",
    )

    display_cols = [
        "일", "채널", "채널분류", "캠페인", "캠페인목적", "그룹",
        "소재", "소재타입", "소재카테고리", "시즌", "AB",
        "노출", "클릭", "비용",
        "가입_채널", "가입_AF", "매출_채널", "매출_AF",
    ]
    df_show = df[display_cols].copy()

    if search:
        text_cols = ["채널", "캠페인", "캠페인목적", "그룹", "소재",
                     "소재타입", "소재카테고리", "시즌"]
        mask_search = pd.Series(False, index=df_show.index)
        for c in text_cols:
            mask_search |= df_show[c].astype(str).str.contains(
                search, case=False, na=False, regex=False)
        df_show = df_show[mask_search]

    c1, c2, c3 = st.columns(3)
    c1.metric("표시 행수", f"{len(df_show):,}")
    c2.metric("총 광고비 (필터 후)", fmt_won(df_show["비용"].sum()))
    c3.metric("유니크 캠페인", df_show["캠페인"].nunique())

    with st.container(border=True):
        st.dataframe(
            df_show,
            hide_index=True,
            width='stretch',
            height=560,
            column_config={
                "일": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "노출": st.column_config.NumberColumn(format="%d"),
                "클릭": st.column_config.NumberColumn(format="%d"),
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "가입_채널": st.column_config.NumberColumn(format="%d"),
                "가입_AF": st.column_config.NumberColumn(format="%d"),
                "매출_채널": st.column_config.NumberColumn(format="₩%d"),
                "매출_AF": st.column_config.NumberColumn(format="₩%d"),
            })

    # Download
    csv_bytes = df_show.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "📥 현재 뷰 CSV 다운로드",
        data=csv_bytes,
        file_name=f"raw_filtered_{d_from}_{d_to}.csv",
        mime="text/csv",
    )


# =============================================================================
# Footer
# =============================================================================
st.markdown(
    f"<div style='text-align:center; color:#9CA3AF; font-size:0.8rem; "
    f"margin-top: 2rem; padding: 1rem;'>"
    f"📌 CLAUDE.md §3·5·6 반영  ·  ROAS 임계값: 🟢 ≥{ROAS_GOOD} / 🔴 &lt;{ROAS_BAD} "
    f"·  A/B 최소노출: {AB_MIN_IMPR:,}  ·  "
    f"지표 기준: AppsFlyer 샘플의 단일 구매매출 (D7 상정)"
    f"</div>",
    unsafe_allow_html=True,
)
