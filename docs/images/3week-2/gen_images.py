"""3주차 2부 강의 이미지 생성 스크립트 (HTML → PNG via Playwright)
RFM + 카피 실험 루프 + Slack MCP — 8개 이미지
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent
W, H = 1200, 630

COMMON_CSS = """
  @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Pretendard Variable', 'Apple SD Gothic Neo', sans-serif;
         background: #f8f9fa; width: 1200px; height: 630px; overflow: hidden; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 20px;
           font-size: 12px; font-weight: 600; }
"""

# ─────────────────────────────────────────────────────────────────
# 01. RFM 3축 개념도
# ─────────────────────────────────────────────────────────────────
html_01 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
.wrap { padding: 44px 56px; }
.label { color: #64748b; font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 30px; font-weight: 800; margin-bottom: 8px; }
.sub { color: #94a3b8; font-size: 14px; margin-bottom: 32px; }
.axes { display: flex; gap: 24px; margin-bottom: 28px; }
.axis-card { flex: 1; border-radius: 16px; padding: 24px 22px; position: relative; overflow: hidden; }
.axis-r { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border: 1px solid #4338ca; }
.axis-f { background: linear-gradient(135deg, #0c1f0c 0%, #14532d 100%); border: 1px solid #16a34a; }
.axis-m { background: linear-gradient(135deg, #1c0a08 0%, #7c2d12 100%); border: 1px solid #ea580c; }
.axis-letter { font-size: 64px; font-weight: 900; position: absolute; right: 20px; top: 12px; opacity: 0.15; }
.axis-r .axis-letter { color: #818cf8; }
.axis-f .axis-letter { color: #4ade80; }
.axis-m .axis-letter { color: #fb923c; }
.axis-name { font-size: 13px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px; }
.axis-r .axis-name { color: #818cf8; }
.axis-f .axis-name { color: #4ade80; }
.axis-m .axis-name { color: #fb923c; }
.axis-title { color: #fff; font-size: 18px; font-weight: 800; margin-bottom: 6px; }
.axis-q { color: rgba(255,255,255,0.6); font-size: 13px; margin-bottom: 16px; font-style: italic; }
.score-row { display: flex; flex-direction: column; gap: 4px; }
.score-item { display: flex; align-items: center; gap: 10px; }
.score-bar-wrap { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; }
.score-bar { height: 100%; border-radius: 3px; }
.axis-r .score-bar { background: #818cf8; }
.axis-f .score-bar { background: #4ade80; }
.axis-m .score-bar { background: #fb923c; }
.score-label { color: rgba(255,255,255,0.7); font-size: 11px; width: 48px; font-weight: 600; }
.score-val { color: rgba(255,255,255,0.5); font-size: 11px; width: 90px; }
.bottom { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 14px 20px; }
.bottom-text { color: #94a3b8; font-size: 13px; line-height: 1.6; }
.bottom-text strong { color: #e2e8f0; }
</style></head><body><div class="wrap">
<div class="label">RFM 개념 · PART 16</div>
<h1>RFM — 세 개의 숫자로 고객을 읽는다</h1>
<div class="sub">"예산 없어요" 마케터의 가장 강력한 무기 — 행동 데이터 중 순도 높은 것만 3가지</div>
<div class="axes">
  <div class="axis-card axis-r">
    <div class="axis-letter">R</div>
    <div class="axis-name">RECENCY</div>
    <div class="axis-title">최근성</div>
    <div class="axis-q">"마지막으로 언제 샀나?"</div>
    <div class="score-row">
      <div class="score-item"><div class="score-label">5점</div><div class="score-bar-wrap"><div class="score-bar" style="width:100%"></div></div><div class="score-val">0 ~ 30일</div></div>
      <div class="score-item"><div class="score-label">4점</div><div class="score-bar-wrap"><div class="score-bar" style="width:80%"></div></div><div class="score-val">31 ~ 60일</div></div>
      <div class="score-item"><div class="score-label">3점</div><div class="score-bar-wrap"><div class="score-bar" style="width:60%"></div></div><div class="score-val">61 ~ 90일</div></div>
      <div class="score-item"><div class="score-label">2점</div><div class="score-bar-wrap"><div class="score-bar" style="width:40%"></div></div><div class="score-val">91 ~ 180일</div></div>
      <div class="score-item"><div class="score-label">1점</div><div class="score-bar-wrap"><div class="score-bar" style="width:20%"></div></div><div class="score-val">181일 이상</div></div>
    </div>
  </div>
  <div class="axis-card axis-f">
    <div class="axis-letter">F</div>
    <div class="axis-name">FREQUENCY</div>
    <div class="axis-title">빈도</div>
    <div class="axis-q">"90일간 몇 번 샀나?"</div>
    <div class="score-row">
      <div class="score-item"><div class="score-label">5점</div><div class="score-bar-wrap"><div class="score-bar" style="width:100%"></div></div><div class="score-val">10회 이상</div></div>
      <div class="score-item"><div class="score-label">4점</div><div class="score-bar-wrap"><div class="score-bar" style="width:80%"></div></div><div class="score-val">4 ~ 9회</div></div>
      <div class="score-item"><div class="score-label">3점</div><div class="score-bar-wrap"><div class="score-bar" style="width:60%"></div></div><div class="score-val">2 ~ 3회</div></div>
      <div class="score-item"><div class="score-label">2점</div><div class="score-bar-wrap"><div class="score-bar" style="width:40%"></div></div><div class="score-val">1회</div></div>
      <div class="score-item"><div class="score-label">1점</div><div class="score-bar-wrap"><div class="score-bar" style="width:20%"></div></div><div class="score-val">0회</div></div>
    </div>
  </div>
  <div class="axis-card axis-m">
    <div class="axis-letter">M</div>
    <div class="axis-name">MONETARY</div>
    <div class="axis-title">구매액</div>
    <div class="axis-q">"90일간 얼마 썼나?"</div>
    <div class="score-row">
      <div class="score-item"><div class="score-label">5점</div><div class="score-bar-wrap"><div class="score-bar" style="width:100%"></div></div><div class="score-val">상위 20% (분위)</div></div>
      <div class="score-item"><div class="score-label">4점</div><div class="score-bar-wrap"><div class="score-bar" style="width:80%"></div></div><div class="score-val">20 ~ 40%</div></div>
      <div class="score-item"><div class="score-label">3점</div><div class="score-bar-wrap"><div class="score-bar" style="width:60%"></div></div><div class="score-val">40 ~ 60%</div></div>
      <div class="score-item"><div class="score-label">2점</div><div class="score-bar-wrap"><div class="score-bar" style="width:40%"></div></div><div class="score-val">60 ~ 80%</div></div>
      <div class="score-item"><div class="score-label">1점</div><div class="score-bar-wrap"><div class="score-bar" style="width:20%"></div></div><div class="score-val">하위 20% / 0원</div></div>
    </div>
  </div>
</div>
<div class="bottom">
  <div class="bottom-text">💡 <strong>왜 3개만으로 잘 작동하나?</strong> 앱 열기·뷰 같은 중간 행동은 노이즈가 크다. <strong>"실제로 돈 썼다"</strong>는 가장 강한 의도 시그널. 복잡한 ML 없이도 세그먼트 일치율 <strong>95%+</strong>.</div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 02. 7 세그먼트 매트릭스
# ─────────────────────────────────────────────────────────────────
html_02 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #fff; }
.wrap { padding: 36px 48px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 26px; }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.seg { border-radius: 14px; padding: 18px 16px; position: relative; }
.seg-champion { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; }
.seg-loyal { background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border: 2px solid #3b82f6; }
.seg-atrisk { background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border: 2px solid #ef4444; }
.seg-hibernating { background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%); border: 2px solid #8b5cf6; }
.seg-lost { background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border: 2px solid #9ca3af; }
.seg-new { background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border: 2px solid #10b981; }
.seg-potential { background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); border: 2px solid #f97316; }
.seg-icon { font-size: 28px; margin-bottom: 8px; }
.seg-name { font-size: 15px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.seg-cond { font-size: 11px; color: #374151; font-family: monospace; background: rgba(0,0,0,0.06); padding: 3px 6px; border-radius: 4px; margin-bottom: 8px; display: inline-block; }
.seg-action { font-size: 12px; color: #374151; line-height: 1.5; }
.seg-size { position: absolute; top: 14px; right: 14px; font-size: 12px; font-weight: 700; color: #6b7280; }
.bottom-row { display: flex; gap: 16px; }
.stat { flex: 1; background: #f8f9fa; border-radius: 10px; padding: 12px 16px; text-align: center; }
.stat-val { font-size: 22px; font-weight: 900; color: #111827; }
.stat-label { font-size: 12px; color: #6b7280; margin-top: 2px; }
</style></head><body><div class="wrap">
<h1>7 세그먼트 매트릭스</h1>
<div class="sub">RFM 점수 조합 → 세그먼트 → 다른 메시지 · 다른 액션</div>
<div class="grid">
  <div class="seg seg-champion">
    <div class="seg-size">~5%</div>
    <div class="seg-icon">👑</div>
    <div class="seg-name">Champion</div>
    <div class="seg-cond">R≥4 F≥4 M≥4</div>
    <div class="seg-action">VIP 인정<br>신상 선공개</div>
  </div>
  <div class="seg seg-loyal">
    <div class="seg-size">~12%</div>
    <div class="seg-icon">💙</div>
    <div class="seg-name">Loyal</div>
    <div class="seg-cond">R≥3 F≥4</div>
    <div class="seg-action">혜택 강화<br>적립 배증</div>
  </div>
  <div class="seg seg-atrisk">
    <div class="seg-size">~18%</div>
    <div class="seg-icon">⚠️</div>
    <div class="seg-name">At-Risk</div>
    <div class="seg-cond">R≤2 F≥3</div>
    <div class="seg-action">돌아올 이유<br>쿠폰 제공</div>
  </div>
  <div class="seg seg-hibernating">
    <div class="seg-size">~15%</div>
    <div class="seg-icon">😴</div>
    <div class="seg-name">Hibernating</div>
    <div class="seg-cond">R≤2 F≤2 M≥3</div>
    <div class="seg-action">감성 리엔게이지</div>
  </div>
  <div class="seg seg-lost">
    <div class="seg-size">~20%</div>
    <div class="seg-icon">💨</div>
    <div class="seg-name">Lost</div>
    <div class="seg-cond">R=1 F≤2</div>
    <div class="seg-action">저비용<br>최소 접촉</div>
  </div>
  <div class="seg seg-new">
    <div class="seg-size">~10%</div>
    <div class="seg-icon">🌱</div>
    <div class="seg-name">New</div>
    <div class="seg-cond">가입≤30일 F≤1</div>
    <div class="seg-action">온보딩 여정<br>첫 구매 유도</div>
  </div>
  <div class="seg seg-potential">
    <div class="seg-size">~20%</div>
    <div class="seg-icon">🔭</div>
    <div class="seg-name">Potential</div>
    <div class="seg-cond">나머지</div>
    <div class="seg-action">실험 대상 풀<br>A/B 테스트</div>
  </div>
  <div style="display:flex;align-items:center;justify-content:center;background:#f0fdf4;border-radius:14px;border:2px dashed #86efac;padding:18px">
    <div style="text-align:center"><div style="font-size:24px;margin-bottom:8px">📊</div><div style="font-size:13px;color:#166534;font-weight:700">15,000명<br>샘플 기준</div></div>
  </div>
</div>
<div class="bottom-row">
  <div class="stat"><div class="stat-val" style="color:#f59e0b">750명</div><div class="stat-label">Champion · CSV 다운로드</div></div>
  <div class="stat"><div class="stat-val" style="color:#ef4444">2,700명</div><div class="stat-label">At-Risk · 긴급 쿠폰</div></div>
  <div class="stat"><div class="stat-val" style="color:#8b5cf6">2,250명</div><div class="stat-label">Hibernating · 감성 캠페인</div></div>
  <div class="stat"><div class="stat-val" style="color:#6b7280">3,000명</div><div class="stat-label">Lost · 월 1회 이메일만</div></div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 03. 3라운드 Open Rate 비교
# ─────────────────────────────────────────────────────────────────
html_03 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #fff; }
.wrap { padding: 38px 50px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 28px; }
.rounds { display: flex; gap: 20px; margin-bottom: 24px; }
.round { flex: 1; border-radius: 14px; padding: 20px; }
.r1 { background: #fff7ed; border: 2px solid #fed7aa; }
.r2 { background: #eff6ff; border: 2px solid #bfdbfe; }
.r3 { background: #f0fdf4; border: 2px solid #86efac; }
.round-head { font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px; }
.r1 .round-head { color: #c2410c; }
.r2 .round-head { color: #1d4ed8; }
.r3 .round-head { color: #15803d; }
.round-title { font-size: 16px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.round-desc { font-size: 12px; color: #6b7280; margin-bottom: 14px; }
.seg-rates { display: flex; flex-direction: column; gap: 6px; }
.seg-row { display: flex; align-items: center; gap: 10px; }
.seg-name { font-size: 12px; font-weight: 600; color: #374151; width: 80px; }
.bar-wrap { flex: 1; height: 18px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
.bar { height: 100%; border-radius: 4px; display: flex; align-items: center; padding-left: 8px; }
.r1 .bar { background: #fed7aa; }
.r2 .bar { background: #bfdbfe; }
.r3 .bar { background: #86efac; }
.bar-pct { font-size: 11px; font-weight: 700; color: #374151; width: 36px; text-align: right; }
.insight { background: #f8f9fa; border-radius: 12px; padding: 16px 20px; }
.insight-title { font-size: 13px; font-weight: 700; color: #111827; margin-bottom: 10px; }
.insight-row { display: flex; gap: 20px; }
.insight-item { flex: 1; }
.insight-label { font-size: 11px; color: #6b7280; font-weight: 700; margin-bottom: 4px; }
.insight-val { font-size: 14px; font-weight: 800; color: #111827; }
.up { color: #16a34a; }
.down { color: #dc2626; }
</style></head><body><div class="wrap">
<h1>3라운드 실험 — Open Rate 비교</h1>
<div class="sub">1월(무차별) → 2월(A/B) → 3월(학습 반영) — 실험으로 진화하는 캠페인</div>
<div class="rounds">
  <div class="round r1">
    <div class="round-head">ROUND 1 · 1월</div>
    <div class="round-title">모든 세그먼트 "혜택 톤" 일괄</div>
    <div class="round-desc">무차별 발송의 한계 체감</div>
    <div class="seg-rates">
      <div class="seg-row"><div class="seg-name">Champion</div><div class="bar-wrap"><div class="bar" style="width:60%"></div></div><div class="bar-pct">3.0%</div></div>
      <div class="seg-row"><div class="seg-name">Loyal</div><div class="bar-wrap"><div class="bar" style="width:56%"></div></div><div class="bar-pct">2.8%</div></div>
      <div class="seg-row"><div class="seg-name">At-Risk</div><div class="bar-wrap"><div class="bar" style="width:50%"></div></div><div class="bar-pct">2.5%</div></div>
      <div class="seg-row"><div class="seg-name">Hibernating</div><div class="bar-wrap"><div class="bar" style="width:44%"></div></div><div class="bar-pct">2.2%</div></div>
      <div class="seg-row"><div class="seg-name">New</div><div class="bar-wrap"><div class="bar" style="width:48%"></div></div><div class="bar-pct">2.4%</div></div>
    </div>
  </div>
  <div class="round r2">
    <div class="round-head">ROUND 2 · 2월</div>
    <div class="round-title">세그먼트별 A/B 톤 실험</div>
    <div class="round-desc">어느 톤이 먹히는지 가설 검증</div>
    <div class="seg-rates">
      <div class="seg-row"><div class="seg-name">Champion</div><div class="bar-wrap"><div class="bar" style="width:92%"></div></div><div class="bar-pct">4.6%</div></div>
      <div class="seg-row"><div class="seg-name">Loyal</div><div class="bar-wrap"><div class="bar" style="width:80%"></div></div><div class="bar-pct">4.0%</div></div>
      <div class="seg-row"><div class="seg-name">At-Risk</div><div class="bar-wrap"><div class="bar" style="width:90%"></div></div><div class="bar-pct">4.5%</div></div>
      <div class="seg-row"><div class="seg-name">Hibernating</div><div class="bar-wrap"><div class="bar" style="width:92%"></div></div><div class="bar-pct">4.6%</div></div>
      <div class="seg-row"><div class="seg-name">New</div><div class="bar-wrap"><div class="bar" style="width:88%"></div></div><div class="bar-pct">4.4%</div></div>
    </div>
  </div>
  <div class="round r3">
    <div class="round-head">ROUND 3 · 3월</div>
    <div class="round-title">R2 승자 톤 대규모 집행</div>
    <div class="round-desc">학습 반영 시 리프트 측정</div>
    <div class="seg-rates">
      <div class="seg-row"><div class="seg-name">Champion</div><div class="bar-wrap"><div class="bar" style="width:100%"></div></div><div class="bar-pct">5.0%</div></div>
      <div class="seg-row"><div class="seg-name">Loyal</div><div class="bar-wrap"><div class="bar" style="width:96%"></div></div><div class="bar-pct">4.8%</div></div>
      <div class="seg-row"><div class="seg-name">At-Risk</div><div class="bar-wrap"><div class="bar" style="width:98%"></div></div><div class="bar-pct">4.9%</div></div>
      <div class="seg-row"><div class="seg-name">Hibernating</div><div class="bar-wrap"><div class="bar" style="width:100%"></div></div><div class="bar-pct">5.0%</div></div>
      <div class="seg-row"><div class="seg-name">New</div><div class="bar-wrap"><div class="bar" style="width:96%"></div></div><div class="bar-pct">4.8%</div></div>
    </div>
  </div>
</div>
<div class="insight">
  <div class="insight-title">🎯 핵심 발견 — 3라운드 학습 결과</div>
  <div class="insight-row">
    <div class="insight-item"><div class="insight-label">Champion × VIP 톤</div><div class="insight-val"><span class="up">+55%</span> 리프트 · 채택</div></div>
    <div class="insight-item"><div class="insight-label">Hibernating × 감성 톤</div><div class="insight-val"><span class="up">+55%</span> 역대 최고</div></div>
    <div class="insight-item"><div class="insight-label">At-Risk × 긴급 톤 가설</div><div class="insight-val"><span class="down">기각</span> · 혜택 톤이 승자</div></div>
    <div class="insight-item"><div class="insight-label">긴급성 톤 (전체)</div><div class="insight-val"><span class="down">전 세그 열위</span> · 메타교훈</div></div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 04. 톤 × 세그먼트 궁합 히트맵
# ─────────────────────────────────────────────────────────────────
html_04 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #f8f9fa; }
.wrap { padding: 38px 52px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 28px; }
table { width: 100%; border-collapse: separate; border-spacing: 6px; margin-bottom: 20px; }
th { padding: 10px 16px; font-size: 13px; font-weight: 700; text-align: center; color: #374151; background: #fff; border-radius: 8px; }
th:first-child { text-align: left; background: transparent; color: #9ca3af; font-size: 12px; }
td { padding: 12px 16px; text-align: center; font-size: 14px; font-weight: 700; border-radius: 10px; position: relative; }
td:first-child { text-align: left; background: #fff; font-size: 14px; font-weight: 700; color: #374151; }
.h5 { background: #064e3b; color: #6ee7b7; }
.h4 { background: #065f46; color: #34d399; }
.h3 { background: #047857; color: #a7f3d0; }
.h2 { background: #fff7ed; color: #ea580c; }
.h1 { background: #fee2e2; color: #dc2626; }
.star { font-size: 10px; }
.legend { display: flex; gap: 12px; align-items: center; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; }
.legend-dot { width: 14px; height: 14px; border-radius: 4px; }
.note { background: #fff; border-radius: 12px; padding: 14px 20px; margin-top: 16px; }
.note-text { font-size: 13px; color: #374151; line-height: 1.6; }
.note-text strong { color: #111827; }
</style></head><body><div class="wrap">
<h1>톤 × 세그먼트 Open Rate 히트맵</h1>
<div class="sub">3라운드 전체 데이터 피벗 — 평균 대비 +20% 이상 승자 조합 ⭐ 표시</div>
<table>
<thead>
<tr>
  <th>세그먼트</th>
  <th>🎁 혜택 톤</th>
  <th>🚨 긴급 톤</th>
  <th>💝 감성 톤</th>
  <th>👑 VIP 톤</th>
</tr>
</thead>
<tbody>
<tr>
  <td>👑 Champion</td>
  <td class="h3">3.0% </td>
  <td class="h2">2.1% </td>
  <td class="h3">3.2% </td>
  <td class="h5">4.6% ⭐</td>
</tr>
<tr>
  <td>💙 Loyal</td>
  <td class="h4">3.8% ⭐</td>
  <td class="h2">2.3% </td>
  <td class="h3">3.1% </td>
  <td class="h4">4.0% ⭐</td>
</tr>
<tr>
  <td>⚠️ At-Risk</td>
  <td class="h5">4.5% ⭐</td>
  <td class="h1">1.8% ✗</td>
  <td class="h3">3.0% </td>
  <td class="h3">3.3% </td>
</tr>
<tr>
  <td>😴 Hibernating</td>
  <td class="h3">2.8% </td>
  <td class="h1">1.5% ✗</td>
  <td class="h5">4.6% ⭐</td>
  <td class="h4">3.9% </td>
</tr>
<tr>
  <td>🌱 New</td>
  <td class="h3">3.2% </td>
  <td class="h2">2.0% </td>
  <td class="h4">4.2% ⭐</td>
  <td class="h3">3.5% </td>
</tr>
</tbody>
</table>
<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#064e3b"></div>4%+ (최고)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#065f46"></div>3.5~4%</div>
  <div class="legend-item"><div class="legend-dot" style="background:#047857"></div>2.5~3.5%</div>
  <div class="legend-item"><div class="legend-dot" style="background:#fff7ed;border:1px solid #fed7aa"></div>2~2.5%</div>
  <div class="legend-item"><div class="legend-dot" style="background:#fee2e2;border:1px solid #fecaca"></div>2% 미만 (경고)</div>
  <div class="legend-item" style="margin-left:20px"><span style="color:#16a34a;font-weight:700">⭐</span> 평균 대비 +20% 이상</div>
  <div class="legend-item"><span style="color:#dc2626;font-weight:700">✗</span> 기각 — 재사용 금지</div>
</div>
<div class="note">
  <div class="note-text">💡 <strong>의외의 발견</strong>: At-Risk 에 긴급 톤이 안 먹힌다 — "빨리 와" 보다 <strong>"당신을 위한 혜택"</strong>이 이탈 방지에 더 효과적. 긴급성은 전 세그먼트 열위 → 다음 라운드부터 배제.</div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 05. Sub-agent 병렬 생성 아키텍처
# ─────────────────────────────────────────────────────────────────
html_05 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); }
.wrap { padding: 40px 52px; }
.label { color: #818cf8; font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 28px; font-weight: 800; margin-bottom: 6px; }
.sub { color: #94a3b8; font-size: 13px; margin-bottom: 28px; }
.arch { display: flex; flex-direction: column; gap: 0; align-items: center; }
.main-agent { background: rgba(129,140,248,0.15); border: 2px solid #818cf8; border-radius: 14px;
              padding: 14px 24px; text-align: center; width: 340px; margin-bottom: 16px; }
.main-title { color: #fff; font-size: 15px; font-weight: 800; }
.main-sub { color: #818cf8; font-size: 12px; margin-top: 4px; }
.dispatch-label { color: rgba(255,255,255,0.3); font-size: 11px; font-weight: 600; letter-spacing: 2px; margin-bottom: 12px; }
.agents-row { display: flex; gap: 14px; width: 100%; justify-content: center; }
.sub-agent { flex: 1; max-width: 140px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15);
             border-radius: 12px; padding: 14px 12px; text-align: center; }
.sub-agent.highlight { background: rgba(167,139,250,0.12); border-color: rgba(167,139,250,0.35); }
.seg-badge { font-size: 18px; margin-bottom: 6px; }
.seg-label { color: #fff; font-size: 12px; font-weight: 700; margin-bottom: 4px; }
.seg-count { color: #6366f1; font-size: 11px; font-weight: 600; margin-bottom: 8px; }
.copy-out { background: rgba(99,102,241,0.2); border-radius: 6px; padding: 4px 8px; font-size: 11px; color: #a5b4fc; }
.result-row { display: flex; gap: 14px; margin-top: 14px; width: 100%; justify-content: center; }
.result-box { flex: 1; max-width: 280px; background: rgba(52,211,153,0.1); border: 1px solid rgba(52,211,153,0.3); border-radius: 10px; padding: 10px 14px; text-align: center; }
.result-label { color: #34d399; font-size: 11px; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px; }
.result-val { color: #fff; font-size: 16px; font-weight: 900; }
.result-sub { color: #6b7280; font-size: 11px; margin-top: 2px; }
.why { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px 20px; margin-top: 14px; width: 100%; max-width: 740px; }
.why-text { color: #94a3b8; font-size: 12px; line-height: 1.7; text-align: center; }
.why-text strong { color: #e2e8f0; }
</style></head><body><div class="wrap">
<div class="label">PART 21 · SUB-AGENT 병렬 생성</div>
<h1>7개 세그먼트 동시 병렬 카피 생성</h1>
<div class="sub">메인 컨텍스트 오염 없이 · 각자 독립 공간 · 총 140개 카피 10~15분 완성</div>
<div class="arch">
  <div class="main-agent">
    <div class="main-title">🎯 오케스트레이터 Agent</div>
    <div class="main-sub">dispatching-parallel-agents · 컨텍스트 깨끗하게 유지</div>
  </div>
  <div class="dispatch-label">⬇ DISPATCH 7개 병렬 ⬇</div>
  <div class="agents-row">
    <div class="sub-agent highlight">
      <div class="seg-badge">👑</div>
      <div class="seg-label">Champion</div>
      <div class="seg-count">VIP 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
    <div class="sub-agent">
      <div class="seg-badge">💙</div>
      <div class="seg-label">Loyal</div>
      <div class="seg-count">혜택 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
    <div class="sub-agent">
      <div class="seg-badge">⚠️</div>
      <div class="seg-label">At-Risk</div>
      <div class="seg-count">혜택 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
    <div class="sub-agent highlight">
      <div class="seg-badge">😴</div>
      <div class="seg-label">Hibernating</div>
      <div class="seg-count">감성 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
    <div class="sub-agent">
      <div class="seg-badge">🌱</div>
      <div class="seg-label">New</div>
      <div class="seg-count">감성 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
    <div class="sub-agent">
      <div class="seg-badge">💨</div>
      <div class="seg-label">Lost</div>
      <div class="seg-count">혜택 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
    <div class="sub-agent">
      <div class="seg-badge">🔭</div>
      <div class="seg-label">Potential</div>
      <div class="seg-count">혜택 톤</div>
      <div class="copy-out">20개 카피</div>
    </div>
  </div>
  <div class="result-row">
    <div class="result-box">
      <div class="result-label">총 생성량</div>
      <div class="result-val">140개</div>
      <div class="result-sub">7세그 × 20개 · 10~15분</div>
    </div>
    <div class="result-box">
      <div class="result-label">API 추가 비용</div>
      <div class="result-val">₩0</div>
      <div class="result-sub">구독 한도 내 · 별도 과금 없음</div>
    </div>
  </div>
  <div class="why">
    <div class="why-text">💡 순차 생성 vs 병렬: 순차로 7개 대화하면 <strong>이전 카피가 다음 카피에 영향</strong>을 미침 (컨텍스트 오염). 병렬 sub-agent 는 각자 독립 컨텍스트 → <strong>다양성 확보 + 컨텍스트 깨끗</strong></div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 06. Slack 주간 리포트 Mockup
# ─────────────────────────────────────────────────────────────────
html_06 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #1a1d21; }
.wrap { display: flex; height: 100%; }
.sidebar { width: 220px; background: #19171d; padding: 20px 16px; flex-shrink: 0; }
.ws-name { color: #fff; font-size: 15px; font-weight: 800; margin-bottom: 20px; }
.ch-list { display: flex; flex-direction: column; gap: 2px; }
.ch-item { padding: 6px 10px; border-radius: 6px; font-size: 13px; color: #9ca3af; display: flex; align-items: center; gap: 6px; }
.ch-item.active { background: #2c2d30; color: #fff; }
.ch-item .dot { width: 6px; height: 6px; border-radius: 50%; background: #ec4899; flex-shrink: 0; }
.main { flex: 1; padding: 0 24px; overflow: hidden; }
.ch-header { border-bottom: 1px solid #2c2d30; padding: 16px 0 12px; margin-bottom: 16px; }
.ch-title { color: #fff; font-size: 16px; font-weight: 800; }
.ch-desc { color: #6b7280; font-size: 12px; margin-top: 2px; }
.msg { display: flex; gap: 12px; margin-bottom: 14px; }
.avatar { width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.av-claude { background: linear-gradient(135deg, #7c3aed, #a855f7); }
.msg-body { flex: 1; }
.msg-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px; }
.msg-name { color: #fff; font-size: 13px; font-weight: 700; }
.msg-time { color: #6b7280; font-size: 11px; }
.msg-app { background: #2c2d30; color: #a855f7; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 600; }
.block { background: #2c2d30; border-radius: 10px; padding: 14px 16px; border-left: 4px solid #a855f7; }
.block-title { color: #fff; font-size: 14px; font-weight: 800; margin-bottom: 10px; }
.seg-line { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid #374151; }
.seg-line:last-child { border: none; }
.seg-icon { font-size: 14px; width: 20px; }
.seg-name { color: #e2e8f0; font-size: 13px; flex: 1; }
.seg-change { font-size: 13px; font-weight: 700; width: 80px; text-align: right; }
.up { color: #ef4444; }
.down { color: #10b981; }
.seg-action { font-size: 11px; color: #6b7280; flex: 2; }
.footer-row { display: flex; gap: 8px; margin-top: 10px; }
.action-btn { background: #374151; color: #e2e8f0; font-size: 11px; padding: 4px 10px; border-radius: 5px; font-weight: 600; }
.action-btn.primary { background: #7c3aed; color: #fff; }
</style></head><body><div class="wrap">
<div class="sidebar">
  <div class="ws-name">crm-lab-jaechul</div>
  <div class="ch-list">
    <div class="ch-item"># general</div>
    <div class="ch-item active"># crm-segments <span class="dot"></span></div>
    <div class="ch-item"># crm-copy</div>
    <div class="ch-item"># alerts</div>
    <div class="ch-item" style="margin-top:12px;color:#6b7280;font-size:11px">DIRECT MESSAGES</div>
    <div class="ch-item">🤖 Claude</div>
  </div>
</div>
<div class="main">
  <div class="ch-header">
    <div class="ch-title"># crm-segments</div>
    <div class="ch-desc">주간 세그먼트 이동 리포트 · 카피 승인 채널</div>
  </div>
  <div class="msg">
    <div class="avatar av-claude">🤖</div>
    <div class="msg-body">
      <div class="msg-header">
        <span class="msg-name">Claude</span>
        <span class="msg-app">Slack MCP</span>
        <span class="msg-time">오늘 오전 8:01</span>
      </div>
      <div class="block">
        <div class="block-title">📊 주간 세그먼트 리포트 (2025-03-31 기준)</div>
        <div class="seg-line">
          <span class="seg-icon">⚠️</span>
          <span class="seg-name">At-Risk</span>
          <span class="seg-change up">+342명 ↑18%</span>
          <span class="seg-action">→ 혜택 톤 + 5,000원 쿠폰 권장</span>
        </div>
        <div class="seg-line">
          <span class="seg-icon">👑</span>
          <span class="seg-name">Champion</span>
          <span class="seg-change down">+18명 ↑2.4%</span>
          <span class="seg-action">→ VIP 온보딩 canvas 자동 진입</span>
        </div>
        <div class="seg-line">
          <span class="seg-icon">💨</span>
          <span class="seg-name">Lost</span>
          <span class="seg-change up">+198명 ↑1.3%</span>
          <span class="seg-action">→ 저비용 유지 (월 1회 이메일)</span>
        </div>
        <div class="seg-line">
          <span class="seg-icon">😴</span>
          <span class="seg-name">Hibernating</span>
          <span class="seg-change down">-87명 ↓3.8%</span>
          <span class="seg-action">→ 감성 캠페인 효과 확인 ✅</span>
        </div>
        <div class="footer-row">
          <div class="action-btn primary">📥 At-Risk CSV 다운로드</div>
          <div class="action-btn">🔗 대시보드 보기</div>
          <div class="action-btn">📋 카피 후보 보기 (thread)</div>
        </div>
      </div>
    </div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 07. 2부 전체 파이프라인 (누구→뭐라고→효과)
# ─────────────────────────────────────────────────────────────────
html_07 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(160deg, #0ea5e9 0%, #6366f1 50%, #8b5cf6 100%); }
.wrap { padding: 40px 52px; }
.label { color: rgba(255,255,255,0.6); font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 28px; font-weight: 800; margin-bottom: 6px; }
.sub { color: rgba(255,255,255,0.7); font-size: 13px; margin-bottom: 28px; }
.pipeline { display: flex; align-items: stretch; gap: 0; }
.stage { flex: 1; background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
         border: 1px solid rgba(255,255,255,0.2); border-radius: 16px; padding: 20px 18px; }
.arrow-col { display: flex; align-items: center; width: 40px; justify-content: center; flex-shrink: 0; }
.arrow-inner { text-align: center; }
.arrow-line { width: 100%; height: 2px; background: rgba(255,255,255,0.2); }
.arrow-icon { color: rgba(255,255,255,0.4); font-size: 16px; margin-top: -4px; }
.stage-q { font-size: 12px; font-weight: 700; letter-spacing: 2px; color: rgba(255,255,255,0.5); margin-bottom: 8px; }
.stage-title { color: #fff; font-size: 20px; font-weight: 900; margin-bottom: 4px; }
.stage-subtitle { color: rgba(255,255,255,0.6); font-size: 12px; margin-bottom: 16px; }
.step-list { display: flex; flex-direction: column; gap: 6px; }
.step { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 8px 12px; }
.step-part { font-size: 10px; color: rgba(255,255,255,0.4); font-weight: 700; letter-spacing: 1px; }
.step-name { color: #fff; font-size: 12px; font-weight: 600; margin-top: 2px; }
.output-badge { display: inline-block; background: rgba(255,255,255,0.15); border-radius: 5px; padding: 2px 8px; font-size: 10px; color: rgba(255,255,255,0.7); margin-top: 4px; }
.bottom { background: rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 20px; margin-top: 20px; display: flex; gap: 32px; align-items: center; justify-content: center; }
.kpi { text-align: center; }
.kpi-val { color: #fff; font-size: 24px; font-weight: 900; }
.kpi-label { color: rgba(255,255,255,0.6); font-size: 11px; margin-top: 2px; }
.divider { width: 1px; height: 40px; background: rgba(255,255,255,0.2); }
</style></head><body><div class="wrap">
<div class="label">2부 전체 파이프라인</div>
<h1>누구에게 · 뭐라고 · 효과는 — 엔드투엔드</h1>
<div class="sub">Braze CSV → RFM 세그먼트 → 실험 학습 → 카피 생성 → Slack 포스팅</div>
<div class="pipeline">
  <div class="stage">
    <div class="stage-q">STEP 1 · 누구에게?</div>
    <div class="stage-title">RFM</div>
    <div class="stage-subtitle">세그먼트 분류</div>
    <div class="step-list">
      <div class="step">
        <div class="step-part">PART 17</div>
        <div class="step-name">Braze CSV 구조 이해</div>
        <div class="output-badge">15,000명 프로필</div>
      </div>
      <div class="step">
        <div class="step-part">PART 18</div>
        <div class="step-name">RFM 계산 + CLAUDE.md §12~17 추가</div>
        <div class="output-badge">segmented_users.csv</div>
      </div>
      <div class="step">
        <div class="step-part">PART 19</div>
        <div class="step-name">대시보드 RFM 탭 신설</div>
        <div class="output-badge">7세그 × CSV 다운로드</div>
      </div>
    </div>
  </div>
  <div class="arrow-col"><div class="arrow-inner"><div class="arrow-line"></div><div class="arrow-icon">▶</div></div></div>
  <div class="stage">
    <div class="stage-q">STEP 2 · 뭐라고?</div>
    <div class="stage-title">카피</div>
    <div class="stage-subtitle">실험 + 생성</div>
    <div class="step-list">
      <div class="step">
        <div class="step-part">PART 20</div>
        <div class="step-name">3라운드 실험 분석</div>
        <div class="output-badge">톤×세그 히트맵</div>
      </div>
      <div class="step">
        <div class="step-part">PART 21</div>
        <div class="step-name">Sub-agent 병렬 카피 생성</div>
        <div class="output-badge">140개 카피 CSV</div>
      </div>
      <div class="step">
        <div class="step-part">PART 22</div>
        <div class="step-name">CLAUDE.md 학습 로그 append</div>
        <div class="output-badge">§17 자동 업데이트</div>
      </div>
    </div>
  </div>
  <div class="arrow-col"><div class="arrow-inner"><div class="arrow-line"></div><div class="arrow-icon">▶</div></div></div>
  <div class="stage">
    <div class="stage-q">STEP 3 · 효과는?</div>
    <div class="stage-title">Slack</div>
    <div class="stage-subtitle">리포트 + 승인</div>
    <div class="step-list">
      <div class="step">
        <div class="step-part">PART 23</div>
        <div class="step-name">Slack MCP 무료 세팅</div>
        <div class="output-badge">5분 · OAuth 연결</div>
      </div>
      <div class="step">
        <div class="step-part">PART 24</div>
        <div class="step-name">주간 리포트 자동 포스팅</div>
        <div class="output-badge">#crm-segments 블록</div>
      </div>
      <div class="step">
        <div class="step-part">PART 24.5</div>
        <div class="step-name">역방향 구조 이해</div>
        <div class="output-badge">4주차 예고 맥락</div>
      </div>
    </div>
  </div>
</div>
<div class="bottom">
  <div class="kpi"><div class="kpi-val">₩0</div><div class="kpi-label">API 추가 비용</div></div>
  <div class="divider"></div>
  <div class="kpi"><div class="kpi-val">140개</div><div class="kpi-label">자동 생성 카피</div></div>
  <div class="divider"></div>
  <div class="kpi"><div class="kpi-val">7개</div><div class="kpi-label">RFM 세그먼트</div></div>
  <div class="divider"></div>
  <div class="kpi"><div class="kpi-val">~3시간</div><div class="kpi-label">전체 실습 소요</div></div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 08. CLAUDE.md 정적→동적 진화 개념
# ─────────────────────────────────────────────────────────────────
html_08 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #fff; }
.wrap { padding: 38px 50px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 4px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 28px; }
.compare { display: flex; gap: 40px; margin-bottom: 24px; }
.side { flex: 1; border-radius: 16px; padding: 24px 24px; }
.static { background: #f8f9fa; border: 2px solid #e5e7eb; }
.dynamic { background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%); border: 2px solid #a78bfa; }
.side-head { font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 10px; }
.static .side-head { color: #6b7280; }
.dynamic .side-head { color: #7c3aed; }
.side-title { font-size: 18px; font-weight: 800; color: #111827; margin-bottom: 16px; }
.section-list { display: flex; flex-direction: column; gap: 6px; }
.sec { padding: 8px 12px; border-radius: 8px; font-size: 13px; }
.static .sec { background: #fff; color: #374151; }
.dynamic .sec { background: rgba(255,255,255,0.6); color: #374151; }
.sec-num { font-weight: 700; color: #6b7280; margin-right: 6px; }
.sec-name { font-weight: 600; }
.sec-tag { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 4px; margin-left: 8px; font-weight: 700; }
.tag-fixed { background: #f3f4f6; color: #6b7280; }
.tag-live { background: #ddd6fe; color: #7c3aed; }
.arrow-col { display: flex; flex-direction: column; justify-content: center; align-items: center; width: 60px; gap: 8px; }
.arrow-big { font-size: 28px; color: #d1d5db; }
.arrow-label { font-size: 11px; color: #9ca3af; font-weight: 600; text-align: center; }
.bottom { background: #f0fdf4; border: 1px solid #86efac; border-radius: 12px; padding: 14px 20px; }
.bottom-text { font-size: 13px; color: #374151; line-height: 1.7; }
.bottom-text strong { color: #111827; }
.highlight { background: #7c3aed; color: #fff; padding: 1px 6px; border-radius: 4px; }
</style></head><body><div class="wrap">
<h1>CLAUDE.md 진화 — 정적 정의집 → 살아 움직이는 지식 베이스</h1>
<div class="sub">1부(§1~11)는 고정된 룰북 · 2부(§12~17)는 실험마다 자라나는 팀 집단 지성</div>
<div class="compare">
  <div class="side static">
    <div class="side-head">1부 · 정적 정의집</div>
    <div class="side-title">변하지 않는 룰북</div>
    <div class="section-list">
      <div class="sec"><span class="sec-num">§1</span><span class="sec-name">프로젝트 개요</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§3</span><span class="sec-name">채널 코드 매핑</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§5</span><span class="sec-name">지표 정의·임계값</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§8</span><span class="sec-name">기술 스택 선호</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§11</span><span class="sec-name">Braze 스키마</span><span class="sec-tag tag-fixed">고정</span></div>
    </div>
  </div>
  <div class="arrow-col">
    <div class="arrow-big">→</div>
    <div class="arrow-label">2부에서<br>추가</div>
  </div>
  <div class="side dynamic">
    <div class="side-head">2부 · 살아 움직이는 지식</div>
    <div class="side-title">실험마다 업데이트</div>
    <div class="section-list">
      <div class="sec"><span class="sec-num">§12</span><span class="sec-name">RFM 스코어링 기준</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§13</span><span class="sec-name">세그먼트 정의 매트릭스</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§15</span><span class="sec-name">카피 톤 가이드</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§16</span><span class="sec-name">A/B 실험 원칙</span><span class="sec-tag tag-fixed">고정</span></div>
      <div class="sec"><span class="sec-num">§17</span><span class="sec-name">카피 학습 로그</span><span class="sec-tag tag-live">🔄 실험마다 append</span></div>
    </div>
  </div>
</div>
<div class="bottom">
  <div class="bottom-text">
    💡 <strong>§17 카피 학습 로그의 힘</strong>: 다음 주 Claude 가 CLAUDE.md 를 읽을 때 <strong>지난 주 학습이 자동으로 컨텍스트</strong>에 들어온다.
    "지난번 Champion에 VIP 먹혔으니 이번엔 더 강화" 같은 <strong class="highlight">연속성 있는 제안</strong>이 자연스럽게 나온다.
    담당자 이직해도 <strong>팀 집단 지성은 남는다</strong>.
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 렌더링
# ─────────────────────────────────────────────────────────────────
IMAGES = [
    ("3w2_01_rfm_concept.png",       html_01),
    ("3w2_02_segments.png",          html_02),
    ("3w2_03_rounds_comparison.png", html_03),
    ("3w2_04_tone_heatmap.png",      html_04),
    ("3w2_05_subagent_arch.png",     html_05),
    ("3w2_06_slack_report.png",      html_06),
    ("3w2_07_pipeline.png",          html_07),
    ("3w2_08_claudemd_evolution.png",html_08),
]

def render_all():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for fname, html in IMAGES:
            out_path = OUT / fname
            page.set_content(html, wait_until="networkidle")
            page.wait_for_timeout(500)
            page.screenshot(path=str(out_path), clip={"x":0,"y":0,"width":W,"height":H})
            print(f"✅ {fname}")
        browser.close()
    print(f"\n완료: {len(IMAGES)}개 이미지 → {OUT}")

if __name__ == "__main__":
    render_all()
