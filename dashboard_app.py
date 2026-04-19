"""네이버 플러스 스토어 퍼포먼스 마케팅 대시보드.

CLAUDE.md 규칙 반영:
- §3-1 채널 매핑 + 외부/자체 분류
- §3-2 캠페인 목적 분류
- §3-3 소재명 5속성 파싱 ({타입}_{카테고리}_{시즌}_{AB}_{버전})
- §3-4 타겟그룹 (논타겟/유사/리마/윈백/VIP)
- §5 CAC/ROAS = AppsFlyer 기준
- §5-4 ROAS 임계값: 양호 4.0 / 불량 2.0
- §6-1 자체매체 분리, 브랜드KW 제외 옵션
- §6-4 A/B 테스트 최소 샘플 10만 노출
- §8 DuckDB 조인, plotly 시각화, 한국식 축약 포맷
"""
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="플러스스토어 퍼마 대시보드",
    page_icon=":material/trending_up:",
    layout="wide",
)

BASE = Path(__file__).resolve().parent
CH_CSV = BASE / "channel_data.csv"
AF_CSV = BASE / "appsflyer_data.csv"

# CLAUDE.md §3-1
CHANNEL_COLOR = {"구글": "#4285F4", "메타": "#1877F2", "네이버": "#03C75A"}
CHANNEL_MAP_AF = {"구글": "googleadwords_int", "메타": "Facebook Ads",
                  "네이버": "naver_search"}

# §5-4 임계값
ROAS_GOOD = 4.0
ROAS_BAD = 2.0

# §6-4 A/B 테스트 최소 샘플
AB_MIN_IMPR = 100_000


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


# =============================================================================
# 데이터 로딩: DuckDB 조인 + 소재명 파싱
# =============================================================================
@st.cache_data(ttl=3600)
def load_joined() -> pd.DataFrame:
    con = duckdb.connect(":memory:")
    con.execute(f"""
    CREATE VIEW channel AS SELECT * FROM read_csv_auto('{CH_CSV}');
    CREATE VIEW appsflyer AS SELECT * FROM read_csv_auto('{AF_CSV}');
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

    # §3-3 소재명 5속성 파싱
    # 포맷: {타입}_{카테고리}_{시즌}_{AB}_{버전}  (AB 없으면 4파트)
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


df_all = load_joined()

# =============================================================================
# Sidebar filters
# =============================================================================
with st.sidebar:
    st.header(":material/filter_alt: 필터")

    min_d, max_d = df_all["일"].min().date(), df_all["일"].max().date()
    d_range = st.date_input("기간", (min_d, max_d),
                            min_value=min_d, max_value=max_d)

    st.divider()
    st.caption("**채널 & 캠페인**")
    ch_classes = st.multiselect("채널분류", ["외부", "자체"], default=["외부", "자체"],
                                help="§6-1 자체매체는 비교시 분리")
    sel_ch = st.multiselect("채널", sorted(df_all["채널"].unique()),
                            default=sorted(df_all["채널"].unique()))
    sel_obj = st.multiselect("캠페인 목적",
                             sorted(df_all["캠페인목적"].unique()),
                             default=sorted(df_all["캠페인목적"].unique()))
    sel_grp = st.multiselect("타겟그룹", sorted(df_all["그룹"].unique()),
                             default=sorted(df_all["그룹"].unique()))

    st.divider()
    st.caption("**소재 속성** (§3-3)")
    sel_type = st.multiselect("소재타입", sorted(df_all["소재타입"].unique()),
                              default=sorted(df_all["소재타입"].unique()))
    sel_cat = st.multiselect("소재 카테고리",
                             sorted(df_all["소재카테고리"].unique()),
                             default=sorted(df_all["소재카테고리"].unique()))
    sel_season = st.multiselect("시즌", sorted(df_all["시즌"].unique()),
                                default=sorted(df_all["시즌"].unique()))

    st.divider()
    st.caption("**분석 옵션**")
    exclude_brand = st.toggle("브랜드KW 제외", value=True,
                              help="§6-1 ROAS 부풀려짐 방지")
    basis = st.radio("지표 기준",
                     ["AF (MMP, 권장)", "채널 보고"], index=0)
    use_af = basis.startswith("AF")

# =============================================================================
# Apply filters
# =============================================================================
d_from, d_to = (d_range if isinstance(d_range, tuple) and len(d_range) == 2
                else (min_d, max_d))

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
# Header + KPI
# =============================================================================
st.title(":material/trending_up: 플러스스토어 퍼마 대시보드")
notes = []
if exclude_brand: notes.append("브랜드KW 제외")
if "자체" not in ch_classes: notes.append("자체매체 제외")
st.caption(
    f"{d_from} ~ {d_to}  ·  {len(df):,}행  ·  기준: **{basis_label}** "
    + (f"  ·  ⚙️ {' / '.join(notes)}" if notes else "")
)

total_spend = df["비용"].sum()
total_impr = df["노출"].sum()
total_click = df["클릭"].sum()
total_signup = df[signup_col].sum()
total_revenue = df[revenue_col].sum()
ctr = (total_click / total_impr * 100) if total_impr else 0
cac = (total_spend / total_signup) if total_signup else 0
roas = (total_revenue / total_spend) if total_spend else 0
af_cov = (df["가입_AF"].sum() / df["가입_채널"].sum() * 100
          if df["가입_채널"].sum() else 0)

with st.container(horizontal=True):
    st.metric("총 광고비", fmt_won(total_spend), border=True)
    st.metric("노출", fmt_num(total_impr), border=True)
    st.metric("CTR", f"{ctr:.2f}%", border=True)
    st.metric(f"가입 ({basis_label})", fmt_num(total_signup), border=True)
    st.metric(f"CAC ({basis_label})", fmt_won(cac), border=True)
    roas_tag = ("양호 ✓" if roas >= ROAS_GOOD
                else "개선 필요 ▼" if roas < ROAS_BAD else "관찰 ○")
    st.metric(f"ROAS ({basis_label})", f"{roas:.2f}", delta=roas_tag,
              delta_color="normal", border=True)
    st.metric("AF 커버리지", f"{af_cov:.1f}%", border=True,
              help="70~90%가 정상 (§5)")

st.divider()

# =============================================================================
# Tabs
# =============================================================================
tab_overview, tab_obj, tab_creative, tab_ab, tab_group, tab_rank = st.tabs([
    "📈 전체 추세",
    "🎯 목적별",
    "🎨 소재 속성",
    "🅰️🅱️ A/B 테스트",
    "👥 타겟그룹",
    "🏆 캠페인 랭킹",
])

# -----------------------------------------------------------------------------
# TAB 1: 전체 추세
# -----------------------------------------------------------------------------
with tab_overview:
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
                        name="광고비(₩)", marker_color="#CCC", opacity=0.65,
                        yaxis="y")
            for ch in sorted(daily["채널"].unique()):
                sub = daily[daily["채널"] == ch]
                fig.add_scatter(
                    x=sub["일"], y=sub["매출"], name=f"{ch} 매출",
                    mode="lines",
                    line=dict(color=CHANNEL_COLOR.get(ch, "#888"), width=2),
                    yaxis="y2")
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10),
                              yaxis=dict(title="광고비"),
                              yaxis2=dict(title="매출", overlaying="y", side="right"),
                              legend=dict(orientation="h", y=1.12),
                              hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

    with col_ch:
        with st.container(border=True):
            st.subheader("채널별 ROAS")
            by_ch = df.groupby(["채널", "채널분류"]).agg(
                비용=("비용", "sum"), 매출=(revenue_col, "sum"),
                가입=(signup_col, "sum"),
            ).reset_index()
            by_ch["ROAS"] = by_ch["매출"] / by_ch["비용"]
            by_ch = by_ch.sort_values("ROAS", ascending=True)

            fig = go.Figure()
            fig.add_bar(
                x=by_ch["ROAS"], y=by_ch["채널"], orientation="h",
                marker=dict(
                    color=[CHANNEL_COLOR.get(c, "#888") for c in by_ch["채널"]],
                    pattern=dict(
                        shape=["/" if cls == "자체" else "" for cls in by_ch["채널분류"]],
                    ),
                ),
                text=[f"{v:.2f}" + (" (자체)" if cls == "자체" else "")
                      for v, cls in zip(by_ch["ROAS"], by_ch["채널분류"])],
                textposition="outside",
            )
            fig.add_vline(x=ROAS_GOOD, line_dash="dash", line_color="#22aa22",
                          annotation_text=f"양호 {ROAS_GOOD}",
                          annotation_position="top")
            fig.add_vline(x=ROAS_BAD, line_dash="dash", line_color="#cc3333",
                          annotation_text=f"불량 {ROAS_BAD}",
                          annotation_position="bottom")
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10),
                              xaxis_title=f"ROAS ({basis_label})",
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: 캠페인 목적별
# -----------------------------------------------------------------------------
with tab_obj:
    st.caption("§3-2 캠페인 목적별 효율 비교 — 예산 재분배 의사결정 근거")
    by_obj = df.groupby("캠페인목적").agg(
        비용=("비용", "sum"), 가입=(signup_col, "sum"),
        매출=(revenue_col, "sum"), 노출=("노출", "sum"),
    ).reset_index()
    by_obj["ROAS"] = (by_obj["매출"] / by_obj["비용"]).round(2)
    by_obj["CAC"] = (by_obj["비용"] / by_obj["가입"].replace(0, pd.NA)).round(0)
    by_obj["비용비중(%)"] = (by_obj["비용"] / by_obj["비용"].sum() * 100).round(1)
    by_obj = by_obj.sort_values("ROAS", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("목적별 ROAS")
            fig = px.bar(by_obj, x="ROAS", y="캠페인목적", orientation="h",
                         color="ROAS",
                         color_continuous_scale="RdYlGn",
                         color_continuous_midpoint=ROAS_GOOD,
                         text="ROAS")
            fig.add_vline(x=ROAS_GOOD, line_dash="dash", line_color="#22aa22")
            fig.add_vline(x=ROAS_BAD, line_dash="dash", line_color="#cc3333")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10),
                              coloraxis_showscale=False, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader("비용 배분 vs 매출 배분")
            melt = by_obj.assign(
                매출비중=(by_obj["매출"] / by_obj["매출"].sum() * 100).round(1)
            )[["캠페인목적", "비용비중(%)", "매출비중"]].rename(
                columns={"비용비중(%)": "비용비중", "매출비중": "매출비중"})
            fig = go.Figure()
            fig.add_bar(x=melt["캠페인목적"], y=melt["비용비중"],
                        name="비용 비중(%)", marker_color="#FFA500")
            fig.add_bar(x=melt["캠페인목적"], y=melt["매출비중"],
                        name="매출 비중(%)", marker_color="#4CAF50")
            fig.update_layout(barmode="group", height=420,
                              margin=dict(l=10, r=10, t=30, b=10),
                              legend=dict(orientation="h", y=1.15))
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.subheader("목적별 상세")
        st.dataframe(
            by_obj[["캠페인목적", "비용", "비용비중(%)", "가입", "CAC", "매출", "ROAS"]],
            hide_index=True, use_container_width=True,
            column_config={
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "CAC": st.column_config.NumberColumn(format="₩%d"),
                "매출": st.column_config.NumberColumn(format="₩%d"),
                "가입": st.column_config.NumberColumn(format="%d"),
                "ROAS": st.column_config.ProgressColumn(
                    "ROAS", format="%.2f", min_value=0,
                    max_value=float(by_obj["ROAS"].max() * 1.1)),
            },
        )

# -----------------------------------------------------------------------------
# TAB 3: 소재 속성
# -----------------------------------------------------------------------------
with tab_creative:
    st.caption("§3-3 소재명 파싱 기반 분석 — 어떤 속성이 효율적인지")

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
        with col_st:
            with st.container(border=True):
                st.subheader(title)
                g = agg_by(col_key, title)
                fig = px.bar(
                    g, x="ROAS", y=col_key, orientation="h",
                    color="ROAS", color_continuous_scale="RdYlGn",
                    color_continuous_midpoint=ROAS_GOOD, text="ROAS")
                fig.update_traces(textposition="outside")
                fig.update_layout(height=350, margin=dict(l=5, r=5, t=10, b=10),
                                  yaxis=dict(title=None, autorange="reversed"),
                                  coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.subheader("카테고리 × 소재타입 ROAS 히트맵")
        pivot_rev = df.pivot_table(index="소재카테고리", columns="소재타입",
                                   values=revenue_col, aggfunc="sum", fill_value=0)
        pivot_spend = df.pivot_table(index="소재카테고리", columns="소재타입",
                                     values="비용", aggfunc="sum", fill_value=0)
        pivot_roas = (pivot_rev / pivot_spend.replace(0, pd.NA)).round(2)
        fig = px.imshow(pivot_roas, text_auto=".2f",
                        color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=ROAS_GOOD, aspect="auto")
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10),
                          coloraxis_colorbar=dict(title="ROAS"))
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: A/B 테스트 판정
# -----------------------------------------------------------------------------
with tab_ab:
    st.caption(
        f"§6-4 A/B 테스트 판정 — 최소 노출 {AB_MIN_IMPR:,} 필요. "
        "같은 (채널, 캠페인, 카테고리, 시즌) 내 A vs B 비교."
    )

    ab = df[df["AB"].isin(["A", "B"])].copy()
    grouping = ["채널", "캠페인목적", "소재카테고리", "시즌"]
    pair = ab.groupby(grouping + ["AB"]).agg(
        노출=("노출", "sum"), 클릭=("클릭", "sum"),
        가입=(signup_col, "sum"), 매출=(revenue_col, "sum"),
        비용=("비용", "sum"),
    ).reset_index()

    # Pivot to get A and B side-by-side
    wide = pair.pivot_table(
        index=grouping, columns="AB",
        values=["노출", "클릭", "가입", "매출", "비용"],
    ).reset_index()
    # flatten multiindex
    wide.columns = [f"{m}_{l}" if l else m for m, l in wide.columns]

    # A·B 양쪽 값이 모두 있어야 비교 가능 — 한쪽만 있는 페어는 제외
    required_cols = ["노출_A", "노출_B", "클릭_A", "클릭_B",
                     "비용_A", "비용_B", "매출_A", "매출_B"]
    missing = [c for c in required_cols if c not in wide.columns]
    if missing:
        wide = wide.reindex(columns=list(wide.columns) + missing)
    wide = wide.dropna(subset=required_cols)
    # 비용이 0이면 ROAS 계산 불가
    wide = wide[(wide["비용_A"] > 0) & (wide["비용_B"] > 0)
                & (wide["노출_A"] > 0) & (wide["노출_B"] > 0)]

    rows = []
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
        st.info("A/B 페어가 없어. 필터 조건 때문에 A 또는 B 한쪽만 남았을 수 있음.")
    else:
        ab_df = pd.DataFrame(rows).sort_values("Δ ROAS", key=abs, ascending=False)

        col1, col2 = st.columns(2)
        col1.metric("A/B 페어 총수", len(ab_df))
        col2.metric("샘플 충분 페어",
                    f"{(ab_df['샘플충분'] == '✓').sum()} / {len(ab_df)}")

        with st.container(border=True):
            st.subheader("ROAS 차이 Top (샘플 충분한 것부터)")
            ok = ab_df[ab_df["샘플충분"] == "✓"].head(20)
            if not ok.empty:
                fig = go.Figure()
                fig.add_bar(
                    x=ok["ROAS_A"],
                    y=ok.index.astype(str) + " | " + ok["채널"] + "/" +
                      ok["카테고리"] + "/" + ok["시즌"],
                    orientation="h", name="A", marker_color="#6BAED6",
                )
                fig.add_bar(
                    x=ok["ROAS_B"],
                    y=ok.index.astype(str) + " | " + ok["채널"] + "/" +
                      ok["카테고리"] + "/" + ok["시즌"],
                    orientation="h", name="B", marker_color="#FD8D3C",
                )
                fig.update_layout(barmode="group", height=500,
                                  margin=dict(l=10, r=10, t=10, b=10),
                                  legend=dict(orientation="h", y=1.08))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("샘플이 충분한 A/B 페어가 없어. 노출 누적 더 필요.")

        with st.container(border=True):
            st.subheader("A/B 전체 표")
            st.dataframe(ab_df, hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: 타겟그룹별 (§3-4)
# -----------------------------------------------------------------------------
with tab_group:
    st.caption("§3-4 타겟그룹별 성과 — 논타겟/유사/리마/윈백/VIP")
    by_grp = df.groupby("그룹").agg(
        비용=("비용", "sum"), 가입=(signup_col, "sum"),
        매출=(revenue_col, "sum"), 노출=("노출", "sum"),
    ).reset_index()
    by_grp["ROAS"] = (by_grp["매출"] / by_grp["비용"]).round(2)
    by_grp["CAC"] = (by_grp["비용"] / by_grp["가입"].replace(0, pd.NA)).round(0)
    by_grp = by_grp.sort_values("ROAS", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("그룹별 ROAS")
            fig = px.bar(by_grp, x="ROAS", y="그룹", orientation="h",
                         color="ROAS", color_continuous_scale="RdYlGn",
                         color_continuous_midpoint=ROAS_GOOD, text="ROAS")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        with st.container(border=True):
            st.subheader("그룹별 CAC")
            fig = px.bar(by_grp.sort_values("CAC"), x="CAC", y="그룹",
                         orientation="h",
                         color="CAC", color_continuous_scale="RdYlGn_r",
                         text=by_grp.sort_values("CAC")["CAC"].apply(fmt_won))
            fig.update_traces(textposition="outside")
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10),
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.dataframe(
            by_grp[["그룹", "비용", "노출", "가입", "CAC", "매출", "ROAS"]],
            hide_index=True, use_container_width=True,
            column_config={
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "CAC": st.column_config.NumberColumn(format="₩%d"),
                "매출": st.column_config.NumberColumn(format="₩%d"),
            },
        )

# -----------------------------------------------------------------------------
# TAB 6: 캠페인 랭킹
# -----------------------------------------------------------------------------
with tab_rank:
    rank = df.groupby(["채널", "채널분류", "캠페인목적", "캠페인"]).agg(
        비용=("비용", "sum"), 클릭=("클릭", "sum"), 노출=("노출", "sum"),
        가입=(signup_col, "sum"), 매출=(revenue_col, "sum"),
    ).reset_index()
    rank["CTR(%)"] = (rank["클릭"] / rank["노출"] * 100).round(2)
    rank["CAC"] = (rank["비용"] / rank["가입"].replace(0, pd.NA)).round(0)
    rank["ROAS"] = (rank["매출"] / rank["비용"]).round(2)
    rank["상태"] = rank["ROAS"].apply(
        lambda r: "🟢 양호" if r >= ROAS_GOOD
        else ("🔴 개선 필요" if r < ROAS_BAD else "🟡 관찰"))
    rank = rank.sort_values("ROAS", ascending=False)[
        ["채널분류", "채널", "캠페인목적", "캠페인", "비용", "노출", "클릭",
         "CTR(%)", "가입", "CAC", "매출", "ROAS", "상태"]
    ]

    with st.container(border=True):
        st.dataframe(
            rank, hide_index=True, use_container_width=True,
            column_config={
                "비용": st.column_config.NumberColumn(format="₩%d"),
                "CAC": st.column_config.NumberColumn(format="₩%d"),
                "매출": st.column_config.NumberColumn(format="₩%d"),
                "ROAS": st.column_config.ProgressColumn(
                    "ROAS", format="%.2f", min_value=0,
                    max_value=float(rank["ROAS"].max() * 1.1)),
            },
        )

st.caption(
    f"📌 CLAUDE.md §3·5·6 반영  ·  "
    f"ROAS 임계값: 🟢 ≥{ROAS_GOOD}, 🔴 <{ROAS_BAD}  ·  "
    f"A/B 최소노출: {AB_MIN_IMPR:,}"
)
