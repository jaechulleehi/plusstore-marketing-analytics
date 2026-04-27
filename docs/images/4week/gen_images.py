"""4주차 강의 이미지 생성 스크립트 (HTML → PNG via Playwright)"""
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
# 01. 4주차 여정 지도
# ─────────────────────────────────────────────────────────────────
html_01 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%); }
.wrap { padding: 40px 50px; }
.title { color: #a78bfa; font-size: 13px; font-weight: 700; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 8px; }
h1 { color: #fff; font-size: 28px; font-weight: 800; margin-bottom: 32px; }
h1 span { color: #c4b5fd; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 16px 18px; position: relative; }
.card.highlight { background: rgba(167,139,250,0.15); border-color: rgba(167,139,250,0.4); }
.part { font-size: 11px; color: #a78bfa; font-weight: 700; letter-spacing: 1px; margin-bottom: 6px; }
.name { color: #fff; font-size: 14px; font-weight: 600; line-height: 1.4; margin-bottom: 8px; }
.time { font-size: 12px; color: #6b7280; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.row3 { display: flex; justify-content: space-between; margin-top: 28px; gap: 14px; }
.card2 { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
         border-radius: 12px; padding: 14px 18px; flex: 1; }
.opt { font-size: 11px; color: #f59e0b; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px; }
</style></head><body><div class="wrap">
<div class="title">4주차 여정 지도</div>
<h1>수동을 자동으로, 혼자를 <span>팀으로</span></h1>
<div class="grid">
  <div class="card">
    <div class="part">PART 26</div>
    <div class="name">3주차 복기<br>수동 루틴의 한계</div>
    <div class="time">⏱ 5분</div>
  </div>
  <div class="card highlight">
    <div class="part">PART 27</div>
    <div class="name">Routines 개념<br>클라우드 스케줄 Claude</div>
    <div class="time">⏱ 10분</div>
  </div>
  <div class="card highlight">
    <div class="part">PART 28</div>
    <div class="name">첫 Routine 만들기<br>매주 월 8시 자동 리포트</div>
    <div class="time">⏱ 20분</div>
  </div>
  <div class="card highlight">
    <div class="part">PART 29</div>
    <div class="name">MCP 커넥터 연결<br>Slack 자동 포스팅</div>
    <div class="time">⏱ 15분</div>
  </div>
  <div class="card highlight">
    <div class="part">PART 30</div>
    <div class="name">Claude Code in Slack<br>팀원 @Claude 호출</div>
    <div class="time">⏱ 15분</div>
  </div>
  <div class="card">
    <div class="part">PART 31</div>
    <div class="name">GitHub Actions<br>팀 공용 자동화</div>
    <div class="time">⏱ 10분 (참고)</div>
  </div>
</div>
<div class="row3">
  <div class="card2">
    <div class="opt">선택 심화</div>
    <div class="name" style="color:#fff;font-size:13px">PART 32 · Agent SDK<br>자체 Slack 봇</div>
    <div class="time">⏱ 25분</div>
  </div>
  <div class="card2">
    <div class="opt" style="color:#34d399">체크리스트</div>
    <div class="name" style="color:#fff;font-size:13px">PART 33 · 비용·한도<br>배포 체크리스트</div>
    <div class="time">⏱ 10분</div>
  </div>
  <div class="card2">
    <div class="opt" style="color:#60a5fa">마무리</div>
    <div class="name" style="color:#fff;font-size:13px">PART 34 · FAQ<br>5주차 예고</div>
    <div class="time">⏱ 10분</div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 02. 수동 vs 자동 비교
# ─────────────────────────────────────────────────────────────────
html_02 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #fff; }
.wrap { display: flex; height: 100%; }
.side { flex: 1; padding: 50px 45px; display: flex; flex-direction: column; }
.left { background: #fff7ed; border-right: 3px solid #fed7aa; }
.right { background: #f0fdf4; }
.head { font-size: 13px; font-weight: 700; letter-spacing: 2px; margin-bottom: 12px; }
.left .head { color: #ea580c; }
.right .head { color: #16a34a; }
h2 { font-size: 26px; font-weight: 800; margin-bottom: 28px; }
.left h2 { color: #9a3412; }
.right h2 { color: #166534; }
.step { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px; }
.num { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center;
       justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; margin-top: 2px; }
.left .num { background: #fed7aa; color: #9a3412; }
.right .num { background: #bbf7d0; color: #166534; }
.step-text { font-size: 14px; color: #374151; line-height: 1.5; }
.step-time { font-size: 12px; color: #9ca3af; margin-top: 2px; }
.total { margin-top: auto; padding: 16px 20px; border-radius: 12px; }
.left .total { background: #fed7aa; }
.right .total { background: #bbf7d0; }
.total-label { font-size: 13px; font-weight: 600; color: #374151; }
.total-val { font-size: 32px; font-weight: 900; }
.left .total-val { color: #c2410c; }
.right .total-val { color: #15803d; }
.arrow { display: flex; align-items: center; justify-content: center; width: 60px;
         background: #f9fafb; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; }
.arrow-icon { font-size: 28px; color: #d1d5db; }
</style></head><body><div class="wrap">
<div class="side left">
  <div class="head">AS-IS · 3주차 수동 루틴</div>
  <h2>매주 월요일 35분</h2>
  <div class="step"><div class="num">1</div><div><div class="step-text">Braze·채널·AF CSV 다운로드</div><div class="step-time">15분 · 파일명 오타 위험</div></div></div>
  <div class="step"><div class="num">2</div><div><div class="step-text">raw/ 폴더에 파일 드롭</div><div class="step-time">2분 · 폴더 헷갈림</div></div></div>
  <div class="step"><div class="num">3</div><div><div class="step-text">Claude Code 열어 RFM 재계산</div><div class="step-time">10분 · 프롬프트 매번 다시 쓰기</div></div></div>
  <div class="step"><div class="num">4</div><div><div class="step-text">결과 확인 + Slack 포스팅</div><div class="step-time">5분 · 오탈자 실수</div></div></div>
  <div class="step"><div class="num">5</div><div><div class="step-text">GitHub 푸시</div><div class="step-time">3분 · conflict 처리</div></div></div>
  <div class="total"><div class="total-label">총 소요 · 실수 포인트 5개</div><div class="total-val">35분/주</div></div>
</div>
<div class="arrow"><div class="arrow-icon">→</div></div>
<div class="side right">
  <div class="head">TO-BE · 4주차 Routine 자동화</div>
  <h2>내가 자는 동안</h2>
  <div class="step"><div class="num">✓</div><div><div class="step-text">Routine 이 GitHub 에서 최신 데이터 pull</div><div class="step-time">자동 · 08:00:42</div></div></div>
  <div class="step"><div class="num">✓</div><div><div class="step-text">CLAUDE.md 기준 RFM 재계산</div><div class="step-time">자동 · 08:01:15</div></div></div>
  <div class="step"><div class="num">✓</div><div><div class="step-text">세그먼트 이동 분석 + 인사이트 생성</div><div class="step-time">자동 · 08:01:30</div></div></div>
  <div class="step"><div class="num">✓</div><div><div class="step-text">Slack #crm-segments 리포트 포스팅</div><div class="step-time">자동 · 08:01:37</div></div></div>
  <div class="step"><div class="num">👀</div><div><div class="step-text">내가 일어나서 결과만 확인</div><div class="step-time">08:45 · 내 역할은 승인·판단만</div></div></div>
  <div class="total"><div class="total-label">총 소요 · 실수 포인트 0개</div><div class="total-val">0분/주</div></div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 03. Routines 아키텍처
# ─────────────────────────────────────────────────────────────────
html_03 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(160deg, #0ea5e9 0%, #6366f1 100%); }
.wrap { padding: 48px 60px; }
.title { color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 30px; font-weight: 800; margin-bottom: 40px; }
.flow { display: flex; align-items: center; gap: 0; }
.node { background: rgba(255,255,255,0.12); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.25); border-radius: 16px;
        padding: 22px 24px; text-align: center; min-width: 155px; }
.node-icon { font-size: 30px; margin-bottom: 10px; }
.node-label { color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px; }
.node-title { color: #fff; font-size: 14px; font-weight: 700; line-height: 1.4; }
.node-sub { color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 4px; }
.arrow { flex: 1; text-align: center; color: rgba(255,255,255,0.5); font-size: 22px; }
.arrow-wrap { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.arrow-label { color: rgba(255,255,255,0.5); font-size: 11px; }
.note { margin-top: 32px; background: rgba(255,255,255,0.1); border-radius: 12px;
        padding: 16px 24px; display: flex; gap: 40px; }
.note-item { color: rgba(255,255,255,0.8); font-size: 13px; }
.note-item strong { color: #fff; }
</style></head><body><div class="wrap">
<div class="title">Routines 아키텍처</div>
<h1>내 맥이 꺼져 있어도 Claude 가 일한다</h1>
<div class="flow">
  <div class="node">
    <div class="node-icon">⏰</div>
    <div class="node-label">TRIGGER</div>
    <div class="node-title">스케줄</div>
    <div class="node-sub">매주 월 08:00 KST</div>
  </div>
  <div class="arrow"><div class="arrow-wrap"><span>→</span><span class="arrow-label">cron 표현식</span></div></div>
  <div class="node">
    <div class="node-icon">☁️</div>
    <div class="node-label">RUNTIME</div>
    <div class="node-title">Anthropic<br>클라우드</div>
    <div class="node-sub">내 맥 없이 실행</div>
  </div>
  <div class="arrow"><div class="arrow-wrap"><span>→</span><span class="arrow-label">GitHub OAuth</span></div></div>
  <div class="node">
    <div class="node-icon">📦</div>
    <div class="node-label">DATA SOURCE</div>
    <div class="node-title">GitHub 레포</div>
    <div class="node-sub">raw/braze/ CSV</div>
  </div>
  <div class="arrow"><div class="arrow-wrap"><span>→</span><span class="arrow-label">CLAUDE.md 기준</span></div></div>
  <div class="node">
    <div class="node-icon">🤖</div>
    <div class="node-label">PROCESS</div>
    <div class="node-title">Claude<br>RFM 분석</div>
    <div class="node-sub">세그먼트 · 인사이트</div>
  </div>
  <div class="arrow"><div class="arrow-wrap"><span>→</span><span class="arrow-label">MCP 커넥터</span></div></div>
  <div class="node">
    <div class="node-icon">💬</div>
    <div class="node-label">OUTPUT</div>
    <div class="node-title">Slack 리포트</div>
    <div class="node-sub">#crm-segments</div>
  </div>
</div>
<div class="note">
  <div class="note-item">⚡ <strong>실행 위치</strong>: Anthropic 클라우드 서버</div>
  <div class="note-item">💰 <strong>비용</strong>: $0.08/hr + 구독 소진</div>
  <div class="note-item">📊 <strong>플랜 한도</strong>: Pro 5회/일 · Max 15회/일</div>
  <div class="note-item">🔒 <strong>로컬 파일</strong>: 접근 불가 (GitHub 경유)</div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 04. Routines vs cron vs GitHub Actions 비교
# ─────────────────────────────────────────────────────────────────
html_04 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #f8f9fa; }
.wrap { padding: 44px 50px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 6px; }
.sub { font-size: 14px; color: #6b7280; margin-bottom: 32px; }
table { width: 100%; border-collapse: collapse; }
th { padding: 14px 20px; font-size: 13px; font-weight: 700; text-align: center; }
th:first-child { text-align: left; color: #6b7280; font-size: 12px; width: 22%; }
.th-routines { background: #7c3aed; color: #fff; border-radius: 10px 10px 0 0; }
.th-cron { background: #374151; color: #fff; border-radius: 10px 10px 0 0; }
.th-actions { background: #1d4ed8; color: #fff; border-radius: 10px 10px 0 0; }
td { padding: 13px 20px; font-size: 13px; border-bottom: 1px solid #f3f4f6; text-align: center; }
td:first-child { text-align: left; color: #6b7280; font-weight: 600; }
tr:hover td { background: #f9fafb; }
.yes { color: #16a34a; font-weight: 700; font-size: 15px; }
.no { color: #dc2626; font-weight: 700; font-size: 15px; }
.warn { color: #d97706; font-weight: 600; }
.rec { padding: 14px 20px; border-radius: 0 0 10px 10px; font-size: 12px; font-weight: 700; }
.rec-r { background: #ede9fe; color: #7c3aed; }
.rec-c { background: #f3f4f6; color: #374151; }
.rec-a { background: #dbeafe; color: #1d4ed8; }
.stars { color: #f59e0b; }
</style></head><body><div class="wrap">
<h1>자동화 방식 3가지 비교</h1>
<div class="sub">마케터 1인 기준 — 어떤 방식을 언제 써야 할까?</div>
<table>
<thead>
<tr>
  <th></th>
  <th class="th-routines">Routines</th>
  <th class="th-cron">로컬 cron</th>
  <th class="th-actions">GitHub Actions</th>
</tr>
</thead>
<tbody>
<tr><td>실행 위치</td><td>Anthropic 클라우드</td><td>내 맥</td><td>GitHub 서버</td></tr>
<tr><td>맥 꺼져도 실행</td><td class="yes">✅ 가능</td><td class="no">❌ 불가</td><td class="yes">✅ 가능</td></tr>
<tr><td>설정 난도</td><td>5분 웹 UI</td><td>터미널 crontab</td><td>YAML 작성</td></tr>
<tr><td>Claude 비용</td><td>구독 소진</td><td>구독 소진</td><td class="warn">API 토큰 별도 과금</td></tr>
<tr><td>MCP 커넥터</td><td class="yes">✅ 지원</td><td class="yes">✅ 지원</td><td class="warn">⚠️ 복잡</td></tr>
<tr><td>로컬 파일 접근</td><td class="no">❌</td><td class="yes">✅</td><td class="no">❌</td></tr>
<tr><td>이벤트 트리거</td><td>스케줄만</td><td>스케줄만</td><td class="yes">✅ PR·Push·이슈</td></tr>
<tr>
  <td>마케터 권장도</td>
  <td class="stars">⭐⭐⭐ 강력 추천</td>
  <td class="stars">⭐ 개인용</td>
  <td class="stars">⭐⭐ 팀 공용</td>
</tr>
</tbody>
</table>
<div style="display:flex;gap:0;margin-top:0">
  <div class="rec rec-r" style="flex:1">✅ 마케터 1인 자동화 기본 선택</div>
  <div class="rec rec-c" style="flex:1">내 맥 항상 켜놓는 경우만</div>
  <div class="rec rec-a" style="flex:1">팀 공용 · 이벤트 기반 필요 시</div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 05. 월요일 아침 자동화 타임라인
# ─────────────────────────────────────────────────────────────────
html_05 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); }
.wrap { padding: 48px 60px; }
.title { color: #818cf8; font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 28px; font-weight: 800; margin-bottom: 36px; }
h1 span { color: #a78bfa; }
.timeline { display: flex; flex-direction: column; gap: 0; }
.event { display: flex; gap: 24px; align-items: flex-start; }
.time-col { width: 120px; text-align: right; padding-top: 14px; flex-shrink: 0; }
.time-val { font-size: 18px; font-weight: 800; color: #fff; }
.time-sec { font-size: 11px; color: #6b7280; }
.line-col { display: flex; flex-direction: column; align-items: center; width: 40px; flex-shrink: 0; }
.dot-outer { width: 16px; height: 16px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.dot-inner { width: 8px; height: 8px; border-radius: 50%; }
.vline { width: 2px; flex: 1; min-height: 28px; }
.content { padding: 10px 0 24px; }
.event-title { color: #fff; font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.event-sub { color: #9ca3af; font-size: 13px; }
.auto { background: rgba(167,139,250,0.15); border: 1px solid rgba(167,139,250,0.3);
        border-radius: 6px; padding: 2px 10px; font-size: 11px; color: #a78bfa; font-weight: 600;
        display: inline-block; margin-left: 10px; }
.human { background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.3);
         border-radius: 6px; padding: 2px 10px; font-size: 11px; color: #34d399; font-weight: 600;
         display: inline-block; margin-left: 10px; }
.purple { background: #7c3aed; }
.green-dot { background: #34d399; }
.purple-line { background: rgba(124,58,237,0.3); }
.green-line { background: rgba(52,211,153,0.3); }
</style></head><body><div class="wrap">
<div class="title">월요일 아침 자동화 타임라인</div>
<h1>내가 <span>자는 동안</span> 시스템이 일한다</h1>
<div class="timeline">
  <div class="event">
    <div class="time-col"><div class="time-val">08:00</div><div class="time-sec">:00</div></div>
    <div class="line-col"><div class="dot-outer" style="background:rgba(124,58,237,0.2)"><div class="dot-inner purple"></div></div><div class="vline purple-line"></div></div>
    <div class="content"><div class="event-title">Routine 깨어남 <span class="auto">자동</span></div><div class="event-sub">내 맥 꺼져있음 · 나는 자고 있음 · Anthropic 클라우드 실행</div></div>
  </div>
  <div class="event">
    <div class="time-col"><div class="time-val">08:00</div><div class="time-sec">:42</div></div>
    <div class="line-col"><div class="dot-outer" style="background:rgba(124,58,237,0.2)"><div class="dot-inner purple"></div></div><div class="vline purple-line"></div></div>
    <div class="content"><div class="event-title">GitHub 에서 최신 데이터 pull <span class="auto">자동</span></div><div class="event-sub">raw/braze/ 최신 파일 읽기 · CLAUDE.md 로드</div></div>
  </div>
  <div class="event">
    <div class="time-col"><div class="time-val">08:01</div><div class="time-sec">:15</div></div>
    <div class="line-col"><div class="dot-outer" style="background:rgba(124,58,237,0.2)"><div class="dot-inner purple"></div></div><div class="vline purple-line"></div></div>
    <div class="content"><div class="event-title">RFM 재계산 + 세그먼트 분류 <span class="auto">자동</span></div><div class="event-sub">전주 대비 이동 감지 · At-Risk 감소 경보</div></div>
  </div>
  <div class="event">
    <div class="time-col"><div class="time-val">08:01</div><div class="time-sec">:37</div></div>
    <div class="line-col"><div class="dot-outer" style="background:rgba(124,58,237,0.2)"><div class="dot-inner purple"></div></div><div class="vline purple-line"></div></div>
    <div class="content"><div class="event-title">Slack #crm-segments 리포트 포스팅 <span class="auto">자동</span></div><div class="event-sub">Block Kit 포맷 · 세그먼트 현황 + 권장 액션</div></div>
  </div>
  <div class="event">
    <div class="time-col"><div class="time-val">08:45</div><div class="time-sec"></div></div>
    <div class="line-col"><div class="dot-outer" style="background:rgba(52,211,153,0.2)"><div class="dot-inner green-dot"></div></div><div class="vline" style="background:transparent"></div></div>
    <div class="content"><div class="event-title">내가 일어나서 Slack 확인 <span class="human">사람</span></div><div class="event-sub">결과만 확인 · 필요하면 @Claude 에게 추가 질문</div></div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 06. MCP 커넥터 연결 흐름
# ─────────────────────────────────────────────────────────────────
html_06 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #f0fdf4; }
.wrap { padding: 44px 56px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 6px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 32px; }
.compare { display: flex; gap: 40px; margin-bottom: 28px; }
.box { flex: 1; border-radius: 16px; padding: 24px 26px; }
.box-old { background: #fff7ed; border: 2px solid #fed7aa; }
.box-new { background: #fff; border: 2px solid #86efac; }
.box-head { font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 12px; }
.box-old .box-head { color: #ea580c; }
.box-new .box-head { color: #16a34a; }
.box-title { font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 16px; }
.flow-mini { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.chip { padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; }
.chip-gray { background: #f3f4f6; color: #374151; }
.chip-orange { background: #fed7aa; color: #c2410c; }
.chip-green { background: #bbf7d0; color: #166534; }
.chip-blue { background: #dbeafe; color: #1d4ed8; }
.chip-purple { background: #ede9fe; color: #7c3aed; }
.arr { color: #9ca3af; font-size: 14px; }
.scope-box { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px 24px; }
.scope-title { font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 12px; }
.scope-row { display: flex; gap: 24px; }
.scope-col { flex: 1; }
.scope-head { font-size: 11px; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; }
.yes-head { color: #16a34a; }
.no-head { color: #dc2626; }
.scope-item { font-size: 13px; color: #374151; padding: 4px 0; border-bottom: 1px solid #f3f4f6; }
.scope-item:last-child { border: none; }
</style></head><body><div class="wrap">
<h1>Routine + MCP 커넥터 연결</h1>
<div class="sub">3주차 로컬 MCP 와 4주차 클라우드 MCP 의 차이</div>
<div class="compare">
  <div class="box box-old">
    <div class="box-head">3주차 · 로컬 MCP</div>
    <div class="box-title">내 맥에서 실행</div>
    <div class="flow-mini">
      <div class="chip chip-gray">내가 명령</div><div class="arr">→</div>
      <div class="chip chip-orange">로컬 Claude</div><div class="arr">→</div>
      <div class="chip chip-orange">로컬 MCP 서버</div><div class="arr">→</div>
      <div class="chip chip-gray">Slack</div>
    </div>
    <div style="margin-top:14px;font-size:12px;color:#9a3412">✅ 로컬 파일 접근 가능<br>❌ 내 맥 꺼지면 중단</div>
  </div>
  <div class="box box-new">
    <div class="box-head">4주차 · Anthropic MCP 커넥터</div>
    <div class="box-title">클라우드에서 실행</div>
    <div class="flow-mini">
      <div class="chip chip-purple">스케줄</div><div class="arr">→</div>
      <div class="chip chip-green">클라우드 Claude</div><div class="arr">→</div>
      <div class="chip chip-green">MCP 커넥터</div><div class="arr">→</div>
      <div class="chip chip-gray">Slack</div>
    </div>
    <div style="margin-top:14px;font-size:12px;color:#166534">✅ 맥 꺼져도 실행<br>❌ 로컬 파일 직접 접근 불가</div>
  </div>
</div>
<div class="scope-box">
  <div class="scope-title">Slack MCP 커넥터 권한 설정 가이드</div>
  <div class="scope-row">
    <div class="scope-col">
      <div class="scope-head yes-head">✅ 줘야 할 권한</div>
      <div class="scope-item">chat:write — 지정 채널에 메시지 쓰기</div>
      <div class="scope-item">chat:write.public — 공개 채널 전용</div>
    </div>
    <div class="scope-col">
      <div class="scope-head no-head">❌ 주면 안 되는 권한</div>
      <div class="scope-item">channels:history — 채널 대화 전체 읽기</div>
      <div class="scope-item">users:read — 팀원 정보 조회</div>
      <div class="scope-item">files:read — 파일 읽기</div>
    </div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 07. Claude Code in Slack 아키텍처
# ─────────────────────────────────────────────────────────────────
html_07 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: linear-gradient(135deg, #4a1942 0%, #1e1b4b 100%); }
.wrap { padding: 46px 56px; }
.title { color: #c4b5fd; font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 28px; font-weight: 800; margin-bottom: 36px; }
h1 span { color: #a78bfa; }
.flow { display: flex; align-items: stretch; gap: 16px; margin-bottom: 28px; }
.step-box { flex: 1; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12);
            border-radius: 14px; padding: 20px 18px; text-align: center; }
.step-num { font-size: 11px; color: rgba(255,255,255,0.4); font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; }
.step-icon { font-size: 28px; margin-bottom: 10px; }
.step-title { color: #fff; font-size: 14px; font-weight: 700; line-height: 1.4; margin-bottom: 6px; }
.step-sub { color: rgba(255,255,255,0.5); font-size: 11px; line-height: 1.5; }
.arr { display: flex; align-items: center; color: rgba(255,255,255,0.3); font-size: 20px; }
.info-row { display: flex; gap: 16px; }
.info-box { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px; padding: 16px 18px; }
.info-label { color: rgba(255,255,255,0.4); font-size: 11px; font-weight: 700; letter-spacing: 1px; margin-bottom: 6px; }
.info-val { color: #fff; font-size: 13px; font-weight: 600; }
.highlight { color: #a78bfa; }
.warning { color: #fbbf24; }
</style></head><body><div class="wrap">
<div class="title">Claude Code in Slack 아키텍처</div>
<h1>팀원이 <span>@Claude</span> 한 마디로 분석 요청</h1>
<div class="flow">
  <div class="step-box">
    <div class="step-num">STEP 01</div>
    <div class="step-icon">💬</div>
    <div class="step-title">팀원이 Slack 에서<br>@Claude 멘션</div>
    <div class="step-sub">자기 구독으로 실행<br>Pro $20 이상 필요</div>
  </div>
  <div class="arr">→</div>
  <div class="step-box">
    <div class="step-num">STEP 02</div>
    <div class="step-icon">⚡</div>
    <div class="step-title">Claude Code in<br>Slack 앱 감지</div>
    <div class="step-sub">멘션한 사람의<br>Claude 구독 활성화</div>
  </div>
  <div class="arr">→</div>
  <div class="step-box">
    <div class="step-num">STEP 03</div>
    <div class="step-icon">📦</div>
    <div class="step-title">GitHub 레포<br>clone + 읽기</div>
    <div class="step-sub">OAuth 연결된 레포만<br>로컬 파일 불가</div>
  </div>
  <div class="arr">→</div>
  <div class="step-box">
    <div class="step-num">STEP 04</div>
    <div class="step-icon">🤖</div>
    <div class="step-title">Claude 분석<br>+ 답변 생성</div>
    <div class="step-sub">CLAUDE.md 자동 참조<br>인사이트 + 제안</div>
  </div>
  <div class="arr">→</div>
  <div class="step-box">
    <div class="step-num">STEP 05</div>
    <div class="step-icon">📩</div>
    <div class="step-title">Slack 스레드에<br>답변 포스팅</div>
    <div class="step-sub">원래 메시지 스레드<br>팀원 모두 확인 가능</div>
  </div>
</div>
<div class="info-row">
  <div class="info-box"><div class="info-label">필요 플랜</div><div class="info-val"><span class="highlight">Pro $20/월</span> 이상 (Team Standard ❌)</div></div>
  <div class="info-box"><div class="info-label">과금 방식</div><div class="info-val">구독 한도 소진 — <span class="highlight">API 토큰 별도 없음</span></div></div>
  <div class="info-box"><div class="info-label">일일 한도</div><div class="info-val">Pro <span class="highlight">5회</span> / Max <span class="highlight">15회</span> / Enterprise <span class="highlight">25회</span></div></div>
  <div class="info-box"><div class="info-label">로컬 파일</div><div class="info-val"><span class="warning">❌ 불가</span> — GitHub 레포 only</div></div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 08. 1인 → 팀 → 조직 확장 경로
# ─────────────────────────────────────────────────────────────────
html_08 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #fff; }
.wrap { padding: 44px 50px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 6px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 32px; }
.tiers { display: flex; align-items: stretch; gap: 24px; margin-bottom: 24px; }
.tier { flex: 1; border-radius: 16px; padding: 24px 22px; position: relative; overflow: hidden; }
.tier-1 { background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%); border: 2px solid #c4b5fd; }
.tier-2 { background: linear-gradient(135deg, #d1fae5 0%, #cffafe 100%); border: 2px solid #6ee7b7; }
.tier-3 { background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #fbbf24; }
.tier-label { font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 10px; }
.tier-1 .tier-label { color: #7c3aed; }
.tier-2 .tier-label { color: #059669; }
.tier-3 .tier-label { color: #b45309; }
.tier-icon { font-size: 36px; margin-bottom: 12px; }
.tier-title { font-size: 18px; font-weight: 800; color: #111827; margin-bottom: 12px; }
.tool-list { list-style: none; }
.tool-list li { font-size: 13px; color: #374151; padding: 5px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }
.tool-list li:last-child { border: none; }
.tool-list li strong { font-weight: 700; }
.arrow-col { display: flex; align-items: center; font-size: 24px; color: #d1d5db; }
.bottom { background: #f8f9fa; border-radius: 12px; padding: 16px 24px; }
.bottom-title { font-size: 13px; font-weight: 700; color: #374151; margin-bottom: 10px; }
.bottom-row { display: flex; gap: 24px; }
.bottom-item { flex: 1; font-size: 12px; color: #6b7280; line-height: 1.6; }
.bottom-item strong { color: #111827; display: block; font-size: 13px; margin-bottom: 2px; }
</style></head><body><div class="wrap">
<h1>자동화 확장 경로</h1>
<div class="sub">1인 마케터에서 조직 전체로 — 단계별 도구 선택 가이드</div>
<div class="tiers">
  <div class="tier tier-1">
    <div class="tier-label">STAGE 1 · 1인</div>
    <div class="tier-icon">👤</div>
    <div class="tier-title">나 혼자 자동화</div>
    <ul class="tool-list">
      <li>✅ <strong>Routines</strong> — 매주 자동 RFM</li>
      <li>✅ <strong>Slack MCP 커넥터</strong> — 결과 포스팅</li>
      <li>추가 비용 없음</li>
      <li>Pro 5회/일 충분</li>
    </ul>
  </div>
  <div class="arrow-col">→</div>
  <div class="tier tier-2">
    <div class="tier-label">STAGE 2 · 팀</div>
    <div class="tier-icon">👥</div>
    <div class="tier-title">팀원도 같이</div>
    <ul class="tool-list">
      <li>✅ <strong>Claude Code in Slack</strong></li>
      <li>팀원 각자 Pro 구독 필요</li>
      <li>@Claude 즉석 질문 가능</li>
      <li>API 별도 과금 없음</li>
    </ul>
  </div>
  <div class="arrow-col">→</div>
  <div class="tier tier-3">
    <div class="tier-label">STAGE 3 · 조직</div>
    <div class="tier-icon">🏢</div>
    <div class="tier-title">전사 공용 시스템</div>
    <ul class="tool-list">
      <li>✅ <strong>GitHub Actions</strong> — 팀 API 토큰</li>
      <li>✅ <strong>Agent SDK 봇</strong> — 실데이터 접근</li>
      <li>보안·법무 검토 필요</li>
      <li>엔지니어링팀 협업</li>
    </ul>
  </div>
</div>
<div class="bottom">
  <div class="bottom-title">📌 단계 전환 신호</div>
  <div class="bottom-row">
    <div class="bottom-item"><strong>1→2 전환 시점</strong>팀원이 "나도 Claude 에게 직접 물어보고 싶다"고 할 때</div>
    <div class="bottom-item"><strong>2→3 전환 시점</strong>팀원 구독 없음 · 회사 실데이터 GitHub 못 올릴 때</div>
    <div class="bottom-item"><strong>현재 권장</strong>4주차 수업은 Stage 1-2 집중. Stage 3 은 감만 잡기.</div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 09. 방식별 비용 비교
# ─────────────────────────────────────────────────────────────────
html_09 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #0f172a; }
.wrap { padding: 46px 56px; }
.title { color: #64748b; font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
h1 { color: #fff; font-size: 28px; font-weight: 800; margin-bottom: 36px; }
.bars { display: flex; flex-direction: column; gap: 20px; margin-bottom: 28px; }
.bar-row { display: flex; align-items: center; gap: 20px; }
.bar-label { width: 180px; text-align: right; flex-shrink: 0; }
.bar-name { color: #fff; font-size: 14px; font-weight: 600; }
.bar-sub { color: #64748b; font-size: 11px; }
.bar-track { flex: 1; height: 44px; background: rgba(255,255,255,0.05); border-radius: 8px; overflow: hidden; position: relative; }
.bar-fill { height: 100%; border-radius: 8px; display: flex; align-items: center; padding: 0 16px; }
.bar-val { color: #fff; font-size: 15px; font-weight: 800; }
.bar-desc { color: rgba(255,255,255,0.6); font-size: 11px; margin-left: 8px; }
.note-row { display: flex; gap: 16px; }
.note-box { flex: 1; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px; padding: 14px 16px; }
.note-label { font-size: 11px; color: #64748b; font-weight: 700; letter-spacing: 1px; margin-bottom: 6px; }
.note-val { font-size: 13px; color: #e2e8f0; }
</style></head><body><div class="wrap">
<div class="title">비용 비교</div>
<h1>방식별 월 예상 비용 (소규모 기준)</h1>
<div class="bars">
  <div class="bar-row">
    <div class="bar-label"><div class="bar-name">Routines</div><div class="bar-sub">마케터 1인 권장</div></div>
    <div class="bar-track">
      <div class="bar-fill" style="width:8%;background:linear-gradient(90deg,#7c3aed,#8b5cf6)">
        <span class="bar-val">~$5</span>
      </div>
    </div>
  </div>
  <div class="bar-row">
    <div class="bar-label"><div class="bar-name">Claude Code in Slack</div><div class="bar-sub">기존 Pro 구독 활용</div></div>
    <div class="bar-track">
      <div class="bar-fill" style="width:3%;background:linear-gradient(90deg,#059669,#10b981)">
        <span class="bar-val" style="white-space:nowrap">$0 추가</span>
      </div>
    </div>
  </div>
  <div class="bar-row">
    <div class="bar-label"><div class="bar-name">GitHub Actions</div><div class="bar-sub">팀 공용 API 토큰</div></div>
    <div class="bar-track">
      <div class="bar-fill" style="width:30%;background:linear-gradient(90deg,#1d4ed8,#3b82f6)">
        <span class="bar-val">$5~$30</span><span class="bar-desc">API 토큰 과금</span>
      </div>
    </div>
  </div>
  <div class="bar-row">
    <div class="bar-label"><div class="bar-name">자체 Slack 봇</div><div class="bar-sub">사내 실데이터 필요 시</div></div>
    <div class="bar-track">
      <div class="bar-fill" style="width:75%;background:linear-gradient(90deg,#b45309,#f59e0b)">
        <span class="bar-val">$30~$100</span><span class="bar-desc">API + 서버 $15</span>
      </div>
    </div>
  </div>
</div>
<div class="note-row">
  <div class="note-box">
    <div class="note-label">💜 1인 마케터 권장 조합</div>
    <div class="note-val">Routines + Claude Code in Slack<br>= 추가 지출 <strong>거의 $0</strong></div>
  </div>
  <div class="note-box">
    <div class="note-label">📊 비용이 오르는 시점</div>
    <div class="note-val">팀 공용 자동화 전환 시<br>GitHub Actions or 자체봇</div>
  </div>
  <div class="note-box">
    <div class="note-label">⚡ Routines 과금 구조</div>
    <div class="note-val">$0.08/hr × 실행시간<br>+ 구독 토큰 소진</div>
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 10. Claude Code CLI vs Agent SDK
# ─────────────────────────────────────────────────────────────────
html_10 = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
""" + COMMON_CSS + """
body { background: #f8f9fa; }
.wrap { padding: 44px 50px; }
h1 { font-size: 26px; font-weight: 800; color: #111827; margin-bottom: 6px; }
.sub { font-size: 13px; color: #6b7280; margin-bottom: 30px; }
.two-col { display: flex; gap: 24px; margin-bottom: 24px; }
.col { flex: 1; border-radius: 16px; padding: 28px 26px; }
.col-cli { background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%); border: 2px solid #a78bfa; }
.col-sdk { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #86efac; }
.col-head { font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 12px; }
.col-cli .col-head { color: #7c3aed; }
.col-sdk .col-head { color: #16a34a; }
.col-title { font-size: 20px; font-weight: 800; color: #111827; margin-bottom: 8px; }
.col-sub { font-size: 13px; color: #6b7280; margin-bottom: 20px; }
.analogy { background: rgba(255,255,255,0.6); border-radius: 10px; padding: 12px 14px;
           font-size: 13px; color: #374151; margin-bottom: 16px; line-height: 1.5; }
.analogy strong { color: #111827; }
.feat-list { list-style: none; }
.feat-list li { font-size: 13px; color: #374151; padding: 6px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }
.feat-list li:last-child { border: none; }
.vs-circle { display: flex; align-items: center; justify-content: center; width: 50px; flex-shrink: 0;
             font-size: 16px; font-weight: 900; color: #9ca3af; }
.bottom { background: #111827; border-radius: 14px; padding: 18px 24px; }
.bottom-text { color: #e5e7eb; font-size: 14px; line-height: 1.7; }
.bottom-text strong { color: #a78bfa; }
</style></head><body><div class="wrap">
<h1>Claude Code CLI vs Agent SDK</h1>
<div class="sub">같은 Claude — 두 가지 접근법. 익숙해지면 자연스럽게 SDK 로 이어집니다.</div>
<div class="two-col">
  <div class="col col-cli">
    <div class="col-head">CLAUDE CODE CLI</div>
    <div class="col-title">내가 직접 대화</div>
    <div class="col-sub">터미널·IDE 에서 Claude 와 대화하는 인터페이스</div>
    <div class="analogy"><strong>비유</strong>: 다이슨 청소기를<br>내가 직접 들고 청소하는 것</div>
    <ul class="feat-list">
      <li>💬 대화형 인터랙션</li>
      <li>🖥️ 터미널 / IDE 에서 실행</li>
      <li>👤 내가 항상 앞에 있어야 함</li>
      <li>🎯 탐색·분석·개발 작업에 최적</li>
    </ul>
  </div>
  <div class="vs-circle">VS</div>
  <div class="col col-sdk">
    <div class="col-head">CLAUDE AGENT SDK</div>
    <div class="col-title">내 시스템에 내장</div>
    <div class="col-sub">Claude 를 내가 만든 프로그램의 두뇌로 심는 라이브러리</div>
    <div class="analogy"><strong>비유</strong>: 다이슨 모터를 로봇에 달아<br>자동으로 돌리는 것</div>
    <ul class="feat-list">
      <li>🤖 이벤트·요청에 자동 반응</li>
      <li>🐍 Python 코드로 제어</li>
      <li>📂 로컬 파일·DB 직접 접근</li>
      <li>🔁 24시간 서버 상주 가능</li>
    </ul>
  </div>
</div>
<div class="bottom">
  <div class="bottom-text">
    💡 <strong>CLI 로 익숙해지면 SDK 로의 전환이 자연스럽습니다.</strong>
    CLI 로 "이런 분석을 Claude 가 해줬으면 좋겠다" 를 확인한 뒤 → SDK 로 그 로직을 시스템에 내장.
    4주차까지는 CLI 중심. Agent SDK 는 "이런 것도 된다" 감잡기.
  </div>
</div>
</div></body></html>"""

# ─────────────────────────────────────────────────────────────────
# 렌더링
# ─────────────────────────────────────────────────────────────────
IMAGES = [
    ("4w_01_journey.png",     html_01),
    ("4w_02_manual_vs_auto.png", html_02),
    ("4w_03_routines_arch.png",  html_03),
    ("4w_04_comparison.png",     html_04),
    ("4w_05_timeline.png",       html_05),
    ("4w_06_mcp_connector.png",  html_06),
    ("4w_07_slack_arch.png",     html_07),
    ("4w_08_scale_path.png",     html_08),
    ("4w_09_cost_compare.png",   html_09),
    ("4w_10_cli_vs_sdk.png",     html_10),
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
