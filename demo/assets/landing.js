/* =========================== Landing interactions =========================== */
(() => {
"use strict";
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const {fmt, fmtSigned, esc} = SAI;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
$("#yr").textContent = new Date().getFullYear();

/* ---------- Nav ---------- */
const nav = $("#nav");
const onScroll = () => nav.classList.toggle("scrolled", scrollY > 20);
addEventListener("scroll", onScroll, {passive: true}); onScroll();
$("#burger").onclick = () => { const o = $("#navLinks").classList.toggle("open"); $("#burger").setAttribute("aria-expanded", o); };
$$("#navLinks a").forEach(a => a.addEventListener("click", () => $("#navLinks").classList.remove("open")));

/* ---------- Spotlight theo con trỏ ---------- */
document.addEventListener("pointermove", e => {
  const el = e.target.closest?.(".spot"); if (!el) return;
  const r = el.getBoundingClientRect();
  el.style.setProperty("--mx", `${e.clientX - r.left}px`); el.style.setProperty("--my", `${e.clientY - r.top}px`);
}, {passive: true});

/* ---------- Nút "nam châm" ---------- */
if (!reduce) $$("[data-magnet]").forEach(b => {
  b.addEventListener("pointermove", e => { const r = b.getBoundingClientRect(); b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * .18}px,${(e.clientY - r.top - r.height / 2) * .25}px)`; });
  b.addEventListener("pointerleave", () => b.style.transform = "");
});

/* ---------- Reveal + đếm số ---------- */
const countUp = el => {
  const to = +el.dataset.count, suf = el.dataset.suffix || "", t0 = performance.now(), dur = 1400;
  const step = now => { const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 4); el.textContent = Math.round(to * e) + suf; if (p < 1) requestAnimationFrame(step); };
  reduce ? el.textContent = to + suf : requestAnimationFrame(step);
};
const io = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; e.target.classList.add("in"); e.target.querySelectorAll?.("[data-count]").forEach(countUp); if (e.target.dataset.count) countUp(e.target); io.unobserve(e.target); }), {threshold: .15, rootMargin: "0px 0px -40px 0px"});
$$(".reveal").forEach(el => io.observe(el));
setTimeout(() => $$(".hero-meta [data-count]").forEach(countUp), 800);

/* ---------- Toast ---------- */
function toast(msg, kind = "ok") {
  const t = document.createElement("div"); t.className = "toast " + kind;
  t.innerHTML = `<span class="ti">${{ok: "✓", warn: "!", err: "×", info: "i"}[kind]}</span><div>${esc(msg)}</div>`;
  $("#toasts").appendChild(t); setTimeout(() => { t.classList.add("out"); setTimeout(() => t.remove(), 300); }, 3800);
}

/* ---------- Hero: video 9:16 dựng thật bằng engine ---------- */
let heroJob = null;
const phone = $("#phone"), stage = $("#stage");
(async () => {
  try { await document.fonts.load('800 40px "Be Vietnam Pro"'); await document.fonts.load('400 20px "Be Vietnam Pro"'); } catch { /* bỏ qua */ }
  heroJob = await SAI.buildJob({session_type: "PRE_MARKET"});
  const P = SAI.makePlayer($("#heroCanvas"));
  P.loop = true; P.load(heroJob, 0.2);
  const vis = new IntersectionObserver(([e]) => e.isIntersecting ? P.play() : P.stop(), {threshold: .2});
  if (!reduce) vis.observe(stage); else P.seek(.2);
  const m = heroJob.market, errs = SAI.factcheck(heroJob.script, heroJob.ctx);
  const total = (heroJob.script.video_script + heroJob.script.social_post_text + heroJob.script.ticker_text).match(SAI.NUM_RE)?.length || 0;
  $("#chipFact").textContent = `${total - errs.length}/${total} hợp lệ`;
  $("#chipRsi").textContent = `${fmt(m.rsi14, 1)} · ${m.rsi14 > 70 ? "quá mua" : m.rsi14 < 30 ? "quá bán" : "trung tính"}`;
  buildMarquee(m); buildViz(heroJob); drawBentoChart(m); initPlayground(heroJob);
})();
$("#szBtn").onclick = () => { phone.classList.toggle("show-sz"); $("#szBtn").classList.toggle("btn-primary"); };
if (!reduce) {
  stage.addEventListener("pointermove", e => { const r = stage.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
    phone.style.transform = `rotateY(${x * 14}deg) rotateX(${-y * 10}deg)`; });
  stage.addEventListener("pointerleave", () => phone.style.transform = "rotateY(-8deg) rotateX(4deg)");
  phone.style.transform = "rotateY(-8deg) rotateX(4deg)";
}

/* ---------- Marquee chỉ số (minh họa) ---------- */
function buildMarquee(m) {
  const rnd = SAI.mulberry32(7);
  const rows = [["VN-INDEX", m.close, m.change_pct], ["VN30", 1790 + rnd() * 40, (rnd() - .45) * 2], ["HNX-INDEX", 238 + rnd() * 6, (rnd() - .5) * 2], ["UPCOM", 102 + rnd() * 3, (rnd() - .5) * 1.4],
    ["SMA20", m.sma20, null], ["RSI14", m.rsi14, null], ["HỖ TRỢ", m.support20, null], ["KHÁNG CỰ", m.resistance20, null], ["THANH KHOẢN", 21450 + rnd() * 2000, (rnd() - .4) * 9]];
  const html = rows.map(([k, v, c]) => `<span class="it"><b>${k}</b><span class="v">${fmt(v)}</span>${c === null ? "" : `<span class="${c >= 0 ? "up" : "down"} mono small">${c >= 0 ? "▲" : "▼"} ${fmtSigned(c)}%</span>`}</span>`).join("")
    + `<span class="it"><span class="badge b-syn">MINH HỌA · không phải số liệu thật</span></span>`;
  $("#marquee").innerHTML = html + html;
}

/* ---------- Minh họa trong các bước pipeline ---------- */
function buildViz(job) {
  $("#vizNews").innerHTML = job.news.slice(0, 4).map(n => `<div class="row"><span class="src">${esc(n.source)}</span><span>${esc(n.title)}</span><span class="score">${n.score.toFixed(3)}</span></div>`).join("")
    + `<div class="row"><span class="src">VnEconomy</span><span class="strike">Giá vàng miếng lập đỉnh mới trong tuần</span><span class="score" style="color:var(--down)">ngoài chủ đề</span></div>`;
  const m = job.market;
  $("#vizScript").innerHTML = `“…VN-Index đóng cửa tại <span class="ok">${fmt(m.close)}</span> điểm, ${m.change >= 0 ? "tăng" : "giảm"} <span class="ok">${fmt(Math.abs(m.change))}</span> điểm. RSI 14 phiên ở mức <span class="ok">${fmt(m.rsi14)}</span>… Mục tiêu <span class="bad">1.999,99</span> điểm…”<br><span class="down">✖ Số không có trong dữ liệu: 1.999,99 → viết lại</span>`;
  $("#wave").innerHTML = Array.from({length: 48}, (_, i) => `<i style="--i:${i};--h:${30 + Math.abs(Math.sin(i * 1.7)) * 70}%"></i>`).join("");
}
function drawBentoChart(m) { $("#bentoChart").getContext("2d").drawImage(SAI.renderChart(m), 0, 0); }

/* ---------- Thanh tiến trình pipeline theo cuộn ---------- */
const steps = $$(".step"), links = $$("#pipeProg a"), rail = $("#rail"), wrap = $("#steps");
function onPipeScroll() {
  const r = wrap.getBoundingClientRect(), mid = innerHeight * .55;
  rail.style.setProperty("--p", Math.max(0, Math.min(100, (mid - r.top) / r.height * 100)) + "%");
  let active = 0; steps.forEach((s, i) => { const b = s.getBoundingClientRect(); if (b.top < mid) active = i; s.classList.toggle("on", b.top < mid); });
  links.forEach((a, i) => a.classList.toggle("on", i <= active));
}
addEventListener("scroll", onPipeScroll, {passive: true}); onPipeScroll();

/* ---------- Lịch kế tiếp (vòng tròn đếm ngược) ---------- */
function nextSlot() {
  const now = new Date();
  for (let d = 0; d < 8; d++) for (const [h, mi] of [[7, 30], [15, 30]]) {
    const c = new Date(now); c.setDate(c.getDate() + d); c.setHours(h, mi, 0, 0);
    if (c > now && c.getDay() % 6 !== 0) return c;
  }
}
function tickRing() {
  const n = nextSlot(), s = Math.floor((n - new Date()) / 1000), pct = Math.max(2, 100 - Math.min(100, s / 864));
  $("#ring").style.setProperty("--p", pct.toFixed(1));
  $("#ringTxt").textContent = `${Math.floor(s / 3600)}h`;
  $("#nextLbl").textContent = `${SAI.pad(n.getHours())}:${SAI.pad(n.getMinutes())} ${["CN", "T2", "T3", "T4", "T5", "T6", "T7"][n.getDay()]}`;
  $("#nextIn").textContent = `còn ${SAI.pad(Math.floor(s / 3600))}:${SAI.pad(Math.floor(s / 60) % 60)}:${SAI.pad(s % 60)}`;
}
tickRing(); setInterval(tickRing, 1000);

/* ---------- Playground factcheck ---------- */
function initPlayground(job) {
  const m = job.market, input = $("#pgIn");
  const base = `Kết thúc phiên, VN-Index đóng cửa tại ${fmt(m.close)} điểm, ${m.change >= 0 ? "tăng" : "giảm"} ${fmt(Math.abs(m.change))} điểm, tương ứng ${fmt(Math.abs(m.change_pct))}%. Chỉ số đang nằm ${m.close >= m.sma20 ? "trên" : "dưới"} đường trung bình 20 phiên ở mức ${fmt(m.sma20)} điểm. RSI 14 phiên ở mức ${fmt(m.rsi14)}. Vùng hỗ trợ quanh ${fmt(m.support20)} điểm, kháng cự quanh ${fmt(m.resistance20)} điểm.`;
  input.value = base;
  $("#pgFacts").innerHTML = [["Đóng cửa", m.close], ["Thay đổi", m.change], ["%", m.change_pct], ["SMA20", m.sma20], ["RSI14", m.rsi14], ["Hỗ trợ", m.support20], ["Kháng cự", m.resistance20]]
    .map(([k, v]) => `<span class="badge b-dry">${k} <b class="mono">${fmt(v)}</b></span>`).join("");
  const run = () => {
    const text = input.value, ann = SAI.annotateNumbers(text, job.ctx);
    let html = "", last = 0;
    for (const a of ann) { html += esc(text.slice(last, a.index)) + `<span class="${a.ok ? "ok" : "bad"}" title="${a.ok ? "Có trong dữ liệu đầu vào" : "Không có trong dữ liệu"}">${esc(a.raw)}</span>`; last = a.index + a.raw.length; }
    html += esc(text.slice(last));
    $("#pgOut").innerHTML = html || '<span class="muted">Nhập kịch bản…</span>';
    const bad = ann.filter(a => !a.ok), banned = SAI.BANNED.filter(b => text.toLowerCase().includes(b));
    const v = $("#pgVerdict");
    if (!bad.length && !banned.length) { v.className = "verdict pass"; v.innerHTML = `✓ Đạt — ${ann.length} con số đều có trong dữ liệu đầu vào`; }
    else { v.className = "verdict fail"; v.innerHTML = `✖ Bị chặn — ${[bad.length ? `${bad.length} số không có trong dữ liệu (${bad.map(b => esc(b.raw)).join(", ")})` : "", banned.length ? `cụm từ cấm: “${banned.join("”, “")}”` : ""].filter(Boolean).join(" · ")} → yêu cầu AI viết lại`; }
  };
  input.addEventListener("input", run); run();
  $("#pgFake").onclick = () => { input.value += ` Mục tiêu tiếp theo là 1.999,99 điểm, nhà đầu tư nên mua ngay.`; run(); toast("Đã chèn số bịa + cụm từ cấm — xem factcheck chặn lại", "warn"); };
  $("#pgReset").onclick = () => { input.value = base; run(); };
}

/* ---------- Bộ ước tính chi phí ---------- */
const OPTS = [["DemoMotion", 0], ["Hybrid", 0.0562 * 15], ["Kling Std", 0.0562 * 75], ["Kling Pro", 0.115 * 75], ["OmniHuman", 0.14 * 75]];
let opt = 1;
$("#cSeg").innerHTML = OPTS.map(([n], i) => `<button class="chip ${i === opt ? "on" : ""}" data-i="${i}">${n}</button>`).join("");
$$("#cSeg .chip").forEach(b => b.onclick = () => { opt = +b.dataset.i; $$("#cSeg .chip").forEach(x => x.classList.toggle("on", x === b)); calc(); });
const range = $("#cRange");
function calc() {
  const v = +range.value, per = OPTS[opt][1], month = per * v * 22;
  range.style.setProperty("--fill", ((v - 1) / 5 * 100) + "%");
  $("#cVid").textContent = v;
  $("#cOut").textContent = month ? `$${fmt(month, 0)}` : "0 đ";
  $("#cPer").textContent = `${v * 22} video/tháng · ${per ? "$" + fmt(per) + "/video" : "miễn phí"}`;
}
range.oninput = calc; calc();
})();
