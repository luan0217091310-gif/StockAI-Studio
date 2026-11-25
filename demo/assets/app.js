/* =====================================================================
   StockAI Studio — Studio demo (chạy hoàn toàn trên trình duyệt)
   Mọi dịch vụ ngoài đều mô phỏng; logic nghiệp vụ dùng engine.js.
   ===================================================================== */
(() => {
"use strict";
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const {fmt, fmtSigned, dmy, ymd, esc, pad, sleep, NFC, SESSION_LABEL, DISCLAIMER, AI_DECL, BANNED, HOOKS, wc} = SAI;
const store = {
  get(k, d) { try { const v = localStorage.getItem("stockai." + k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("stockai." + k, JSON.stringify(v)); return true; } catch { return false; } }
};

/* ---------- Icon ---------- */
const I = {
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.14v13.72a1 1 0 0 0 1.52.85l11-6.86a1 1 0 0 0 0-1.7l-11-6.86A1 1 0 0 0 8 5.14Z"/></svg>',
  pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>',
  stop: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
  rss: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1.5"/></svg>',
  ai: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/></svg>',
  mic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3"/></svg>',
  film: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7 3v18M17 3v18M3 8h4M3 16h4M17 8h4M17 16h4"/></svg>',
  send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="m5 12 5 5 9-10"/></svg>',
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  video: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="m10 9 5 3-5 3Z"/></svg>',
  telegram: '<svg viewBox="0 0 24 24" fill="#29a9eb"><path d="M21.9 4.6 18.8 19.3c-.2 1-.8 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.8 8.8-7.9c.4-.3-.1-.5-.6-.2L6.8 13.2 2.2 11.8c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.5 1.2Z"/></svg>',
  facebook: '<svg viewBox="0 0 24 24" fill="#1877f2"><path d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12Z"/></svg>',
  youtube: '<svg viewBox="0 0 24 24" fill="#ff0033"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8ZM9.6 15.6V8.4l6.2 3.6-6.2 3.6Z"/></svg>',
  tiktok: '<svg viewBox="0 0 24 24" fill="#e5e7eb"><path d="M19.6 6.7a4.8 4.8 0 0 1-3.8-4.2V2h-3.4v13.7a2.9 2.9 0 0 1-5.2 1.7 2.9 2.9 0 0 1 3.2-4.5V9.4a6.3 6.3 0 0 0-5.4 10.7 6.3 6.3 0 0 0 10.8-4.4V8.7a8.2 8.2 0 0 0 4.8 1.5V6.8l-1-.1Z"/></svg>',
  nav: {dash: "▦", char: "◉", lib: "▶", sched: "◷", set: "⚙"}
};
const PF = {telegram: "Telegram", facebook: "Facebook Reels", youtube: "YouTube Shorts", tiktok: "TikTok"};
const PRIV = {telegram: ["channel"], facebook: ["published"], youtube: ["private", "unlisted", "public"], tiktok: ["SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS", "PUBLIC_TO_EVERYONE"]};
const STATUS = {PENDING: ["Chờ", "b-dry"], RUNNING: ["Đang chạy", "b-run"], WAITING_APPROVAL: ["Chờ duyệt", "b-wait"], PUBLISHING: ["Đang đăng", "b-run"],
  COMPLETED: ["Hoàn tất", "b-ok"], FAILED: ["Lỗi", "b-fail"], CANCELLED: ["Đã hủy", "b-fail"], SKIPPED: ["Bỏ qua", "b-dry"]};
const badge = s => { const [l, c] = STATUS[s] || [s, "b-dry"]; return `<span class="badge ${c}"><span class="dot"></span>${l}</span>`; };

/* ---------- Toast ---------- */
function toast(msg, kind = "ok") {
  const t = document.createElement("div"); t.className = "toast " + kind;
  t.innerHTML = `<span class="ti">${{ok: "✓", warn: "!", err: "×", info: "i"}[kind]}</span><div>${esc(msg)}</div>`;
  $("#toasts").appendChild(t); setTimeout(() => { t.classList.add("out"); setTimeout(() => t.remove(), 300); }, 4200);
}

/* ---------- Trạng thái ---------- */
let jobs = store.get("jobs", []);
let schedules = store.get("schedules", [
  {id: 1, name: "Bản tin trước phiên", session_type: "PRE_MARKET", time: "07:30", days: "mon-fri", platforms: ["telegram"], require_approval: true, is_active: true, last_run_at: null, last_status: null},
  {id: 2, name: "Tổng kết sau phiên", session_type: "POST_MARKET", time: "15:30", days: "mon-fri", platforms: ["telegram", "youtube"], require_approval: true, is_active: true, last_run_at: null, last_status: null}]);
let settings = {mode: "DEMO", avatar_provider: "demo", voice: "vi-VN-HoaiMyNeural", rate: 5, ...store.get("settings", {})};
const secrets = {}; // chỉ trong bộ nhớ tab
let running = null, selectedJob = null, session = "PRE_MARKET";
const saveJobs = () => store.set("jobs", jobs.slice(0, 30).map(({_assets, ...r}) => r));
const saveSched = () => store.set("schedules", schedules);
const saveSettings = () => store.set("settings", settings);
// R-RUN-4: job còn RUNNING từ lần trước → FAILED/INTERRUPTED
jobs.forEach(j => { if (j.status === "RUNNING" || j.status === "PUBLISHING") { j.status = "FAILED"; j.error_code = "INTERRUPTED"; j.error_message = "Trang bị đóng khi job đang chạy."; } });
saveJobs();
const voiceOpts = () => ({voice: settings.voice, rate: settings.rate});

/* ---------- Điều hướng ---------- */
const TITLES = {
  dash: ["Bảng điều khiển", "Chạy quy trình 5 bước và xem kết quả theo thời gian thực"],
  char: ["Nhân vật & giọng", "Ảnh MC, bản ghi đồng ý, nhà cung cấp avatar và giọng đọc"],
  lib: ["Kho nội dung", "Xem lại video, sửa caption, duyệt và đăng"],
  sched: ["Lịch tự động", "Đặt giờ chạy cố định, tự chạy bù khi lỡ lịch"],
  set: ["Cài đặt", "Chế độ vận hành, khóa dịch vụ và kiểm tra môi trường"]
};
function switchTab(t) {
  $$(".nav-i[data-tab]").forEach(b => b.classList.toggle("on", b.dataset.tab === t));
  $$(".page").forEach(s => s.classList.toggle("on", s.id === "tab-" + t));
  $("#pgTitle").textContent = TITLES[t][0]; $("#pgSub").textContent = TITLES[t][1];
  if (t !== "dash") dashPlayer.stop();
  if (t === "lib") renderLib(); if (t === "sched") renderSched(); if (t === "set") renderSettings(); if (t === "char") drawAvPrev();
  $("#content").scrollTop = 0;
  history.replaceState(null, "", "#" + t);
}
$$(".nav-i[data-tab]").forEach(b => b.onclick = () => switchTab(b.dataset.tab));
$("#collapse").onclick = () => { document.body.classList.toggle("collapsed"); store.set("collapsed", document.body.classList.contains("collapsed")); };
if (store.get("collapsed", false)) document.body.classList.add("collapsed");
document.addEventListener("pointermove", e => { const el = e.target.closest?.(".spot"); if (!el) return; const r = el.getBoundingClientRect(); el.style.setProperty("--mx", `${e.clientX - r.left}px`); el.style.setProperty("--my", `${e.clientY - r.top}px`); }, {passive: true});

/* ================= BẢNG ĐIỀU KHIỂN ================= */
const STEPS = [["Thu thập", I.rss], ["AI biên tập", I.ai], ["Giọng & avatar", I.mic], ["Dựng video", I.film], ["Xuất bản", I.send]];
const RANGE = [[0, 20], [20, 35], [35, 70], [70, 95], [95, 100]];
$("#stepper").innerHTML = STEPS.map(([n, ic], i) => `<div class="stp" id="st${i}"><div class="top"><span class="ic">${ic}</span><div><div class="n">BƯỚC ${i + 1}</div><div class="t">${n}</div></div></div><div class="st">Chờ</div><div class="bar"><i></i></div></div>`).join("");
function setStep(i, state, frac = 0, msg) {
  const el = $("#st" + i); el.className = "stp " + (state || "");
  el.querySelector(".bar i").style.width = (state === "done" ? 100 : frac * 100) + "%";
  el.querySelector(".ic").innerHTML = state === "done" ? I.check : state === "err" ? I.x : STEPS[i][1];
  if (msg !== undefined) el.querySelector(".st").textContent = msg;
}
function setOverall(pct, label) { $("#ovBar").style.width = pct + "%"; $("#ovPct").textContent = Math.round(pct) + "%"; if (label) $("#ovLbl").textContent = label; }
function resetSteps() { STEPS.forEach((_, i) => setStep(i, "", 0, "Chờ")); setOverall(0, "Chưa chạy"); }

let logLines = [], logFilter = "";
function termWrite(level, msg) {
  const ts = new Date().toLocaleTimeString("vi-VN", {hour12: false});
  const term = $("#term"); if (!logLines.length) term.innerHTML = "";
  logLines.push({ts, level, msg});
  if (logFilter && level !== logFilter) return;
  appendLine(ts, level, msg);
}
function appendLine(ts, level, msg) {
  const term = $("#term"), d = document.createElement("div"); d.className = "ln " + level;
  d.innerHTML = `<span class="ts">${ts}</span><span class="lv">${level}</span><span class="msg">${esc(msg)}</span>`;
  term.appendChild(d); if (term.children.length > 1200) term.firstChild.remove(); term.scrollTop = term.scrollHeight;
}
$$("#logFilter button").forEach(b => b.onclick = () => { logFilter = b.dataset.l; $$("#logFilter button").forEach(x => x.classList.toggle("on", x === b));
  $("#term").innerHTML = ""; logLines.filter(l => !logFilter || l.level === logFilter).forEach(l => appendLine(l.ts, l.level, l.msg)); });
$("#copyLog").onclick = () => { navigator.clipboard?.writeText(logLines.map(l => `[${l.ts}] ${l.level.padEnd(7)} ${l.msg}`).join("\n")); toast("Đã sao chép log"); };
$("#clrLog").onclick = () => { logLines = []; $("#term").innerHTML = '<div class="empty">Log trống.</div>'; };
$$("#sessSeg button").forEach(b => b.onclick = () => { session = b.dataset.v; $$("#sessSeg button").forEach(x => x.classList.toggle("on", x === b)); });

/* Trình phát dashboard */
const dashPlayer = SAI.makePlayer($("#dashCanvas"), {
  onTime: (t, D) => { $("#dashSeek").value = Math.round(t / D * 1000); $("#dashSeek").style.setProperty("--fill", (t / D * 100) + "%"); $("#dashTime").textContent = `${mmss(t)} / ${mmss(D)}`; },
  onState: p => $("#dashPlay").innerHTML = p ? I.pause : I.play, voice: voiceOpts});
const mmss = s => `${Math.floor(s / 60)}:${pad(Math.floor(s % 60))}`;
$("#dashPlay").innerHTML = I.play;
$("#dashPlay").onclick = () => { dashPlayer.speakOn = $("#dashVoice").checked; dashPlayer.toggle(); };
$("#dashSeek").oninput = e => dashPlayer.seek(e.target.value / 1000);
$("#dashSafe").onchange = e => { dashPlayer.safe = e.target.checked; dashPlayer.draw(); };
function loadDash(job) {
  dashPlayer.load(job); $("#pvBadge").hidden = !job; $("#toLib").disabled = !job;
  $("#pvTitle").innerHTML = job ? `${esc(job.video_title)}<div style="margin-top:6px">${badge(job.status)}</div>` : "Xem trước 9:16";
}
$("#toLib").onclick = () => { const j = dashPlayer.job; if (j) { switchTab("lib"); openDrawer(j.id); } };

/* Chạy pipeline */
async function runPipeline(session_type, trigger = "MANUAL", schedule = null) {
  if (running) { toast("Đang có job chạy (409) — vui lòng chờ.", "warn"); return null; }
  const now = new Date();
  const job = {id: SAI.uuid(), run_date: ymd(now), session_type, trigger, schedule_id: schedule?.id ?? null, mode: settings.mode, status: "RUNNING",
    current_step: 0, progress_pct: 0, created_at: now.toISOString(), events: [], publish_logs: [], platforms: schedule?.platforms || ["telegram", "facebook", "youtube", "tiktok"],
    require_approval: schedule ? schedule.require_approval : true};
  running = job; const ctl = {cancelled: false}; job._ctl = ctl;
  logLines = []; $("#term").innerHTML = ""; resetSteps(); setRunUI(true);
  const log = async (level, msg, step = job.current_step) => { job.events.push({ts: new Date().toISOString(), step, level, message: msg}); termWrite(level, msg); await sleep(level === "DEBUG" ? 60 : 150); if (ctl.cancelled) throw new Error("CANCELLED"); };
  const prog = (i, f, msg) => { const [a, b] = RANGE[i]; job.progress_pct = Math.round(a + (b - a) * f); setOverall(job.progress_pct, `Bước ${i + 1}/5 · ${STEPS[i][0]}`); setStep(i, f >= 1 ? "done" : "doing", f, msg); };
  try {
    await log("INFO", `Bắt đầu job ${job.id.slice(0, 8)} · ${SESSION_LABEL[session_type]} · chế độ ${settings.mode} · kích hoạt ${trigger}`);
    // B1
    job.current_step = 1; prog(0, .05, "Tải RSS…");
    await log("INFO", "B1 · Tải RSS song song: CafeF, Vietstock, VnEconomy (bản web dùng fixture, không gọi mạng)");
    const news = await SAI.collectNews(now, log); prog(0, .45, `${news.length} tin sau lọc`);
    await log("SUCCESS", `Giữ lại ${news.length} tin sau lọc chủ đề + chống trùng; xếp hạng 0,5·độ mới + 0,3·từ khóa + 0,2·số nguồn`);
    news.slice(0, 3).forEach((n, i) => termWrite("DEBUG", `  #${i} [${n.score}] ${n.title} — ${n.source}`));
    await log("INFO", "Chuỗi provider thị trường: PublicVci → Cache → Synthetic");
    await log("WARN", "PublicVci: bản web không gọi mạng · Cache: chưa có snapshot thật");
    const market = SAI.buildSnapshot(SAI.syntheticBars(now, 60, jobs.length), "Dữ liệu minh họa", "SYNTHETIC");
    job.market = market; job.news = news; job.data_quality = market.data_quality; prog(0, .8, "Tính chỉ báo");
    await log("WARN", "Dùng dữ liệu MINH HỌA (SYNTHETIC) → biểu đồ/video có watermark, bước Xuất bản chỉ dry-run (R-DATA-2, R-PUB-1)");
    await log("SUCCESS", `VN-Index ${fmt(market.close)} (${fmtSigned(market.change_pct)}%) · SMA20 ${fmt(market.sma20)} · RSI14 Wilder ${fmt(market.rsi14)} · HT ${fmt(market.support20)} · KC ${fmt(market.resistance20)}`);
    await log("SUCCESS", "Đã vẽ chart.png 1080×660 (60 nến + khối lượng + SMA20 + hỗ trợ/kháng cự)"); prog(0, 1, `${news.length} tin · 60 phiên`);
    updateCards(market);
    // B2
    job.current_step = 2; prog(1, .1, "Dựng ngữ cảnh");
    const ctx = {run_date: job.run_date, session_type, market, news, hook_style: HOOKS[now.getDate() % HOOKS.length]};
    await log("INFO", `B2 · Hook hôm nay: “${ctx.hook_style}”`);
    await log("WARN", secrets.gemini_api_key ? "Gemini: bản web không gọi API thật → dùng TemplateFallbackProvider" : "Gemini: chưa có khóa API → dùng TemplateFallbackProvider");
    const script = SAI.templateScript(ctx); prog(1, .5, "Hậu kiểm");
    const fake = {...script, video_script: script.video_script.replace("Xin chào", "VN-Index có thể lên 1.999,99 điểm. Xin chào")};
    const fakeErr = SAI.factcheck(fake, ctx);
    await log(fakeErr.length ? "SUCCESS" : "ERROR", `Tự kiểm factcheck: chèn số bịa “1.999,99” → ${fakeErr.length ? "bị chặn ✓" : "KHÔNG bị chặn ✗"}`);
    const errs = SAI.postcheck(script, ctx);
    job.factcheck_passed = errs.length ? 0 : 1; job.llm_provider = "template_fallback"; job.llm_model = "-";
    if (errs.length) { errs.forEach(e => termWrite("ERROR", e)); throw Object.assign(new Error("Hậu kiểm kịch bản thất bại"), {code: "SCRIPT_INVALID"}); }
    job.script = script; job.video_title = script.video_title; job.social_post_text = script.social_post_text; job.ctx = ctx;
    await log("SUCCESS", `Kịch bản hợp lệ: ${wc(script.video_script)} từ · 2 kịch bản · ${script.selected_news.length} tin · factcheck số liệu ĐẠT · có miễn trừ + khai báo AI`); prog(1, 1, `${wc(script.video_script)} từ · factcheck ✓`);
    // B3
    job.current_step = 3; prog(2, .05, "Chuẩn hóa TTS");
    await log("INFO", "B3 · Chuẩn hóa văn bản cho TTS (% → “phần trăm”, +/− điểm → tăng/giảm, bỏ emoji)");
    await log("INFO", `TTS ${settings.voice} rate ${settings.rate >= 0 ? "+" : ""}${settings.rate}% (bản thật: edge-tts boundary="WordBoundary")`);
    const words = SAI.wordTimings(SAI.viNormalize(script.video_script), settings.rate); job.words = words;
    job.duration_s = +((words.at(-1).end_ms + 600) / 1000).toFixed(2); prog(2, .4, `voice.mp3 ${fmt(job.duration_s, 1)}s`);
    await log(job.duration_s >= 45 && job.duration_s <= 95 ? "SUCCESS" : "WARN", `voice.mp3 ≈ ${fmt(job.duration_s, 1)} giây (yêu cầu 45–95 giây) · ${words.length} WordTiming`);
    job.cues = SAI.buildCues(words); job.srt = SAI.toSRT(job.cues); job.ass = SAI.toASS(job.cues);
    await log("SUCCESS", `Phụ đề: ${job.cues.length} cue, tối đa 2 dòng, mỗi dòng ≤ 800 px → subs.srt + subs.ass`); prog(2, .6, `${job.cues.length} cue phụ đề`);
    const consent = store.get("avatar", null)?.consent;
    if (settings.avatar_provider !== "demo") await log("WARN", `Provider “${settings.avatar_provider}” trả phí: bản web không gọi API → dùng DemoMotion (chi phí ước tính vẫn được ghi)`);
    job.avatar_provider = "DemoMotion"; job.avatar_has_lipsync = false; job.est_cost_usd = 0;
    await log("INFO", `Avatar: ${consent ? "ảnh người dùng (" + consent.subject_name + ", đã có bản ghi đồng ý)" : "ảnh mẫu (is_placeholder=1)"} → crop 1080×976`);
    await log("SUCCESS", "DemoMotion: nhịp thở 6 giây, 30 fps, khớp độ dài audio ± 0,1 giây (R-AV-2) · chi phí 0 đồng"); prog(2, 1, "avatar.mp4 · 0 đồng");
    // B4
    job.current_step = 4; prog(3, .05, "Giai đoạn A");
    await log("INFO", "B4 · Giai đoạn A: base.png, news_card_1..3.png, ticker_strip.png, ai_intro.png, disclaimer.png");
    job._assets = null; SAI.prepareAssets(job); prog(3, .4, "B-roll + xfade");
    await log("INFO", `B-roll: chart → card1 → card2 → card3 → chart, xfade 0,4 giây, mỗi đoạn ≈ ${fmt(job._assets.segLen, 1)} giây`);
    await log("INFO", "Giai đoạn B: overlay theo layout v3 (header 120–220, ticker 220–280, B-roll 280–940, avatar 944–1920, phụ đề đáy y=1400)");
    loadDash(job); prog(3, .8, "Kiểm tra ffprobe");
    await log("SUCCESS", "Kiểm tra ffprobe (mô phỏng): 1080×1920 · 30 fps · có audio · metadata comment=\"AI-generated content…\" · ai_label_applied=1");
    job.ai_label_applied = 1; prog(3, 1, `final.mp4 ${fmt(job.duration_s, 1)}s`);
    // B5
    job.current_step = 5; prog(4, .2, "Xuất bản");
    if (job.require_approval) { job.status = "WAITING_APPROVAL"; await log("WARN", "B5 · Chờ duyệt (human-in-the-loop) → mở Kho nội dung để xem, sửa caption và Duyệt & Đăng"); prog(4, .5, "Chờ bạn duyệt"); }
    else { await log("INFO", "B5 · Tự đăng (không cần duyệt), trừ TikTok"); await publishJob(job, job.platforms.filter(p => p !== "tiktok"), {}, log); prog(4, 1, "Đã xử lý"); }
    job.completed_at = new Date().toISOString();
    await log("SUCCESS", `Hoàn tất · trạng thái ${STATUS[job.status][0]} · video ${fmt(job.duration_s, 1)} giây`);
    setOverall(job.status === "WAITING_APPROVAL" ? 97 : 100, job.status === "WAITING_APPROVAL" ? "Đang chờ bạn duyệt" : "Hoàn tất");
    toast(job.status === "WAITING_APPROVAL" ? "Video đã dựng xong — đang chờ bạn duyệt" : "Job hoàn tất");
  } catch (e) {
    if (e.message === "CANCELLED") { job.status = "CANCELLED"; termWrite("WARN", "Người dùng đã hủy job"); setStep(Math.max(0, job.current_step - 1), "err", 1, "Đã hủy"); setOverall(job.progress_pct, "Đã hủy"); }
    else { job.status = "FAILED"; job.error_code = e.code || "UNEXPECTED"; job.error_message = e.message; termWrite("ERROR", e.message); setStep(Math.max(0, job.current_step - 1), "err", 1, "Lỗi"); setOverall(job.progress_pct, "Lỗi"); }
  } finally {
    running = null; delete job._ctl; setRunUI(false);
    if (job.market) { jobs.unshift(job); saveJobs(); }
    if (schedule) { schedule.last_run_at = new Date().toISOString(); schedule.last_status = job.status; saveSched(); renderSched(); }
    if (job.script) loadDash(job);
    selectedJob = job.id; refreshAll();
  }
  return job;
}
function setRunUI(on) {
  const b = $("#runBtn"); b.classList.toggle("busy", on);
  b.innerHTML = on ? `${I.stop}<span>Hủy job</span>` : `${I.play}<span>Chạy quy trình</span>`;
  $("#pulse").classList.toggle("busy", on); $("#engineSt").textContent = on ? "Đang chạy job…" : "Sẵn sàng";
}
$("#runBtn").onclick = () => { if (running) { running._ctl.cancelled = true; return; } runPipeline(session); };

/* KPI */
function updateCards(m) {
  if (!m) return;
  $("#cIdx").textContent = fmt(m.close);
  $("#cChg").innerHTML = `<span class="${m.change >= 0 ? "up" : "down"}">${m.change >= 0 ? "▲" : "▼"} ${fmtSigned(m.change)} (${fmtSigned(m.change_pct)}%)</span> · ${m.session_date.split("-").reverse().join("/")}`;
  $("#qBadge").textContent = m.data_quality === "SYNTHETIC" ? "minh họa" : m.data_quality === "CACHED" ? "cached" : "live";
  $("#qBadge").className = "badge " + (m.data_quality === "LIVE" ? "b-live" : m.data_quality === "CACHED" ? "b-cache" : "b-syn");
  drawSpark(m.bars.slice(-30).map(b => b.close), m.change >= 0);
}
function drawSpark(vals, up) {
  const c = $("#spark"), g = c.getContext("2d"), W = c.width, H = c.height, lo = Math.min(...vals), hi = Math.max(...vals);
  g.clearRect(0, 0, W, H);
  const X = i => i / (vals.length - 1) * W, Y = v => H - 6 - (v - lo) / (hi - lo || 1) * (H - 14);
  const col = up ? "16,185,129" : "244,63,94", gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, `rgba(${col},.35)`); gr.addColorStop(1, `rgba(${col},0)`);
  g.beginPath(); vals.forEach((v, i) => i ? g.lineTo(X(i), Y(v)) : g.moveTo(X(i), Y(v))); g.lineTo(W, H); g.lineTo(0, H); g.fillStyle = gr; g.fill();
  g.beginPath(); vals.forEach((v, i) => i ? g.lineTo(X(i), Y(v)) : g.moveTo(X(i), Y(v))); g.strokeStyle = `rgb(${col})`; g.lineWidth = 2; g.stroke();
}
function nextRun() {
  const now = new Date(); let best = null;
  for (const s of schedules.filter(s => s.is_active)) {
    const [h, mi] = s.time.split(":").map(Number);
    for (let d = 0; d < 8; d++) { const c = new Date(now); c.setDate(c.getDate() + d); c.setHours(h, mi, 0, 0);
      if (c <= now) continue; if (s.days === "mon-fri" && (c.getDay() === 0 || c.getDay() === 6)) continue;
      if (!best || c < best.at) best = {at: c, s}; break; }
  }
  return best;
}
const DOW = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
function tick() {
  const n = nextRun();
  if (n) { const sec = Math.floor((n.at - new Date()) / 1000);
    $("#cNext").textContent = n.s.time;
    $("#cCount").textContent = `còn ${pad(Math.floor(sec / 3600))}:${pad(Math.floor(sec / 60) % 60)}:${pad(sec % 60)} · ${DOW[n.at.getDay()]}`;
    $("#cRing").style.setProperty("--p", Math.max(2, 100 - Math.min(100, sec / 864)).toFixed(1)); $("#cRingT").textContent = sec >= 3600 ? Math.floor(sec / 3600) + "h" : Math.ceil(sec / 60) + "p"; }
  else { $("#cNext").textContent = "--:--"; $("#cCount").textContent = "Chưa có lịch đang bật"; $("#cRingT").textContent = "—"; }
  // Bộ lập lịch: kích hoạt khi tới giờ (độ trễ cho phép 60 giây)
  const now = new Date();
  for (const s of schedules.filter(s => s.is_active)) {
    const [h, mi] = s.time.split(":").map(Number), at = new Date(now); at.setHours(h, mi, 0, 0);
    if (s.days === "mon-fri" && (now.getDay() === 0 || now.getDay() === 6)) continue;
    const diff = now - at, key = `${s.id}@${ymd(now)}T${s.time}`;
    if (diff >= 0 && diff < 60000 && s._fired !== key && !running) { s._fired = key; toast(`Đến giờ lịch “${s.name}” — tự chạy quy trình`, "info"); switchTab("dash"); runPipeline(s.session_type, "SCHEDULE", s); }
  }
}
function refreshAll() {
  $("#cVid").textContent = jobs.filter(j => j.ai_label_applied).length;
  const w = jobs.filter(j => j.status === "WAITING_APPROVAL").length;
  $("#cWait").innerHTML = w ? `<span class="warn">${w} chờ duyệt</span>` : "0 chờ duyệt";
  $("#navWait").hidden = !w; $("#navWait").textContent = w;
  const prod = settings.mode === "PRODUCTION";
  $("#cMode").textContent = prod ? "Production" : "Demo";
  $("#cCost").textContent = prod ? "Bản web vẫn không gọi API thật" : "0 đồng · không gọi API trả phí";
  $("#modeCard").innerHTML = prod ? `<b><span class="badge b-wait">PRODUCTION</span> Cấu hình thử</b>Bản web không thể đăng thật — cần ứng dụng desktop (FastAPI + FFmpeg).`
    : `<b><span class="badge b-ai">DEMO</span> Bản chạy trên trình duyệt</b>Mọi dịch vụ ngoài đều mô phỏng. Không gửi dữ liệu ra ngoài, không đăng bài thật.`;
  if (jobs[0]?.market) updateCards(jobs[0].market);
  if ($("#tab-lib").classList.contains("on")) renderLib();
}
function voiceNotice() {
  if (!("speechSynthesis" in window) || SAI.viVoices().length || store.get("hideVoiceNote", false)) { $("#voiceNotice").innerHTML = ""; return; }
  $("#voiceNotice").innerHTML = `<div class="notice info"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg><span>Trình duyệt chưa có giọng tiếng Việt — phần đọc thử sẽ dùng giọng mặc định. Mở bằng <b>Microsoft Edge</b> để nghe giọng HoaiMy/NamMinh. Video vẫn dựng bình thường.</span><button class="x" id="hideVN">${I.x.replace("<svg", '<svg width="16" height="16"')}</button></div>`;
  $("#hideVN").onclick = () => { store.set("hideVoiceNote", true); voiceNotice(); };
}

/* ================= NHÂN VẬT & GIỌNG ================= */
function drawAvPrev() {
  const c = $("#avPrev"), g = c.getContext("2d");
  g.drawImage(SAI.currentAvatar(), 0, 0, 1080, 976);
  // vùng phụ đề trong khung avatar: y 1240–1400 → 296–456; vùng bị che y ≥ 1440 → ≥ 496
  g.strokeStyle = "rgba(250,204,21,.95)"; g.setLineDash([16, 12]); g.lineWidth = 4; g.strokeRect(140, 296, 800, 160); g.setLineDash([]);
  g.fillStyle = "rgba(250,204,21,.95)"; g.font = `700 26px ${SAI.FONT}`; g.fillText("Phụ đề (y 1240–1400)", 150, 286);
  const gr = g.createLinearGradient(0, 496, 0, 976); gr.addColorStop(0, "rgba(244,63,94,.35)"); gr.addColorStop(1, "rgba(244,63,94,.18)");
  g.fillStyle = gr; g.fillRect(0, 496, 1080, 480); g.fillStyle = "#fff"; g.font = `700 28px ${SAI.FONT}`; g.fillText("Từ đây xuống bị UI TikTok/Reels che (y ≥ 1440)", 30, 540);
}
let pendingImg = null;
function setAvStatus() {
  const a = store.get("avatar", null);
  $("#avStatus").innerHTML = a ? `<span class="badge b-ok"><span class="dot"></span>Đang dùng ảnh của ${esc(a.consent.subject_name)}</span> <span class="tiny faint">đồng ý ghi nhận ${new Date(a.consent.created_at).toLocaleString("vi-VN")}</span>`
    : `<span class="badge b-dry">Ảnh mẫu</span> <span class="tiny faint">do app tự vẽ (is_placeholder=1)</span>`;
}
function handleFile(file) {
  if (!file || !file.type.startsWith("image/")) return toast("Vui lòng chọn file ảnh", "err");
  const r = new FileReader(); r.onload = () => { const im = new Image(); im.onload = () => {
    pendingImg = {im}; if (im.width < 720) toast("Ảnh nhỏ hơn 720px chiều ngang — chất lượng có thể kém", "warn");
    const c = $("#avPrev").getContext("2d"); c.drawImage(SAI.cropPortrait(im), 0, 0);
    $("#avStatus").innerHTML = `<span class="badge b-wait">Bản xem trước</span> <span class="tiny faint">nhập tên + tick đồng ý rồi bấm “Áp dụng ảnh” (R-LEGAL-3)</span>`; updApply(); }; im.src = r.result; }; r.readAsDataURL(file);
}
const updApply = () => $("#avApply").disabled = !(pendingImg && $("#consChk").checked && $("#consName").value.trim());
$("#avApply").onclick = () => {
  const consent = {subject_name: NFC($("#consName").value.trim()), relation: $("#consRel").value, statement: $("#consTxt").textContent, created_at: new Date().toISOString()};
  const cropped = SAI.cropPortrait(pendingImg.im); SAI.setAvatar(cropped);
  jobs.forEach(j => j._assets = null);
  const small = document.createElement("canvas"); small.width = 540; small.height = 488; small.getContext("2d").drawImage(cropped, 0, 0, 540, 488);
  const ok = store.set("avatar", {dataUrl: small.toDataURL("image/jpeg", .85), consent});
  pendingImg = null; updApply(); drawAvPrev(); setAvStatus(); dashPlayer.draw(); thumbCache.clear();
  toast(ok ? "Đã áp dụng ảnh MC + lưu bản ghi đồng ý" : "Đã áp dụng ảnh (không lưu được vào trình duyệt)");
};
$("#drop").onclick = () => $("#avFile").click();
$("#avFile").onchange = e => handleFile(e.target.files[0]);
$("#drop").ondragover = e => { e.preventDefault(); $("#drop").classList.add("over"); };
$("#drop").ondragleave = () => $("#drop").classList.remove("over");
$("#drop").ondrop = e => { e.preventDefault(); $("#drop").classList.remove("over"); handleFile(e.dataTransfer.files[0]); };
$("#consChk").onchange = updApply; $("#consName").oninput = updApply;
$("#avReset").onclick = () => { SAI.setAvatar(SAI.placeholderAvatar()); try { localStorage.removeItem("stockai.avatar"); } catch { /* */ } pendingImg = null; updApply(); drawAvPrev(); setAvStatus(); dashPlayer.draw(); thumbCache.clear(); toast("Đã chuyển về ảnh mẫu"); };

const PROVIDERS = [
  ["demo", "DemoMotion", "Ảnh thật + chuyển động nhẹ, không khớp môi", 0],
  ["hybrid", "Hybrid", "Khớp môi 7s đầu + 8s cuối, giữa DemoMotion", 0.0562 * 15],
  ["fal", "fal.ai Kling v2", "Khớp môi toàn bộ (Standard)", 0.0562 * 75],
  ["heygen", "HeyGen Photo Avatar", "Khớp môi toàn bộ · chưa kiểm chứng API v3", 0.10 * 75]];
function renderProviders() {
  $("#provGrid").innerHTML = PROVIDERS.map(([k, n, d, c]) => `<button class="opt ${settings.avatar_provider === k ? "on" : ""}" data-p="${k}"><b>${n}</b><span>${d}</span><div class="price">${c ? "≈ $" + fmt(c) + " / video" : "0 đồng"}</div></button>`).join("");
  $$("#provGrid .opt").forEach(b => b.onclick = () => { settings.avatar_provider = b.dataset.p; saveSettings(); renderProviders(); });
  const [, n, , c] = PROVIDERS.find(p => p[0] === settings.avatar_provider);
  $("#costEst").innerHTML = c ? `<b>${n}</b> ≈ <b style="color:var(--brand-2)">$${fmt(c)}/video</b> (75 giây) · ≈ $${fmt(c * 44, 0)}/tháng cho 44 video.<br><span class="tiny faint">Chỉ dùng ở PRODUCTION trên app desktop. Bản web luôn dựng bằng DemoMotion. Giá cần kiểm chứng lại.</span>`
    : `<b>0 đồng / video.</b> Ảnh thật + nhịp thở 6 giây + sóng âm. Phù hợp để chạy hằng ngày.`;
}
const VOICES = [["vi-VN-HoaiMyNeural", "HoaiMy", "Giọng nữ · miền Bắc", "#f472b6"], ["vi-VN-NamMinhNeural", "NamMinh", "Giọng nam · miền Bắc", "#38bdf8"]];
function renderVoices() {
  $("#voiceGrid").innerHTML = VOICES.map(([k, n, d, col]) => `<button class="opt ${settings.voice === k ? "on" : ""}" data-v="${k}"><span class="voice-av" style="background:${col}22;color:${col}">${n[0]}</span><b>${n}</b><span>${d}</span></button>`).join("");
  $$("#voiceGrid .opt").forEach(b => b.onclick = () => { settings.voice = b.dataset.v; saveSettings(); renderVoices(); });
}
const rate = $("#rate");
const updRate = () => { $("#rateLbl").textContent = (rate.value >= 0 ? "+" : "") + rate.value + "%"; rate.style.setProperty("--fill", ((+rate.value + 10) / 30 * 100) + "%"); };
rate.value = settings.rate; updRate();
rate.oninput = () => { settings.rate = +rate.value; saveSettings(); updRate(); };
const showNorm = () => $("#ttsNorm").textContent = "→ " + SAI.viNormalize($("#ttsText").value);
$("#ttsText").oninput = showNorm; showNorm();
$("#ttsBtn").onclick = () => { const v = SAI.speak($("#ttsText").value, voiceOpts()); $("#ttsInfo").textContent = v ? "Đang đọc bằng: " + v : "Trình duyệt không hỗ trợ đọc"; };

/* ================= KHO NỘI DUNG ================= */
const thumbCache = new Map();
function thumb(j) {
  if (thumbCache.has(j.id)) return thumbCache.get(j.id);
  const c = document.createElement("canvas"); c.width = 360; c.height = 640;
  try { SAI.drawFrame(c.getContext("2d"), j, Math.min(6, j.duration_s / 2)); } catch { SAI.drawEmpty(c.getContext("2d")); }
  const url = c.toDataURL("image/jpeg", .82); thumbCache.set(j.id, url); return url;
}
let libFilter = "";
$$("#libFilter button").forEach(b => b.onclick = () => { libFilter = b.dataset.v; $$("#libFilter button").forEach(x => x.classList.toggle("on", x === b)); renderLib(); });
$("#libSearch").oninput = () => renderLib();
function renderLib() {
  const q = $("#libSearch").value.trim().toLowerCase();
  const list = jobs.filter(j => (!libFilter || j.status === libFilter) && (!q || (j.video_title || "").toLowerCase().includes(q)));
  if (!list.length) {
    $("#jobList").innerHTML = `<div class="card empty-state" style="grid-column:1/-1">${I.video}<h3>${jobs.length ? "Không có video phù hợp bộ lọc" : "Chưa có video nào"}</h3><p class="small">${jobs.length ? "Thử bộ lọc khác." : "Vào Bảng điều khiển và bấm “Chạy quy trình” để dựng bản tin đầu tiên."}</p>${jobs.length ? "" : '<button class="btn btn-primary" id="goRun" style="margin-top:10px">Tới Bảng điều khiển</button>'}</div>`;
    $("#goRun")?.addEventListener("click", () => switchTab("dash")); return;
  }
  $("#jobList").innerHTML = list.map(j => `<div class="card jc ${j.status === "WAITING_APPROVAL" ? "wait" : ""}" data-id="${j.id}">
      <div class="th">${j.script ? `<img src="${thumb(j)}" alt="">` : `<div class="empty-state" style="padding:40px 10px">${I.x}<div class="small">${esc(j.error_code || "Lỗi")}</div></div>`}${badge(j.status)}${j.duration_s ? `<span class="dur">${mmss(j.duration_s)}</span>` : ""}<div class="ov"><span>${I.play.replace("<svg", '<svg width="18" height="18"')}</span></div></div>
      <div class="bd"><b>${esc(j.video_title || "(không có tiêu đề)")}</b><div class="m"><span>${new Date(j.created_at).toLocaleString("vi-VN", {hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit"})}</span>·<span>${SESSION_LABEL[j.session_type].toLowerCase()}</span>${j.data_quality === "SYNTHETIC" ? '<span class="badge b-syn">minh họa</span>' : ""}</div></div></div>`).join("");
  $$("#jobList .jc").forEach(el => el.onclick = () => openDrawer(el.dataset.id));
}

/* Drawer chi tiết */
let libPlayer = null;
function closeDrawer() { $("#drawer").classList.remove("on"); $("#scrim").classList.remove("on"); $("#drawer").setAttribute("aria-hidden", "true"); libPlayer?.stop(); }
$("#dwClose").onclick = closeDrawer; $("#scrim").onclick = closeDrawer;
function buildCaption(job, p) {
  const t = job.video_title, txt = job.social_post_text, tags = job.script.hashtags.join(" ");
  if (p === "telegram") { const lines = txt.split("\n").filter(Boolean); return (`<b>${t}</b>\n` + lines.slice(1, 4).join("\n") + "\nChi tiết ở tin nhắn bên dưới.\n" + AI_DECL).slice(0, 1024); }
  if (p === "youtube") return {title: t.slice(0, 100 - 8) + " #Shorts", description: (txt + "\n" + tags + " #Shorts").slice(0, 5000)};
  return (txt + "\n" + tags).slice(0, 2200);
}
async function publishJob(job, platforms, privacy, log = async (l, m) => termWrite(l, m)) {
  job.status = "PUBLISHING";
  for (const p of platforms) {
    if (job.publish_logs.some(x => x.platform === p && x.status === "SUCCESS")) { await log("INFO", `${PF[p]}: đã đăng trước đó → bỏ qua (R-PUB-2)`); continue; }
    const blocked = job.data_quality === "SYNTHETIC" || !job.ai_label_applied || settings.mode === "DEMO";
    const preview = {platform: p, title: job.video_title, caption: buildCaption(job, p), privacy: privacy[p] || PRIV[p][0],
      flags: p === "tiktok" ? {is_aigc: true} : p === "youtube" ? {containsSyntheticMedia: true, selfDeclaredMadeForKids: false} : {}};
    job.publish_logs.push({platform: p, status: blocked ? "DRY_RUN" : "SUCCESS", privacy_level: preview.privacy, preview, created_at: new Date().toISOString(),
      error_message: blocked ? (job.data_quality === "SYNTHETIC" ? "Dữ liệu minh họa → chỉ dry-run (R-PUB-1)" : "Chế độ DEMO → dry-run") : null});
    await log(blocked ? "WARN" : "SUCCESS", `${PF[p]}: ${blocked ? "DRY_RUN — đã lưu publish_preview.json" : "đăng thành công"} · quyền riêng tư ${preview.privacy}`);
  }
  job.status = "COMPLETED"; saveJobs();
}
function openDrawer(id) {
  const j = jobs.find(x => x.id === id); if (!j) return;
  selectedJob = id;
  $("#dwTitle").textContent = j.video_title || "Job lỗi";
  $("#dwBadges").innerHTML = badge(j.status) + (j.data_quality === "SYNTHETIC" ? ' <span class="badge b-syn">MINH HỌA</span>' : "");
  const body = $("#dwBody");
  if (!j.script) { body.innerHTML = `<div class="card panel" style="grid-column:1/-1"><div class="notice err">Job lỗi: ${esc(j.error_code || "")} — ${esc(j.error_message || "")}</div><pre class="box">${esc((j.events || []).map(e => `[${e.ts.slice(11, 19)}] B${e.step} ${e.level.padEnd(7)} ${e.message}`).join("\n"))}</pre><button class="btn btn-danger" id="delJob" style="margin-top:12px">Xóa job</button></div>`; }
  else body.innerHTML = `
    <div>
      <div class="device"><canvas id="libCanvas" width="540" height="960"></canvas></div>
      <div class="pctl"><button class="play" id="libPlay"></button><input type="range" id="libSeek" min="0" max="1000" aria-label="Tua video"><span class="time" id="libTime"></span></div>
      <div class="ptog"><label class="check"><input type="checkbox" id="libVoice" checked>Giọng đọc</label><label class="check"><input type="checkbox" id="libSafe">Vùng an toàn</label></div>
      <div style="display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap"><button class="btn btn-sm" id="recBtn">⏺ Ghi WebM</button><button class="btn btn-sm" id="pngBtn">Ảnh bìa PNG</button><button class="btn btn-sm btn-danger" id="delJob">Xóa</button></div>
      <div class="tiny faint" id="recInfo" style="text-align:center;margin-top:8px"></div>
      <div class="card" style="padding:14px;margin-top:16px;font-size:12.5px;color:var(--text-2)">LLM: <b>${esc(j.llm_provider)}</b> · factcheck <b class="${j.factcheck_passed ? "up" : "down"}">${j.factcheck_passed ? "ĐẠT" : "LỖI"}</b><br>Avatar: <b>${esc(j.avatar_provider)}</b> · chi phí $${fmt(j.est_cost_usd || 0)}<br>Thời lượng: <b>${fmt(j.duration_s, 1)} giây</b> · ${j.cues.length} cue phụ đề</div>
    </div>
    <div>
      <div class="tabs" id="dwTabs">${["Bài đăng", "Kịch bản", "Biểu đồ", "Tin nguồn", "Phụ đề", "Log", "Dữ liệu"].map((n, i) => `<button data-p="${i}" class="${i === 0 ? "on" : ""}">${n}</button>`).join("")}</div>
      <div class="pane on" data-p="0">
        ${j.data_quality === "SYNTHETIC" ? `<div class="notice">⚠ Video dùng DỮ LIỆU MINH HỌA → chỉ được dry-run, không đăng thật (R-DATA-2, R-PUB-1).</div>` : ""}
        <div class="field" style="margin-top:0"><label>Tiêu đề video <span class="faint" id="tLen"></span></label><input class="input" id="edTitle" maxlength="80" value="${esc(j.video_title)}"></div>
        <div class="field"><label>Bài đăng</label><textarea class="textarea" id="edPost">${esc(j.social_post_text)}</textarea></div>
        <div class="check-line" id="edCheck"></div>
        <div style="display:flex;gap:8px;margin-top:10px"><button class="btn btn-sm" id="saveEd">Lưu chỉnh sửa</button><button class="btn btn-sm" id="copyPost">Copy bài đăng</button></div>
        <h3 style="margin:24px 0 4px;font-size:15px">Duyệt &amp; Đăng</h3><div class="tiny faint">TikTok: gửi nháp vào hộp thư, bật is_aigc. YouTube: containsSyntheticMedia=true.</div>
        <div class="pub-list">${Object.keys(PF).map(p => `<div class="pub"><label class="check" style="margin:0"><input type="checkbox" class="pubChk" value="${p}" ${j.platforms.includes(p) ? "checked" : ""}></label><span class="pn">${I[p]}${PF[p]}</span><select class="select pubPriv" data-p="${p}">${PRIV[p].map(o => `<option>${o}</option>`).join("")}</select></div>`).join("")}</div>
        <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap"><button class="btn btn-ok" id="approveBtn" ${j.status === "WAITING_APPROVAL" ? "" : "disabled"}>${I.send}Duyệt &amp; Đăng</button><button class="btn" id="republishBtn" ${j.status === "COMPLETED" ? "" : "disabled"}>Đăng thêm nền tảng</button></div>
        ${j.publish_logs.length ? `<table class="t" style="margin-top:16px"><tr><th>Nền tảng</th><th>Trạng thái</th><th>Ghi chú</th><th></th></tr>${j.publish_logs.map((l, i) => `<tr><td>${PF[l.platform]}</td><td><span class="badge ${l.status === "SUCCESS" ? "b-ok" : "b-dry"}">${l.status}</span></td><td class="small muted">${esc(l.error_message || l.privacy_level || "")}</td><td><button class="btn btn-sm btn-ghost" data-prev="${i}">Preview</button></td></tr>`).join("")}</table><pre class="box" id="pubPrev" style="display:none;margin-top:10px"></pre>` : ""}
      </div>
      <div class="pane" data-p="1"><div class="small muted" style="margin-bottom:10px">${wc(j.script.video_script)} từ · sentiment <b>${j.script.market_sentiment}</b> · hook “${esc(j.ctx?.hook_style || "")}”</div><pre class="box">${esc(j.script.video_script)}</pre>
        <h3 style="font-size:15px;margin:18px 0 8px">Hai kịch bản thị trường</h3>${j.script.scenarios.map(s => `<div class="card" style="padding:12px 14px;margin-bottom:8px;font-size:13.5px"><b>${s.name}:</b> ${esc(s.description)}</div>`).join("")}
        <h3 style="font-size:15px;margin:18px 0 8px">Ticker</h3><pre class="box">${esc(j.script.ticker_text)}</pre></div>
      <div class="pane" data-p="2"><canvas id="chartCv" width="1080" height="660" style="width:100%;border-radius:12px;border:1px solid var(--line)"></canvas>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px" id="cardsCv"></div></div>
      <div class="pane" data-p="3"><table class="t"><tr><th>#</th><th>Tin</th><th>Nguồn</th><th>Điểm</th></tr>${j.news.map((n, i) => `<tr><td class="mono">${i}</td><td>${esc(n.title)}<div class="tiny muted">${esc(n.summary)}</div></td><td>${esc(n.source)}</td><td class="mono">${n.score}</td></tr>`).join("")}</table><div class="tiny faint" style="margin-top:8px">Bản web dùng tin mẫu (fixture). Bản desktop lấy RSS trực tiếp và giữ link gốc.</div></div>
      <div class="pane" data-p="4"><div style="display:flex;gap:8px"><button class="btn btn-sm" id="dlSrt">Tải subs.srt</button><button class="btn btn-sm" id="dlAss">Tải subs.ass</button></div><pre class="box" style="margin-top:10px">${esc(j.srt)}</pre></div>
      <div class="pane" data-p="5"><pre class="box">${esc(j.events.map(e => `[${e.ts.slice(11, 19)}] B${e.step ?? "-"} ${e.level.padEnd(7)} ${e.message}`).join("\n"))}</pre></div>
      <div class="pane" data-p="6"><pre class="box">${esc(JSON.stringify({id: j.id, status: j.status, data_quality: j.data_quality, market: {...j.market, bars: `[${j.market.bars.length} phiên]`}, script: j.script}, null, 2))}</pre></div>
    </div>`;
  $("#drawer").classList.add("on"); $("#scrim").classList.add("on"); $("#drawer").setAttribute("aria-hidden", "false");
  $("#delJob").onclick = () => { if (!confirm("Xóa job này?")) return; jobs = jobs.filter(x => x.id !== j.id); thumbCache.delete(j.id); saveJobs(); closeDrawer(); refreshAll(); renderLib(); toast("Đã xóa job"); };
  if (!j.script) return;
  $$("#dwTabs button").forEach(b => b.onclick = () => { $$("#dwTabs button").forEach(x => x.classList.toggle("on", x === b)); $$("#dwBody .pane").forEach(p => p.classList.toggle("on", p.dataset.p === b.dataset.p)); });
  libPlayer?.stop();
  libPlayer = SAI.makePlayer($("#libCanvas"), {
    onTime: (t, D) => { $("#libSeek").value = Math.round(t / D * 1000); $("#libSeek").style.setProperty("--fill", (t / D * 100) + "%"); $("#libTime").textContent = `${mmss(t)} / ${mmss(D)}`; },
    onState: p => $("#libPlay").innerHTML = p ? I.pause : I.play, voice: voiceOpts});
  $("#libPlay").innerHTML = I.play; libPlayer.load(j);
  $("#libPlay").onclick = () => { libPlayer.speakOn = $("#libVoice").checked; libPlayer.toggle(); };
  $("#libSeek").oninput = e => libPlayer.seek(e.target.value / 1000);
  $("#libSafe").onchange = e => { libPlayer.safe = e.target.checked; libPlayer.draw(); };
  const A = SAI.prepareAssets(j);
  $("#chartCv").getContext("2d").drawImage(A.chart, 0, 0);
  A.cards.forEach(c => { const im = document.createElement("img"); im.src = c.toDataURL("image/jpeg", .8); im.style.cssText = "width:100%;border-radius:8px;border:1px solid var(--line)"; $("#cardsCv").appendChild(im); });
  const checkEd = () => { const p = $("#edPost").value, errs = []; if (!p.includes(DISCLAIMER)) errs.push("thiếu câu miễn trừ"); if (!p.includes(AI_DECL)) errs.push("thiếu khai báo AI"); BANNED.forEach(b => p.toLowerCase().includes(b) && errs.push(`cụm cấm “${b}”`));
    $("#edCheck").innerHTML = errs.length ? `<span class="badge b-fail">✖ ${errs.join(" · ")}</span>` : `<span class="badge b-ok">✓ Đạt kiểm tra pháp lý (R-LEGAL-1, R-LEGAL-4)</span>`;
    $("#tLen").textContent = `${$("#edTitle").value.length}/80`; return errs; };
  $("#edPost").oninput = checkEd; $("#edTitle").oninput = checkEd; checkEd();
  const commit = () => { j.video_title = NFC($("#edTitle").value); j.social_post_text = NFC($("#edPost").value); saveJobs(); thumbCache.delete(j.id); };
  $("#saveEd").onclick = () => { if (checkEd().length) return toast("Bài đăng chưa đạt kiểm tra — chưa lưu", "err"); commit(); renderLib(); toast("Đã lưu chỉnh sửa"); };
  $("#copyPost").onclick = () => { navigator.clipboard?.writeText($("#edPost").value); toast("Đã copy bài đăng"); };
  const doPub = async () => { if (checkEd().length) return toast("Bài đăng chưa đạt kiểm tra", "err"); commit();
    const ps = $$(".pubChk").filter(c => c.checked).map(c => c.value); if (!ps.length) return toast("Chọn ít nhất 1 nền tảng", "warn");
    const priv = {}; $$(".pubPriv").forEach(s => priv[s.dataset.p] = s.value);
    await publishJob(j, ps, priv, async (l, m) => { j.events.push({ts: new Date().toISOString(), step: 5, level: l, message: m}); });
    toast(j.data_quality === "SYNTHETIC" ? `Đã lưu bản xem trước (dry-run) cho ${ps.length} nền tảng` : "Đã đăng"); refreshAll(); renderLib(); openDrawer(j.id); };
  $("#approveBtn").onclick = doPub; $("#republishBtn").onclick = doPub;
  $$("[data-prev]").forEach(b => b.onclick = () => { const l = j.publish_logs[+b.dataset.prev]; const pre = $("#pubPrev"); pre.style.display = "block"; pre.textContent = "publish_preview.json\n" + JSON.stringify(l.preview, null, 2); });
  const dl = (name, text) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], {type: "text/plain"})); a.download = name; a.click(); };
  $("#dlSrt").onclick = () => dl("subs.srt", j.srt); $("#dlAss").onclick = () => dl("subs.ass", j.ass);
  $("#pngBtn").onclick = () => { const c = document.createElement("canvas"); c.width = 1080; c.height = 1920; SAI.drawFrame(c.getContext("2d"), j, 1); c.toBlob(b => { const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "thumbnail.png"; a.click(); }); };
  $("#recBtn").onclick = () => recordVideo(j);
}
function recordVideo(j) {
  if (!HTMLCanvasElement.prototype.captureStream || !window.MediaRecorder) return toast("Trình duyệt không hỗ trợ ghi video", "err");
  const c = document.createElement("canvas"); c.width = 720; c.height = 1280; const g = c.getContext("2d");
  const rec = new MediaRecorder(c.captureStream(30), {mimeType: MediaRecorder.isTypeSupported("video/webm;codecs=vp9") ? "video/webm;codecs=vp9" : "video/webm", videoBitsPerSecond: 3_000_000});
  const chunks = []; rec.ondataavailable = e => chunks.push(e.data);
  rec.onstop = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(chunks, {type: "video/webm"})); a.download = `stockai_${j.run_date}.webm`; a.click(); $("#recInfo").textContent = "Đã tải file WebM (không có tiếng — bản desktop dùng FFmpeg ghép voice.mp3)."; $("#recBtn").disabled = false; };
  const t0 = performance.now(); rec.start(); $("#recBtn").disabled = true;
  const step = () => { const t = (performance.now() - t0) / 1000; if (t >= j.duration_s) { rec.stop(); return; } SAI.drawFrame(g, j, t); $("#recInfo").textContent = `Đang ghi ${Math.floor(t)}/${Math.floor(j.duration_s)} giây… (giữ tab mở)`; requestAnimationFrame(step); };
  step();
}

/* ================= LỊCH ================= */
let sDays = "mon-fri";
$$("#sDays button").forEach(b => b.onclick = () => { sDays = b.dataset.v; $$("#sDays button").forEach(x => x.classList.toggle("on", x === b)); });
$("#sPf").innerHTML = Object.keys(PF).map(p => `<label><input type="checkbox" class="sPf" value="${p}" ${p === "telegram" ? "checked" : ""}>${I[p].replace("<svg", '<svg width="16" height="16"')}${PF[p]}</label>`).join("");
function renderWeek() {
  const now = new Date(), mon = new Date(now); mon.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  $("#week").innerHTML = Array.from({length: 7}, (_, i) => { const d = new Date(mon); d.setDate(mon.getDate() + i); const wd = d.getDay();
    const evs = schedules.filter(s => s.is_active && (s.days === "all" || (wd !== 0 && wd !== 6))).sort((a, b) => a.time.localeCompare(b.time));
    return `<div class="day ${d.toDateString() === now.toDateString() ? "today" : ""}"><div class="dn"><span>${DOW[wd]}</span><span>${pad(d.getDate())}/${pad(d.getMonth() + 1)}</span></div>${evs.map(s => `<div class="ev ${s.session_type === "POST_MARKET" ? "post" : ""}">${s.time} · ${esc(s.name.length > 14 ? s.name.slice(0, 14) + "…" : s.name)}</div>`).join("")}</div>`; }).join("");
}
function renderSched() {
  renderWeek();
  $("#schCount").textContent = `${schedules.filter(s => s.is_active).length}/${schedules.length} đang bật`;
  $("#schList").innerHTML = schedules.map(s => `<div class="card sch ${s.is_active ? "" : "off"}"><span class="tm">${s.time}</span>
      <div class="info"><b>${esc(s.name)}</b><div class="m"><span class="badge ${s.session_type === "POST_MARKET" ? "b-ai" : "b-cache"}">${SESSION_LABEL[s.session_type].toLowerCase()}</span><span>${s.days === "mon-fri" ? "T2–T6" : "Cả tuần"}</span>·${s.platforms.map(p => I[p].replace("<svg", '<svg width="14" height="14" style="display:inline;vertical-align:-2px"')).join(" ")}·<span>${s.require_approval ? "chờ duyệt" : "tự đăng"}</span>${s.last_run_at ? `·<span>lần cuối ${new Date(s.last_run_at).toLocaleString("vi-VN", {hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit"})} ${badge(s.last_status)}</span>` : ""}</div></div>
      <label class="switch" title="Bật/tắt"><input type="checkbox" data-tog="${s.id}" ${s.is_active ? "checked" : ""}><span></span></label>
      <button class="btn btn-sm" data-run="${s.id}">Chạy thử</button><button class="icon-btn" data-del="${s.id}" title="Xóa">${I.x.replace("<svg", '<svg width="14" height="14"')}</button></div>`).join("")
    || `<div class="empty-state">Chưa có lịch nào.</div>`;
  $$("[data-tog]").forEach(c => c.onchange = () => { schedules.find(s => s.id == c.dataset.tog).is_active = c.checked; saveSched(); renderSched(); tick(); });
  $$("[data-del]").forEach(b => b.onclick = () => { schedules = schedules.filter(s => s.id != b.dataset.del); saveSched(); renderSched(); tick(); toast("Đã xóa lịch"); });
  $$("[data-run]").forEach(b => b.onclick = () => { const s = schedules.find(s => s.id == b.dataset.run); switchTab("dash"); runPipeline(s.session_type, "MANUAL", s); });
}
function addSchedule(name, type, time, days) {
  const ps = $$(".sPf").filter(c => c.checked).map(c => c.value);
  schedules.push({id: Date.now(), name: NFC(name), session_type: type, time, days, platforms: ps.length ? ps : ["telegram"], require_approval: $("#sAppr").checked || ps.includes("tiktok"), is_active: true, last_run_at: null, last_status: null});
  saveSched(); renderSched(); tick();
}
$("#sAdd").onclick = () => { addSchedule($("#sName").value || "Lịch mới", $("#sType").value, $("#sTime").value, sDays); toast("Đã lưu lịch — đồng bộ ngay, không cần khởi động lại"); };
$("#sQuick").onclick = () => { const d = new Date(Date.now() + 60000), t = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  addSchedule("Lịch thử nghiệm", "PRE_MARKET", t, "all"); toast(`Đã tạo lịch lúc ${t}. Giữ tab mở — quy trình sẽ tự chạy.`, "info"); };

/* ================= CÀI ĐẶT ================= */
const KEYS = [["AI", "gemini_api_key", "Gemini API key"], ["AI", "openai_api_key", "OpenAI-compatible API key"], ["Dữ liệu", "ssi_consumer_id", "SSI FastConnect Consumer ID"], ["Dữ liệu", "ssi_consumer_secret", "SSI FastConnect Consumer Secret"],
  ["Avatar & giọng", "fal_key", "fal.ai key"], ["Avatar & giọng", "heygen_api_key", "HeyGen API key"], ["Avatar & giọng", "elevenlabs_api_key", "ElevenLabs API key"],
  ["Mạng xã hội", "telegram_bot_token", "Telegram Bot Token"], ["Mạng xã hội", "facebook_page_token", "Facebook Page Token"], ["Mạng xã hội", "tiktok_access_token", "TikTok access token"]];
const mask = v => v.length <= 8 ? "••••" : v.slice(0, 4) + "••••••" + v.slice(-4);
function renderKeys() {
  let grp = "";
  $("#keys").innerHTML = KEYS.map(([g, k, lb]) => { const h = g !== grp ? `<div class="grp-t">${g}</div>` : ""; grp = g;
    return `${h}<div class="field" style="margin-top:10px"><label>${lb} ${secrets[k] ? `<span class="badge b-ok">${mask(secrets[k])}</span>` : ""}</label><div class="key-row"><input class="input" type="password" data-key="${k}" placeholder="${secrets[k] ? "Nhập để thay khóa mới" : "Dán khóa vào đây"}" autocomplete="off"><button class="btn btn-sm" data-test="${k}">Kiểm tra</button></div></div>`; }).join("");
  $$("[data-key]").forEach(i => i.onchange = () => { if (i.value.trim()) { secrets[i.dataset.key] = i.value.trim(); toast("Đã lưu khóa trong bộ nhớ tab (bản desktop: keyring hệ điều hành)"); } i.value = ""; renderKeys(); renderProd(); });
  $$("[data-test]").forEach(b => b.onclick = () => toast(secrets[b.dataset.test] ? "Định dạng hợp lệ. Bản web không gọi API thật — kiểm tra thật cần app desktop." : "Chưa nhập khóa", secrets[b.dataset.test] ? "info" : "warn"));
}
function renderProd() {
  const miss = [];
  if (!secrets.ssi_consumer_id || !secrets.ssi_consumer_secret) miss.push("Nguồn dữ liệu hợp lệ (SSI FastConnect) — quyết định D1");
  if (!secrets.gemini_api_key && !secrets.openai_api_key) miss.push("Khóa LLM (Gemini hoặc OpenAI-compatible)");
  if (!store.get("avatar", null)) miss.push("Ảnh chân dung thật + bản ghi đồng ý (R-LEGAL-3)");
  if (!secrets.telegram_bot_token) miss.push("Ít nhất một kênh đăng (Telegram Bot Token)");
  miss.push("Ứng dụng desktop (FastAPI + FFmpeg) — bản web không thể đăng thật");
  $("#prodCheck").innerHTML = settings.mode === "PRODUCTION"
    ? `<div class="notice" style="display:block;margin:0"><b>Điều kiện còn thiếu cho PRODUCTION</b><ul style="margin:8px 0 0;padding-left:18px">${miss.map(x => `<li>${x}</li>`).join("")}</ul></div>`
    : `<div class="notice info" style="margin:0">DEMO: dữ liệu minh họa, kịch bản mẫu, avatar chuyển động nhẹ, đăng bài dạng dry-run. Chi phí 0 đồng.</div>`;
}
function renderPreflight() {
  const items = [
    ["Canvas 2D (dựng khung hình)", true, ""],
    ["Giọng đọc tiếng Việt của trình duyệt", ("speechSynthesis" in window) && SAI.viVoices().length > 0, "Mở bằng Microsoft Edge để có giọng HoaiMy/NamMinh"],
    ["MediaRecorder (ghi WebM)", !!window.MediaRecorder, "Trình duyệt không hỗ trợ ghi video"],
    ["Lưu trữ cục bộ (localStorage)", store.set("probe", 1), "Trình duyệt chặn lưu trữ — dữ liệu sẽ mất khi đóng tab"],
    ["Ảnh chân dung + bản ghi đồng ý", !!store.get("avatar", null), "Đang dùng ảnh mẫu — tải ảnh ở Nhân vật & giọng"],
    ["FFmpeg (ass, zoompan, showwaves, xfade, loudnorm, libx264)", null, "Chỉ cần cho bản desktop: winget install Gyan.FFmpeg"]];
  $("#pfList").innerHTML = items.map(([n, ok, h]) => `<div class="pf-item"><span class="ic" style="background:${ok === true ? "rgba(16,185,129,.15);color:#34d399" : ok === false ? "rgba(245,158,11,.15);color:#fbbf24" : "rgba(56,189,248,.12);color:#7dd3fc"}">${ok === true ? "✓" : ok === false ? "!" : "i"}</span><div>${n}${ok !== true && h ? `<div class="tiny muted">${h}</div>` : ""}</div></div>`).join("");
}
function renderSettings() { $("#modeSw").checked = settings.mode === "PRODUCTION"; renderKeys(); renderProd(); renderPreflight(); }
$("#modeSw").onchange = e => { settings.mode = e.target.checked ? "PRODUCTION" : "DEMO"; saveSettings(); renderProd(); refreshAll(); };
$("#exportBtn").onclick = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify({jobs: jobs.map(({_assets, ...r}) => r), schedules, settings}, null, 2)], {type: "application/json"})); a.download = "stockai_demo_export.json"; a.click(); };
$("#wipeBtn").onclick = () => { if (!confirm("Xóa toàn bộ job, lịch, ảnh và cài đặt demo?")) return; Object.keys(localStorage).filter(k => k.startsWith("stockai.")).forEach(k => localStorage.removeItem(k)); location.reload(); };

/* ================= COMMAND PALETTE ================= */
const CMDS = [
  ["Chạy quy trình ngay", I.play, () => { switchTab("dash"); runPipeline(session); }, "Bảng điều khiển"],
  ["Mở Bảng điều khiển", I.rss, () => switchTab("dash"), "1"], ["Mở Nhân vật & giọng", I.mic, () => switchTab("char"), "2"],
  ["Mở Kho nội dung", I.film, () => switchTab("lib"), "3"], ["Mở Lịch tự động", I.send, () => switchTab("sched"), "4"], ["Mở Cài đặt", I.ai, () => switchTab("set"), "5"],
  ["Mở video mới nhất", I.video, () => { if (jobs[0]) { switchTab("lib"); openDrawer(jobs[0].id); } else toast("Chưa có video", "warn"); }, "Kho"],
  ["Tạo lịch thử sau 1 phút", I.send, () => { switchTab("sched"); $("#sQuick").click(); }, "Lịch"],
  ["Nghe thử giọng đọc", I.mic, () => { switchTab("char"); $("#ttsBtn").click(); }, "Giọng"],
  ["Xuất dữ liệu demo (JSON)", I.check, () => $("#exportBtn").click(), "Cài đặt"],
  ["Về trang giới thiệu", I.x, () => location.href = "index.html", "Trang chủ"]];
let cmdSel = 0, cmdItems = CMDS;
function renderCmd() {
  const q = $("#cmdIn").value.trim().toLowerCase(); cmdItems = CMDS.filter(c => !q || c[0].toLowerCase().includes(q)); cmdSel = Math.min(cmdSel, Math.max(0, cmdItems.length - 1));
  $("#cmdList").innerHTML = cmdItems.map((c, i) => `<button class="cmdk-item ${i === cmdSel ? "sel" : ""}" data-i="${i}">${c[1]}${c[0]}<span class="hint">${c[3]}</span></button>`).join("") || '<div class="empty-state small">Không có lệnh phù hợp</div>';
  $$("#cmdList .cmdk-item").forEach(b => { b.onclick = () => runCmd(+b.dataset.i); b.onmouseenter = () => { cmdSel = +b.dataset.i; $$("#cmdList .cmdk-item").forEach(x => x.classList.toggle("sel", x === b)); }; });
}
const openCmd = () => { $("#cmdk").classList.add("on"); $("#cmdIn").value = ""; cmdSel = 0; renderCmd(); setTimeout(() => $("#cmdIn").focus(), 30); };
const closeCmd = () => $("#cmdk").classList.remove("on");
const runCmd = i => { const c = cmdItems[i]; closeCmd(); c?.[2](); };
$("#openCmd").onclick = openCmd; $("#cmdk").onclick = e => { if (e.target.id === "cmdk") closeCmd(); };
$("#cmdIn").oninput = () => { cmdSel = 0; renderCmd(); };
$("#cmdIn").onkeydown = e => { if (e.key === "ArrowDown") { cmdSel = (cmdSel + 1) % cmdItems.length; renderCmd(); e.preventDefault(); } else if (e.key === "ArrowUp") { cmdSel = (cmdSel - 1 + cmdItems.length) % cmdItems.length; renderCmd(); e.preventDefault(); } else if (e.key === "Enter") runCmd(cmdSel); };
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); $("#cmdk").classList.contains("on") ? closeCmd() : openCmd(); return; }
  if (e.key === "Escape") { closeCmd(); closeDrawer(); return; }
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName) || e.ctrlKey || e.metaKey || e.altKey) return;
  const t = {1: "dash", 2: "char", 3: "lib", 4: "sched", 5: "set"}[e.key]; if (t) switchTab(t);
});

/* ================= KHỞI ĐỘNG ================= */
(async () => {
  try { await document.fonts.load('800 40px "Be Vietnam Pro"'); await document.fonts.load('400 20px "Be Vietnam Pro"'); } catch { /* */ }
  const storedAv = store.get("avatar", null);
  if (storedAv) await new Promise(res => { const im = new Image(); im.onload = () => { SAI.setAvatar(SAI.cropPortrait(im)); res(); }; im.onerror = res; im.src = storedAv.dataUrl; });
  resetSteps(); renderProviders(); renderVoices(); setAvStatus(); refreshAll(); tick(); setInterval(tick, 1000);
  const last = jobs.find(j => j.script); loadDash(last || null);
  voiceNotice(); if ("speechSynthesis" in window) speechSynthesis.onvoiceschanged = () => { voiceNotice(); };
  const h = location.hash.slice(1); if (TITLES[h]) switchTab(h);
  if (!jobs.length && !store.get("welcomed", false)) { store.set("welcomed", true); setTimeout(() => toast("Chào mừng! Bấm “Chạy quy trình” để dựng bản tin đầu tiên (Ctrl K để mở bảng lệnh).", "info"), 700); }
})();
})();
