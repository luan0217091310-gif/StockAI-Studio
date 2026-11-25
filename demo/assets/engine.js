/* =====================================================================
   StockAI Studio — engine dùng chung cho web demo (BLUEPRINT v3.0)
   Logic nghiệp vụ là bản port từ Python (indicators, ranking, factcheck,
   template, cues, layout 9:16). Mọi dịch vụ ngoài đều mô phỏng.
   Không phụ thuộc DOM ngoài canvas → dùng được cho landing + studio.
   ===================================================================== */
(function (global) {
"use strict";

const NFC = s => String(s ?? "").normalize("NFC");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const nfCache = {};
const nf = d => (nfCache[d] ||= new Intl.NumberFormat("vi-VN", {minimumFractionDigits: d, maximumFractionDigits: d}));
const fmt = (x, d = 2) => nf(d).format(x);
const fmtSigned = (x, d = 2) => (x >= 0 ? "+" : "-") + fmt(Math.abs(x), d);
const pad = n => String(n).padStart(2, "0");
const dmy = d => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
const ymd = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : "j" + Math.random().toString(16).slice(2) + Date.now().toString(16));
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const SESSION_LABEL = {PRE_MARKET: "TRƯỚC PHIÊN", POST_MARKET: "TỔNG KẾT PHIÊN", ADHOC: "ĐIỂM TIN"};
const FONT = `"Be Vietnam Pro","Segoe UI",system-ui,sans-serif`;

/* ---------- Layout 9:16 (Mục 10 — khớp stockai/layout.py) ---------- */
const L = {
  W: 1080, H: 1920,
  header: {x: 60, y: 120, w: 960, h: 100},
  ticker: {y: 220, h: 60, speed: 140},
  broll: {y: 280, h: 660},
  aiLabel: {x: 76, y: 296, h: 44},
  divider: {y: 940, h: 4},
  avatar: {y: 944, h: 976},
  subs: {left: 140, right: 940, bottom: 1400, size: 60, maxW: 800},
  wave: {x: 120, y: 1410, w: 840, h: 60},
  disclaimer: {x: 60, y: 860, w: 900, h: 70},
  unsafe: {bottomY: 1440, rightX: 960, rightFromY: 840, topY: 120}
};

/* ---------- SyntheticProvider: random walk có seed theo ngày ---------- */
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function tradingDaysBack(n, end) {
  const out = []; const d = new Date(end); d.setHours(0, 0, 0, 0);
  if (d.getDay() === 0) d.setDate(d.getDate() - 2); else if (d.getDay() === 6) d.setDate(d.getDate() - 1);
  while (out.length < n) { if (d.getDay() !== 0 && d.getDay() !== 6) out.unshift(new Date(d)); d.setDate(d.getDate() - 1); }
  return out;
}
function syntheticBars(seedDate, n = 60, seedExtra = 0) {
  const rnd = mulberry32(Number(ymd(seedDate).replaceAll("-", "")) + seedExtra);
  let c = 1640 + rnd() * 60; const bars = [];
  for (const d of tradingDaysBack(n, seedDate)) {
    const o = c * (1 + (rnd() - 0.5) * 0.006);
    c = o * (1 + (rnd() - 0.48) * 0.018);
    const h = Math.max(o, c) * (1 + rnd() * 0.006), l = Math.min(o, c) * (1 - rnd() * 0.006);
    bars.push({date: ymd(d), open: +o.toFixed(2), high: +h.toFixed(2), low: +l.toFixed(2), close: +c.toFixed(2), volume: Math.round(550e6 + rnd() * 450e6)});
  }
  return bars;
}

/* ---------- Chỉ báo (Mục 9.2) ---------- */
function sma(arr, n) { return arr.map((_, i) => i < n - 1 ? null : arr.slice(i - n + 1, i + 1).reduce((a, b) => a + b, 0) / n); }
function rsiWilder(close, n = 14) {
  const a = 1 / n; let g = 0, l = 0;
  for (let i = 1; i < close.length; i++) {
    const d = close[i] - close[i - 1], gi = Math.max(d, 0), li = Math.max(-d, 0);
    if (i === 1) { g = gi; l = li; } else { g = a * gi + (1 - a) * g; l = a * li + (1 - a) * l; }
  }
  return l === 0 ? 100 : 100 - 100 / (1 + g / l);
}
function buildSnapshot(bars, source, quality) {
  const close = bars.map(b => b.close), last = bars.at(-1), prev = bars.at(-2), t20 = bars.slice(-20);
  const change = last.close - prev.close;
  return {symbol: "VNINDEX", session_date: last.date, bars, close: last.close, change: +change.toFixed(2),
    change_pct: +(change / prev.close * 100).toFixed(2), volume: last.volume, value_bn_vnd: null, foreign_net_bn_vnd: null,
    sma20: +sma(close, 20).at(-1).toFixed(2), rsi14: +rsiWilder(close).toFixed(2),
    support20: +Math.min(...t20.map(b => b.low)).toFixed(2), resistance20: +Math.max(...t20.map(b => b.high)).toFixed(2),
    source, data_quality: quality};
}

/* ---------- Tin tức: fixture RSS mẫu (đúng cấu trúc 3 nguồn) ---------- */
const NEWS_FIXTURE = [
  {t: "Khối ngoại bán ròng phiên thứ ba liên tiếp trên HOSE", s: "CafeF", h: 3, sum: "Dòng vốn ngoại tiếp tục rút ròng, tập trung ở nhóm ngân hàng và bất động sản."},
  {t: "NHNN giữ ổn định lãi suất điều hành, tỷ giá hạ nhiệt", s: "VnEconomy", h: 5, sum: "Ngân hàng Nhà nước duy trì mặt bằng lãi suất, tỷ giá trung tâm giảm nhẹ trong tuần."},
  {t: "Thanh khoản HOSE cải thiện, dòng tiền quay lại nhóm chứng khoán", s: "Vietstock", h: 7, sum: "Giá trị giao dịch tăng so với phiên trước, nhóm cổ phiếu chứng khoán thu hút dòng tiền."},
  {t: "Khối ngoại bán ròng phiên thứ 3 liên tiếp trên sàn HOSE", s: "Vietstock", h: 4, sum: "Tin trùng ý với CafeF — dùng để kiểm tra chống trùng gần đúng."},
  {t: "Fed phát tín hiệu thận trọng về lộ trình giảm lãi suất", s: "VnEconomy", h: 9, sum: "Biên bản cuộc họp cho thấy các thành viên muốn thêm dữ liệu lạm phát trước khi quyết định."},
  {t: "Nhóm cổ phiếu thép hồi phục sau chuỗi điều chỉnh", s: "CafeF", h: 11, sum: "Nhiều mã thép tăng giá trở lại khi giá nguyên liệu đầu vào ổn định."},
  {t: "Giá vàng miếng lập đỉnh mới trong tuần", s: "VnEconomy", h: 6, sum: "Tin ngoài chủ đề chứng khoán — sẽ bị bộ lọc từ khóa loại bỏ."},
  {t: "Trái phiếu doanh nghiệp: áp lực đáo hạn giảm dần", s: "CafeF", h: 20, sum: "Khối lượng trái phiếu đáo hạn trong quý tới thấp hơn cùng kỳ."},
  {t: "UPCoM: thêm doanh nghiệp đăng ký giao dịch trong tháng", s: "Vietstock", h: 26, sum: "Số doanh nghiệp mới lên sàn UPCoM tăng nhẹ."},
  {t: "VN-Index giằng co quanh vùng kháng cự ngắn hạn", s: "CafeF", h: 2, sum: "Chỉ số dao động hẹp, lực cung xuất hiện khi tiếp cận vùng đỉnh cũ."}
];
const TOPIC_KW = {"vn-index": 3, "cổ phiếu": 2, "chứng khoán": 2, "hose": 2, "hnx": 2, "upcom": 1.5, "khối ngoại": 3, "thanh khoản": 2.5, "lãi suất": 2, "tỷ giá": 1.5, "nhnn": 1.5, "fed": 1.5, "trái phiếu": 1};
const normTitle = s => NFC(s).toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").replace(/\s+/g, " ").trim();
function hashStr(s) { let h = 0x811c9dc5; for (const ch of s) { h ^= ch.codePointAt(0); h = Math.imul(h, 0x01000193) >>> 0; } return h.toString(16).padStart(8, "0"); }
async function sha256(s) {
  if (global.crypto?.subtle) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join(""); }
  return hashStr(s).repeat(8); // file:// trên một số trình duyệt không có subtle crypto
}
function jaccard(a, b) { const A = new Set(normTitle(a).split(" ")), B = new Set(normTitle(b).split(" ")); let i = 0; A.forEach(w => B.has(w) && i++); return i / (A.size + B.size - i); }
async function collectNews(now, log = async () => {}) {
  const prevTd = new Date(now); prevTd.setHours(0, 0, 0, 0);
  do { prevTd.setDate(prevTd.getDate() - 1); } while (prevTd.getDay() === 0 || prevTd.getDay() === 6);
  let since = new Date(Math.min(now - 48 * 3600e3, prevTd));
  if (now - since > 96 * 3600e3) since = new Date(now - 96 * 3600e3);
  await log("INFO", `Cửa sổ tin: từ ${since.toLocaleString("vi-VN")} (${Math.round((now - since) / 3600e3)} giờ)`);
  const items = [], seen = new Set();
  for (const f of NEWS_FIXTURE) {
    const title = NFC(f.t), low = title.toLowerCase() + " " + f.sum.toLowerCase();
    const kw = Object.entries(TOPIC_KW).filter(([k]) => low.includes(k));
    if (!kw.length) { await log("DEBUG", `Loại tin ngoài chủ đề: “${title}”`); continue; }
    const hash = await sha256(normTitle(title));
    if (seen.has(hash)) continue; seen.add(hash);
    const dup = items.find(x => jaccard(x.title, title) >= 0.6);
    if (dup) { dup.sources++; await log("DEBUG", `Chống trùng (Jaccard ≥ 0,6): gộp “${title}” vào tin của ${dup.source}`); continue; }
    items.push({title, source: f.s, url: `https://example.invalid/${f.s.toLowerCase()}/${hash.slice(0, 10)}`, published_at: new Date(now - f.h * 3600e3).toISOString(),
      summary: NFC(f.sum).slice(0, 300), content_hash: hash, kwWeight: kw.reduce((a, [, w]) => a + w, 0), hoursAgo: f.h, sources: 1});
  }
  const maxKw = Math.max(...items.map(x => x.kwWeight));
  items.forEach(x => x.score = +(0.5 * Math.max(0, 1 - x.hoursAgo / 96) + 0.3 * x.kwWeight / maxKw + 0.2 * Math.min(x.sources, 3) / 3).toFixed(3));
  items.sort((a, b) => b.score - a.score);
  return items.slice(0, 20).map((x, i) => ({...x, id: i}));
}

/* ---------- AI biên tập: TemplateFallbackProvider + hậu kiểm ---------- */
const DISCLAIMER = "Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.";
const AI_DECL = "Video có sử dụng AI (MC ảo, giọng đọc tổng hợp).";
const BANNED = ["chắc chắn", "mua ngay", "bắt đáy ngay", "x2 tài khoản", "cơ hội cuối cùng"];
const HOOKS = ["câu hỏi gợi tò mò", "con số nổi bật nhất", "so sánh với phiên trước", "tin nóng nhất", "cảnh báo nhẹ nhàng"];
const wc = s => String(s).trim().split(/\s+/).filter(Boolean).length;
const lc1 = s => s.charAt(0).toLowerCase() + s.slice(1);
function templateScript(ctx) {
  const m = ctx.market, up = m.change >= 0, dir = up ? "tăng" : "giảm";
  const sd = new Date(m.session_date + "T00:00:00");
  const hookIdx = HOOKS.indexOf(ctx.hook_style) >= 0 ? HOOKS.indexOf(ctx.hook_style) : 0;
  const n = ctx.news.slice(0, 3);
  const hookLines = [
    `Sau phiên ${dir} ${fmt(Math.abs(m.change))} điểm, liệu VN-Index sẽ đi tiếp theo hướng nào?`,
    `${fmt(m.close)} điểm, đó là mức đóng cửa mới nhất của VN-Index.`,
    `So với phiên trước, VN-Index đã ${dir} ${fmt(Math.abs(m.change_pct))}%.`,
    `Tin đáng chú ý nhất hôm nay: ${lc1(n[0].title)}.`,
    `Thị trường đang ở vùng nhạy cảm, hãy cùng điểm lại các tín hiệu cần lưu ý.`
  ];
  const rsiState = m.rsi14 > 70 ? "quá mua" : m.rsi14 < 30 ? "quá bán" : "trung tính";
  const parts = [
    hookLines[hookIdx],
    `Xin chào quý vị, đây là bản tin chứng khoán ${SESSION_LABEL[ctx.session_type].toLowerCase()} ngày ${dmy(new Date(ctx.run_date))}.`,
    `Kết thúc phiên ngày ${pad(sd.getDate())}/${pad(sd.getMonth() + 1)}, VN-Index đóng cửa tại ${fmt(m.close)} điểm, ${dir} ${fmt(Math.abs(m.change))} điểm, tương ứng ${fmt(Math.abs(m.change_pct))}%.`,
    `Về kỹ thuật, chỉ số đang nằm ${m.close >= m.sma20 ? "trên" : "dưới"} đường trung bình 20 phiên ở mức ${fmt(m.sma20)} điểm.`,
    `Chỉ báo RSI 14 phiên ở mức ${fmt(m.rsi14)}, cho thấy trạng thái ${rsiState}.`,
    `Vùng hỗ trợ gần nhất quanh ${fmt(m.support20)} điểm, còn kháng cự nằm quanh ${fmt(m.resistance20)} điểm.`,
    `Tiếp theo là các tin đáng chú ý.`,
    `Thứ nhất, ${lc1(n[0].title)}.`, `Thứ hai, ${lc1(n[1].title)}.`, `Thứ ba, ${lc1(n[2].title)}.`,
    `Kịch bản cơ sở, chỉ số dao động trong vùng ${fmt(m.support20)} đến ${fmt(m.resistance20)} điểm.`,
    `Kịch bản thận trọng, nếu mất hỗ trợ ${fmt(m.support20)} điểm, áp lực điều chỉnh có thể tăng, cần chú ý quản trị rủi ro.`
  ];
  // Câu có thể bỏ khi tiêu đề tin quá dài (giữ ≤ 220 từ)
  const optional = [`Tiếp theo là các tin đáng chú ý.`, parts[1]];
  while (wc([...parts, "Cảm ơn quý vị đã theo dõi, hẹn gặp lại trong bản tin tiếp theo.", DISCLAIMER].join(" ")) > 212 && optional.length) parts.splice(parts.indexOf(optional.shift()), 1);
  const fillers = [n[0].summary, n[1].summary, n[2].summary, "Diễn biến dòng tiền trong những phiên tới sẽ là yếu tố quan trọng cần theo dõi.", "Quý vị nên theo dõi thêm thông tin từ các nguồn chính thức trước khi ra quyết định."];
  const closing = ["Cảm ơn quý vị đã theo dõi, hẹn gặp lại trong bản tin tiếp theo.", DISCLAIMER];
  // Giống template_fallback.py: thêm câu đệm trước 2 kịch bản cho tới khi ≥ 170 từ, không bao giờ vượt 215 từ
  const extra = [], assemble = ex => [...parts.slice(0, -2), ...ex, ...parts.slice(-2), ...closing].join(" ");
  for (const f of fillers) {
    if (wc(assemble(extra)) >= 170) break;
    if (wc(assemble([...extra, f])) > 215) continue;
    extra.push(f);
  }
  const video_script = NFC(assemble(extra));
  const sentiment = m.change_pct > 0.3 ? "BULLISH" : m.change_pct < -0.3 ? "BEARISH" : "NEUTRAL";
  const ticker = `VN-INDEX ${fmt(m.close)} (${fmtSigned(m.change_pct)}%) | SMA20 ${fmt(m.sma20)} | RSI14 ${fmt(m.rsi14, 1)}`.slice(0, 120);
  const scenarios = [
    {name: "CƠ SỞ", description: `Dao động trong vùng ${fmt(m.support20)} – ${fmt(m.resistance20)} điểm, thị trường chờ thêm thông tin mới.`},
    {name: "THẬN TRỌNG", description: `Nếu đánh mất hỗ trợ ${fmt(m.support20)} điểm, áp lực điều chỉnh có thể gia tăng.`}
  ];
  const social = NFC([
    `📊 BẢN TIN CHỨNG KHOÁN ${SESSION_LABEL[ctx.session_type]} ${dmy(new Date(ctx.run_date))}`, "",
    `• VN-Index: ${fmt(m.close)} điểm (${fmtSigned(m.change)} | ${fmtSigned(m.change_pct)}%)`,
    `• SMA20: ${fmt(m.sma20)} · RSI14: ${fmt(m.rsi14)}`,
    `• Hỗ trợ ${fmt(m.support20)} · Kháng cự ${fmt(m.resistance20)}`, "",
    "📰 Tin đáng chú ý:", ...n.map(x => `• ${x.title} (${x.source})`), "",
    `🔹 Kịch bản cơ sở: ${scenarios[0].description}`, `🔸 Kịch bản thận trọng: ${scenarios[1].description}`, "",
    `Nguồn tin: ${[...new Set(n.map(x => x.source))].join(", ")}.`, DISCLAIMER, AI_DECL
  ].join("\n"));
  const impacts = ["TIÊU CỰC", "TRUNG LẬP", "TÍCH CỰC"];
  return {
    video_title: `Bản tin ${SESSION_LABEL[ctx.session_type].toLowerCase()} ${dmy(new Date(ctx.run_date))}: VN-Index ${dir} ${fmt(Math.abs(m.change_pct))}%`.slice(0, 80),
    market_sentiment: sentiment,
    selected_news: n.map((x, i) => ({headline: x.title.split(" ").slice(0, 12).join(" "), impact: /bán ròng|thận trọng/i.test(x.title) ? "TIÊU CỰC" : /cải thiện|hồi phục|tăng/i.test(x.title) ? "TÍCH CỰC" : impacts[1], brief: x.summary, source_index: i})),
    scenarios, social_post_text: social, video_script, ticker_text: ticker,
    hashtags: ["#chungkhoan", "#VNIndex", "#bantinchungkhoan", "#taichinh"]
  };
}
/* Factcheck số liệu bằng code (Mục 9.4.5) */
const NUM_RE = /[+-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|[+-]?\d+(?:,\d+)?/g;
const parseVN = s => parseFloat(String(s).replace(/\./g, "").replace(",", "."));
function allowedNumbers(ctx) {
  const m = ctx.market, sd = new Date(m.session_date + "T00:00:00"), rd = new Date(ctx.run_date + "T00:00:00");
  const allowed = [m.close, m.change, m.change_pct, m.sma20, m.rsi14, m.support20, m.resistance20, m.volume, m.volume / 1e6,
    sd.getDate(), sd.getMonth() + 1, sd.getFullYear(), rd.getDate(), rd.getMonth() + 1, rd.getFullYear(), 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 20, 60];
  const newsText = ctx.news.map(x => x.title + " " + x.summary).join(" ");
  (newsText.match(NUM_RE) || []).forEach(x => allowed.push(parseVN(x)));
  return allowed;
}
const numberOk = (v, allowed) => { v = Math.abs(v); return allowed.some(a => { a = Math.abs(a); return Math.abs(a - v) <= 0.01 || (a && Math.abs(a - v) / a <= 0.005) || Math.abs(+a.toFixed(1) - v) <= 0.01 || Math.abs(Math.round(a) - v) <= 0.01; }); };
function factcheck(script, ctx) {
  const allowed = allowedNumbers(ctx), errs = [];
  const text = [script.video_script, script.social_post_text, script.ticker_text].join("\n");
  for (const raw of (text.match(NUM_RE) || [])) if (!numberOk(parseVN(raw), allowed)) errs.push(`Số không có trong dữ liệu: ${raw}`);
  const inputs = (ctx.news.map(x => x.title + " " + x.summary).join(" ") + " VNINDEX").toUpperCase();
  for (const t of (script.video_script.match(/\b[A-Z]{3}\b/g) || [])) if (!["SMA", "RSI", "HNX", "USD", "VND"].includes(t) && !inputs.includes(t)) errs.push(`Mã không có trong dữ liệu: ${t}`);
  return errs;
}
/** Đánh dấu từng con số trong văn bản: [{raw, ok, index}] — dùng cho playground. */
function annotateNumbers(text, ctx) {
  const allowed = allowedNumbers(ctx), out = [];
  for (const m of String(text).matchAll(NUM_RE)) out.push({raw: m[0], index: m.index, ok: numberOk(parseVN(m[0]), allowed)});
  return out;
}
function postcheck(script, ctx) {
  const errs = [], w = wc(script.video_script);
  if (w < 160 || w > 220) errs.push(`video_script có ${w} từ (yêu cầu 160–220)`);
  if (!script.video_script.trim().endsWith(DISCLAIMER)) errs.push("Thiếu câu miễn trừ ở cuối kịch bản (R-LEGAL-4)");
  if (!script.social_post_text.includes(DISCLAIMER) || !script.social_post_text.includes(AI_DECL)) errs.push("Bài đăng thiếu miễn trừ hoặc khai báo AI (R-LEGAL-1)");
  script.selected_news.forEach(h => wc(h.headline) > 12 && errs.push(`Headline quá 12 từ: ${h.headline}`));
  if (script.selected_news.length < 3 || script.selected_news.length > 4) errs.push("selected_news phải có 3–4 tin");
  if (script.scenarios.length !== 2) errs.push("Phải có đúng 2 kịch bản");
  if (script.ticker_text.length > 120) errs.push("ticker_text quá 120 ký tự");
  const all = (script.video_script + " " + script.social_post_text).toLowerCase();
  BANNED.forEach(b => all.includes(b) && errs.push(`Cụm từ cấm: “${b}”`));
  return errs.concat(factcheck(script, ctx));
}

/* ---------- Giọng đọc & phụ đề ---------- */
function viNormalize(s) {
  return NFC(s).replace(/([+])(\d[\d.,]*)\s*điểm/g, "tăng $2 điểm").replace(/-(\d[\d.,]*)\s*điểm/g, "giảm $1 điểm")
    .replace(/%/g, " phần trăm").replace(/VN-?INDEX/gi, "VN-Index").replace(/\|/g, ".")
    .replace(/[*#_~]/g, "").replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "").replace(/\s+/g, " ").trim();
}
function wordTimings(text, ratePct = 5) {
  const words = text.split(/\s+/).filter(Boolean), out = []; let t = 300;
  const k = 1 / (1 + ratePct / 100);
  for (const w of words) {
    const dur = (170 + w.length * 38) * k; out.push({text: w, start_ms: Math.round(t), end_ms: Math.round(t + dur)});
    t += dur + (/[.,;:?!]$/.test(w) ? (/[.?!]$/.test(w) ? 380 : 180) * k : 40 * k);
  }
  return out;
}
let measureCtx = null;
const mctx = () => measureCtx || (measureCtx = document.createElement("canvas").getContext("2d"));
function buildCues(words) {
  const g = mctx(); g.font = `700 ${L.subs.size}px ${FONT}`;
  const fits = s => g.measureText(s).width <= L.subs.maxW;
  const cues = []; let lines = [""], start = null, last = null;
  const flush = () => { if (start === null) return; cues.push({start, end: last.end_ms, lines: lines.filter(Boolean)}); lines = [""]; start = null; };
  for (const w of words) {
    if (start === null) start = w.start_ms;
    const cur = lines.at(-1), cand = cur ? cur + " " + w.text : w.text;
    if (fits(cand)) lines[lines.length - 1] = cand;
    else if (lines.length < 2) lines.push(w.text);
    else { flush(); start = w.start_ms; lines = [w.text]; }
    last = w;
    const dur = last.end_ms - start;
    if ((/[.?!]$/.test(w.text) && dur >= 800) || dur >= 3500) flush();
  }
  flush();
  for (let i = 0; i < cues.length - 1; i++) if (cues[i + 1].start - cues[i].end < 150) cues[i].end = cues[i + 1].start;
  return cues;
}
function toSRT(cues) {
  const ts = ms => { const h = Math.floor(ms / 3.6e6), m = Math.floor(ms / 6e4) % 60, s = Math.floor(ms / 1000) % 60, r = ms % 1000; return `${pad(h)}:${pad(m)}:${pad(s)},${String(r).padStart(3, "0")}`; };
  return cues.map((c, i) => `${i + 1}\n${ts(c.start)} --> ${ts(c.end)}\n${c.lines.join("\n")}\n`).join("\n");
}
function toASS(cues) {
  const ts = ms => { const cs = Math.round(ms / 10); return `${Math.floor(cs / 360000)}:${pad(Math.floor(cs / 6000) % 60)}:${pad(Math.floor(cs / 100) % 60)}.${pad(cs % 100)}`; };
  return `[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Main,Be Vietnam Pro,60,&H0015CCFA,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,140,140,520,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n` +
    cues.map(c => `Dialogue: 0,${ts(c.start)},${ts(c.end)},Main,,0,0,0,,${c.lines.join("\\N")}`).join("\n");
}
function viVoices() { return ("speechSynthesis" in global) ? speechSynthesis.getVoices().filter(v => v.lang && v.lang.toLowerCase().startsWith("vi")) : []; }
function speak(text, {voice = "vi-VN-HoaiMyNeural", rate = 5, onend} = {}) {
  if (!("speechSynthesis" in global)) return null;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(viNormalize(text));
  const vs = viVoices(), want = /NamMinh/i.test(voice) ? /nam ?minh/i : /hoai ?my/i;
  u.voice = vs.find(v => want.test(v.name)) || vs[0] || null; u.lang = "vi-VN"; u.rate = 1 + rate / 100;
  if (onend) u.onend = onend;
  speechSynthesis.speak(u);
  return u.voice ? u.voice.name : "giọng mặc định của trình duyệt";
}

/* ---------- Avatar mẫu (vẽ bằng canvas) + crop 1080×976 ---------- */
let avatarImg = null;
function placeholderAvatar() {
  const c = document.createElement("canvas"); c.width = 1080; c.height = 976; const g = c.getContext("2d");
  const bg = g.createLinearGradient(0, 0, 0, 976); bg.addColorStop(0, "#0f1d33"); bg.addColorStop(1, "#060a14"); g.fillStyle = bg; g.fillRect(0, 0, 1080, 976);
  // phông studio: đèn bokeh + màn hình biểu đồ mờ
  const bokeh = [[160, 180, 120, "rgba(16,185,129,.18)"], [930, 140, 150, "rgba(99,102,241,.20)"], [820, 420, 90, "rgba(56,189,248,.14)"], [250, 520, 110, "rgba(139,92,246,.14)"]];
  for (const [x, y, r, col] of bokeh) { const rg = g.createRadialGradient(x, y, 0, x, y, r); rg.addColorStop(0, col); rg.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = rg; g.fillRect(x - r, y - r, r * 2, r * 2); }
  g.strokeStyle = "rgba(16,185,129,.22)"; g.lineWidth = 4; g.beginPath();
  for (let i = 0; i <= 40; i++) { const x = 40 + i * 25, y = 300 - Math.sin(i * 0.45) * 40 - i * 3; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke();
  // vai + áo vest
  const suit = g.createLinearGradient(0, 640, 0, 976); suit.addColorStop(0, "#1e293b"); suit.addColorStop(1, "#0b1222");
  g.fillStyle = suit; g.beginPath(); g.moveTo(150, 976); g.bezierCurveTo(170, 760, 330, 690, 540, 680); g.bezierCurveTo(750, 690, 910, 760, 930, 976); g.fill();
  g.fillStyle = "#f1f5f9"; g.beginPath(); g.moveTo(470, 690); g.lineTo(540, 800); g.lineTo(610, 690); g.closePath(); g.fill();
  g.fillStyle = "#10b981"; g.beginPath(); g.moveTo(525, 705); g.lineTo(555, 705); g.lineTo(568, 860); g.lineTo(540, 890); g.lineTo(512, 860); g.closePath(); g.fill();
  g.fillStyle = "#0f172a"; g.beginPath(); g.moveTo(470, 690); g.lineTo(420, 976); g.lineTo(380, 976); g.lineTo(440, 700); g.fill(); g.beginPath(); g.moveTo(610, 690); g.lineTo(660, 976); g.lineTo(700, 976); g.lineTo(640, 700); g.fill();
  // cổ + đầu
  const skin = g.createLinearGradient(380, 200, 700, 640); skin.addColorStop(0, "#f2c9a5"); skin.addColorStop(1, "#d49d76");
  g.fillStyle = skin; g.fillRect(498, 540, 84, 160);
  g.beginPath(); g.ellipse(540, 400, 140, 178, 0, 0, Math.PI * 2); g.fill();
  g.fillStyle = "rgba(0,0,0,.10)"; g.beginPath(); g.ellipse(540, 600, 70, 20, 0, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#111827"; g.beginPath(); g.ellipse(540, 285, 152, 96, 0, Math.PI * 0.98, Math.PI * 2.02); g.fill();
  g.beginPath(); g.ellipse(410, 340, 26, 70, 0.1, 0, Math.PI * 2); g.ellipse(670, 340, 26, 70, -0.1, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#1f2937"; g.beginPath(); g.ellipse(487, 395, 15, 10, 0, 0, Math.PI * 2); g.ellipse(593, 395, 15, 10, 0, 0, Math.PI * 2); g.fill();
  g.strokeStyle = "#5b3a29"; g.lineWidth = 7; g.lineCap = "round"; g.beginPath(); g.moveTo(462, 362); g.quadraticCurveTo(487, 350, 512, 360); g.moveTo(568, 360); g.quadraticCurveTo(593, 350, 618, 362); g.stroke();
  g.strokeStyle = "#a0522d"; g.lineWidth = 7; g.beginPath(); g.arc(540, 470, 40, 0.18 * Math.PI, 0.82 * Math.PI); g.stroke();
  g.fillStyle = "rgba(255,255,255,.5)"; g.font = `600 26px ${FONT}`; g.textAlign = "center"; g.fillText("ẢNH MẪU · tải ảnh của bạn ở Studio", 540, 940); g.textAlign = "left";
  return c;
}
function cropPortrait(img) {
  const c = document.createElement("canvas"); c.width = 1080; c.height = 976; const g = c.getContext("2d");
  const r = 1080 / 976, ir = img.width / img.height; let sw, sh, sx, sy;
  if (ir > r) { sh = img.height; sw = sh * r; sx = (img.width - sw) / 2; sy = 0; } else { sw = img.width; sh = sw / r; sx = 0; sy = Math.max(0, (img.height - sh) * 0.25); }
  g.drawImage(img, sx, sy, sw, sh, 0, 0, 1080, 976); return c;
}
const currentAvatar = () => avatarImg || (avatarImg = placeholderAvatar());
const setAvatar = c => { avatarImg = c; };

/* ---------- Thành phần đồ họa (Giai đoạn A) ---------- */
function roundRect(g, x, y, w, h, r) { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); }
function wrapText(g, text, maxW) { const words = text.split(" "), lines = []; let cur = ""; for (const w of words) { const t = cur ? cur + " " + w : w; if (g.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t; } if (cur) lines.push(cur); return lines; }
function watermark(g, w, h) {
  g.save(); g.translate(w / 2, h / 2); g.rotate(-0.32); g.fillStyle = "rgba(245,158,11,.20)"; g.font = `800 52px ${FONT}`; g.textAlign = "center";
  g.fillText("DỮ LIỆU MINH HỌA", 0, -20); g.font = `700 32px ${FONT}`; g.fillText("KHÔNG PHẢI SỐ LIỆU THẬT", 0, 30); g.restore();
}
function renderChart(m) {
  const c = document.createElement("canvas"); c.width = 1080; c.height = 660; const g = c.getContext("2d");
  const bgr = g.createLinearGradient(0, 0, 0, 660); bgr.addColorStop(0, "#0d1526"); bgr.addColorStop(1, "#0a0f1c"); g.fillStyle = bgr; g.fillRect(0, 0, 1080, 660);
  const bars = m.bars, x0 = 40, x1 = 1000, yTop = 130, yBot = 520, vTop = 545, vBot = 640;
  const lo = Math.min(...bars.map(b => b.low), m.support20) * 0.998, hi = Math.max(...bars.map(b => b.high), m.resistance20) * 1.002;
  const Y = v => yBot - (v - lo) / (hi - lo) * (yBot - yTop), step = (x1 - x0) / bars.length;
  g.strokeStyle = "rgba(148,163,184,.10)"; g.lineWidth = 1;
  for (let i = 0; i <= 5; i++) { const y = yTop + i * (yBot - yTop) / 5; g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke(); }
  // vùng gradient dưới đường giá đóng cửa
  const area = g.createLinearGradient(0, yTop, 0, yBot); area.addColorStop(0, "rgba(16,185,129,.18)"); area.addColorStop(1, "rgba(16,185,129,0)");
  g.fillStyle = area; g.beginPath(); bars.forEach((b, i) => { const x = x0 + i * step + step / 2; i ? g.lineTo(x, Y(b.close)) : g.moveTo(x, Y(b.close)); }); g.lineTo(x1 - step / 2, yBot); g.lineTo(x0 + step / 2, yBot); g.fill();
  const maxV = Math.max(...bars.map(b => b.volume));
  bars.forEach((b, i) => { const x = x0 + i * step + step / 2, upc = b.close >= b.open; g.strokeStyle = g.fillStyle = upc ? "#10B981" : "#F43F5E"; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(x, Y(b.high)); g.lineTo(x, Y(b.low)); g.stroke();
    const yo = Y(b.open), yc = Y(b.close); g.fillRect(x - step * 0.32, Math.min(yo, yc), step * 0.64, Math.max(2, Math.abs(yc - yo)));
    g.globalAlpha = 0.35; const vh = b.volume / maxV * (vBot - vTop); g.fillRect(x - step * 0.32, vBot - vh, step * 0.64, vh); g.globalAlpha = 1; });
  const s = sma(bars.map(b => b.close), 20); g.strokeStyle = "#F59E0B"; g.lineWidth = 3; g.beginPath(); let st = false;
  s.forEach((v, i) => { if (v === null) return; const x = x0 + i * step + step / 2; st ? g.lineTo(x, Y(v)) : g.moveTo(x, Y(v)); st = true; }); g.stroke();
  g.setLineDash([10, 8]); g.lineWidth = 2;
  [[m.support20, "#10B981", "Hỗ trợ"], [m.resistance20, "#F43F5E", "Kháng cự"]].forEach(([v, col, lb]) => { g.strokeStyle = col; g.beginPath(); g.moveTo(x0, Y(v)); g.lineTo(x1, Y(v)); g.stroke();
    g.fillStyle = col; g.font = `600 20px ${FONT}`; g.textAlign = "right"; g.fillText(`${lb} ${fmt(v)}`, 1015, Y(v) - 8); });
  g.setLineDash([]); g.textAlign = "left";
  const up = m.change >= 0; g.font = `800 38px ${FONT}`; g.fillStyle = up ? "#10B981" : "#F43F5E";
  g.fillText(`VN-INDEX | ${fmt(m.close)} (${fmtSigned(m.change)} | ${fmtSigned(m.change_pct)}%)`, 40, 100);
  const sd = new Date(m.session_date + "T00:00:00");
  g.fillStyle = "#94A3B8"; g.font = `400 21px ${FONT}`; g.fillText(`Phiên ${dmy(sd)} · Nguồn: ${m.source} · SMA20 ${fmt(m.sma20)} · RSI14 ${fmt(m.rsi14)}`, 40, 128 - 2);
  if (m.data_quality === "SYNTHETIC") watermark(g, 1080, 660);
  return c;
}
const IMPACT_COL = {"TÍCH CỰC": "#10B981", "TIÊU CỰC": "#F43F5E", "TRUNG LẬP": "#F59E0B"};
function renderCard(h, src, m, idx) {
  const c = document.createElement("canvas"); c.width = 1080; c.height = 660; const g = c.getContext("2d");
  const gr = g.createLinearGradient(0, 0, 1080, 660); gr.addColorStop(0, "#0F172A"); gr.addColorStop(1, "#111827"); g.fillStyle = gr; g.fillRect(0, 0, 1080, 660);
  const col = IMPACT_COL[h.impact];
  const glow = g.createRadialGradient(1000, 80, 0, 1000, 80, 520); glow.addColorStop(0, col + "33"); glow.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = glow; g.fillRect(0, 0, 1080, 660);
  g.fillStyle = col; roundRect(g, 60, 110, 8, 430, 4); g.fill();
  g.font = `700 26px ${FONT}`; const tw = g.measureText(h.impact).width + 40;
  g.globalAlpha = .18; roundRect(g, 96, 100, tw, 46, 23); g.fill(); g.globalAlpha = 1; g.fillText(h.impact, 116, 133);
  g.fillStyle = "#9CA3AF"; g.font = `600 24px ${FONT}`; g.fillText(`TIN NÓNG #${idx + 1}`, 120 + tw, 133);
  let size = 62, lines; do { g.font = `800 ${size}px ${FONT}`; lines = wrapText(g, h.headline, 880); size -= 4; } while (lines.length > 3 && size > 40);
  size += 4; g.fillStyle = "#F9FAFB"; lines.slice(0, 3).forEach((l, i) => g.fillText(l, 96, 230 + i * (size + 16)));
  g.font = `400 32px ${FONT}`; g.fillStyle = "#CBD5E1"; wrapText(g, h.brief, 880).slice(0, 2).forEach((l, i) => g.fillText(l, 96, 230 + Math.min(3, lines.length) * (size + 16) + 30 + i * 44));
  g.font = `600 24px ${FONT}`; g.fillStyle = "#64748B"; g.fillText(`Nguồn: ${src}`, 96, 600);
  if (m.data_quality === "SYNTHETIC") watermark(g, 1080, 660);
  return c;
}
function renderTickerStrip(text) {
  const mg = mctx(); mg.font = `500 34px ${FONT}`; const seg = text + "  •  "; const S = Math.ceil(mg.measureText(seg).width);
  const n = Math.ceil(1080 / S) + 1; const c = document.createElement("canvas"); c.width = S * n; c.height = 60; const g = c.getContext("2d");
  g.fillStyle = "#111827"; g.fillRect(0, 0, c.width, 60); g.fillStyle = "#E5E7EB"; g.font = `500 34px ${FONT}`; g.textBaseline = "middle";
  for (let i = 0; i < n; i++) g.fillText(seg, i * S, 31); return {canvas: c, S};
}
function prepareAssets(job) {
  if (job._assets) return job._assets;
  const m = job.market, sc = job.script;
  const chart = renderChart(m);
  const cards = sc.selected_news.map((h, i) => renderCard(h, job.news[h.source_index]?.source || "", m, i));
  const seq = [chart, ...cards, chart], D = job.duration_s, xf = 0.4;
  job._assets = {chart, cards, seq, segLen: (D + xf * (seq.length - 1)) / seq.length, xf, ticker: renderTickerStrip(sc.ticker_text)};
  return job._assets;
}

/* ---------- Khung hình (Giai đoạn B — cùng filtergraph, vẽ bằng canvas) ---------- */
function drawFrame(g, job, t, opt = {}) {
  const A = prepareAssets(job), D = job.duration_s;
  g.save(); g.scale(g.canvas.width / 1080, g.canvas.height / 1920);
  g.fillStyle = "#0B1120"; g.fillRect(0, 0, 1080, 1920);
  // Header Z1
  const lg = g.createLinearGradient(60, 138, 124, 202); lg.addColorStop(0, "#34d399"); lg.addColorStop(1, "#059669");
  g.fillStyle = lg; roundRect(g, 60, 138, 64, 64, 16); g.fill();
  g.fillStyle = "#04130d"; [[0.35, 0], [0.6, 1], [0.85, 2]].forEach(([h, i]) => g.fillRect(72 + i * 15, 192 - (44 * h), 9, 44 * h));
  g.fillStyle = "#F9FAFB"; g.font = `800 36px ${FONT}`; g.fillText("BẢN TIN CHỨNG KHOÁN", 140, 168);
  g.fillStyle = "#34d399"; g.font = `600 26px ${FONT}`; g.fillText(SESSION_LABEL[job.session_type], 140, 204);
  g.fillStyle = "#9CA3AF"; g.textAlign = "right"; g.font = `600 28px ${FONT}`; g.fillText(dmy(new Date(job.run_date + "T00:00:00")), 1020, 182); g.textAlign = "left";
  // Ticker Z2
  const tk = A.ticker; g.drawImage(tk.canvas, -((t * L.ticker.speed) % tk.S), L.ticker.y);
  // B-roll Z3 với xfade
  const pos = i => i * (A.segLen - A.xf);
  let idx = 0; for (let i = 0; i < A.seq.length; i++) if (t >= pos(i)) idx = i;
  const drawSeg = (i, alpha) => { const lt = t - pos(i); const zoom = (i === 0 || i === A.seq.length - 1) ? 1 + 0.04 * Math.min(1, lt / A.segLen) : 1;
    g.globalAlpha = alpha; g.save(); g.beginPath(); g.rect(0, L.broll.y, 1080, L.broll.h); g.clip();
    g.drawImage(A.seq[i], 540 - 540 * zoom, L.broll.y + 330 - 330 * zoom, 1080 * zoom, 660 * zoom); g.restore(); g.globalAlpha = 1; };
  drawSeg(idx, 1);
  if (idx + 1 < A.seq.length && t > pos(idx + 1) - A.xf) drawSeg(idx + 1, Math.min(1, (t - (pos(idx + 1) - A.xf)) / A.xf));
  // Nhãn AI cố định (R-LEGAL-1)
  g.font = `700 24px ${FONT}`; const lbl = "Nội dung có sử dụng AI", lw = g.measureText(lbl).width;
  g.fillStyle = "rgba(15,23,42,.85)"; roundRect(g, L.aiLabel.x, L.aiLabel.y, lw + 86, 44, 22); g.fill();
  g.fillStyle = "#8B5CF6"; roundRect(g, L.aiLabel.x + 6, L.aiLabel.y + 6, 50, 32, 16); g.fill();
  g.fillStyle = "#fff"; g.fillText("AI", L.aiLabel.x + 16, L.aiLabel.y + 31); g.fillStyle = "#E5E7EB"; g.fillText(lbl, L.aiLabel.x + 68, L.aiLabel.y + 31);
  // Z4 đường phân cách phát sáng
  g.shadowColor = "#10B981"; g.shadowBlur = 24; g.fillStyle = "#10B981"; g.fillRect(0, L.divider.y, 1080, 4); g.shadowBlur = 0;
  // Z5 avatar — "nhịp thở" chu kỳ 6s
  const av = opt.avatar || currentAvatar(), z = 1.03 + 0.03 * Math.sin(2 * Math.PI * t / 6);
  g.save(); g.beginPath(); g.rect(0, L.avatar.y, 1080, L.avatar.h); g.clip();
  g.drawImage(av, 540 - 540 * z, L.avatar.y + 488 - 488 * z, 1080 * z, 976 * z); g.restore();
  // Phụ đề
  const cue = job.cues.find(c => t * 1000 >= c.start && t * 1000 < c.end);
  if (cue) { g.font = `700 ${L.subs.size}px ${FONT}`; g.textAlign = "center"; g.lineJoin = "round";
    cue.lines.forEach((ln, i) => { const y = L.subs.bottom - (cue.lines.length - 1 - i) * 72 - 14;
      g.lineWidth = 10; g.strokeStyle = "#000"; g.strokeText(ln, 540, y); g.fillStyle = "#FACC15"; g.fillText(ln, 540, y); });
    g.textAlign = "left"; }
  // Sóng âm
  const speaking = job.words.some(w => t * 1000 >= w.start_ms && t * 1000 <= w.end_ms);
  g.strokeStyle = "rgba(16,185,129,.8)"; g.lineWidth = 3; g.beginPath();
  for (let x = 0; x <= L.wave.w; x += 6) { const a = speaking ? (Math.sin(x * 0.09 + t * 20) * Math.sin(x * 0.013 + t * 3)) * 24 : 1.5; g.moveTo(L.wave.x + x, L.wave.y + 30 - a); g.lineTo(L.wave.x + x, L.wave.y + 30 + a); } g.stroke();
  // 3 giây đầu: nhãn AI mở rộng
  if (t < 3) { g.fillStyle = "rgba(76,29,149,.92)"; roundRect(g, 76, 360, 928, 92, 18); g.fill(); g.fillStyle = "#fff"; g.font = `700 34px ${FONT}`; g.textAlign = "center";
    g.fillText("Video có sử dụng AI: MC ảo & giọng đọc tổng hợp", 540, 418); g.textAlign = "left"; }
  // 4 giây cuối: miễn trừ
  if (t >= D - 4) { const d = L.disclaimer; g.fillStyle = "rgba(0,0,0,.82)"; roundRect(g, d.x, d.y, d.w, d.h, 14); g.fill();
    g.fillStyle = "#FDE68A"; g.font = `600 28px ${FONT}`; g.textAlign = "center"; g.fillText(DISCLAIMER, d.x + d.w / 2, d.y + 45); g.textAlign = "left"; }
  if (opt.safe) { g.fillStyle = "rgba(244,63,94,.33)"; g.fillRect(0, 0, 1080, L.unsafe.topY); g.fillRect(0, L.unsafe.bottomY, 1080, 1920 - L.unsafe.bottomY); g.fillRect(L.unsafe.rightX, L.unsafe.rightFromY, 120, L.unsafe.bottomY - L.unsafe.rightFromY);
    g.fillStyle = "#fff"; g.font = `700 30px ${FONT}`; g.fillText("Vùng bị UI nền tảng che", 40, 1500); }
  g.restore();
}
function drawEmpty(g, msg = "Chưa có video", sub = "Bấm “Chạy quy trình” để dựng bản tin") {
  g.save(); g.scale(g.canvas.width / 1080, g.canvas.height / 1920);
  const bg = g.createLinearGradient(0, 0, 0, 1920); bg.addColorStop(0, "#0B1120"); bg.addColorStop(1, "#060912"); g.fillStyle = bg; g.fillRect(0, 0, 1080, 1920);
  g.strokeStyle = "rgba(148,163,184,.12)"; g.setLineDash([14, 12]); g.lineWidth = 3; roundRect(g, 60, 300, 960, 620, 28); g.stroke(); g.setLineDash([]);
  g.fillStyle = "#10B981"; g.fillRect(0, 940, 1080, 4);
  g.fillStyle = "#94A3B8"; g.font = `700 44px ${FONT}`; g.textAlign = "center"; g.fillText(msg, 540, 600); g.font = `400 30px ${FONT}`; g.fillStyle = "#64748B"; g.fillText(sub, 540, 656);
  g.globalAlpha = .45; g.drawImage(currentAvatar(), 0, 944, 1080, 976); g.restore();
}

/* ---------- Tạo một job demo hoàn chỉnh (không log) ---------- */
async function buildJob({now = new Date(), session_type = "PRE_MARKET", rate = 5, seedExtra = 0} = {}) {
  const news = await collectNews(now);
  const market = buildSnapshot(syntheticBars(now, 60, seedExtra), "Dữ liệu minh họa", "SYNTHETIC");
  const ctx = {run_date: ymd(now), session_type, market, news, hook_style: HOOKS[now.getDate() % HOOKS.length]};
  const script = templateScript(ctx);
  const words = wordTimings(viNormalize(script.video_script), rate);
  const cues = buildCues(words);
  return {id: uuid(), run_date: ymd(now), session_type, market, news, script, words, cues, ctx,
    duration_s: +((words.at(-1).end_ms + 600) / 1000).toFixed(2), data_quality: "SYNTHETIC", ai_label_applied: 1,
    video_title: script.video_title, social_post_text: script.social_post_text};
}

/* ---------- Trình phát canvas ---------- */
function makePlayer(canvas, {onTime, onState, voice} = {}) {
  const g = canvas.getContext("2d");
  const P = {job: null, t: 0, playing: false, safe: false, raf: 0, t0: 0, loop: false, speakOn: false};
  P.draw = () => { if (!P.job) { drawEmpty(g); return; } drawFrame(g, P.job, P.t, {safe: P.safe}); onTime?.(P.t, P.job.duration_s); };
  const tickFn = now => { if (!P.playing) return; P.t = (now - P.t0) / 1000;
    if (P.t >= P.job.duration_s) { if (P.loop) { P.t0 = now; P.t = 0; } else { P.t = P.job.duration_s; P.stop(); } }
    P.draw(); P.raf = requestAnimationFrame(tickFn); };
  P.play = () => { if (!P.job) return; if (P.t >= P.job.duration_s - .05) P.t = 0; P.playing = true; P.t0 = performance.now() - P.t * 1000;
    if (P.speakOn && P.t < 1) speak(P.job.script.video_script, voice?.() || {}); onState?.(true); P.raf = requestAnimationFrame(tickFn); };
  P.stop = () => { const was = P.playing; P.playing = false; cancelAnimationFrame(P.raf); if (was && P.speakOn && "speechSynthesis" in global) speechSynthesis.cancel(); onState?.(false); };
  P.toggle = () => P.playing ? P.stop() : P.play();
  P.seek = frac => { if (!P.job) return; const was = P.playing; if (was) { P.playing = false; cancelAnimationFrame(P.raf); }
    P.t = Math.max(0, Math.min(1, frac)) * P.job.duration_s; P.draw();
    if (was) { P.playing = true; P.t0 = performance.now() - P.t * 1000; P.raf = requestAnimationFrame(tickFn); } };
  P.load = (job, t0 = 4) => { P.stop(); P.job = job; P.t = job ? Math.min(t0, job.duration_s) : 0; P.draw(); };
  P.draw();
  return P;
}

global.SAI = {NFC, sleep, fmt, fmtSigned, dmy, ymd, uuid, esc, pad, SESSION_LABEL, FONT, L,
  mulberry32, tradingDaysBack, syntheticBars, sma, rsiWilder, buildSnapshot,
  NEWS_FIXTURE, collectNews, jaccard, DISCLAIMER, AI_DECL, BANNED, HOOKS, wc, templateScript,
  NUM_RE, parseVN, factcheck, annotateNumbers, postcheck, viNormalize, wordTimings, buildCues, toSRT, toASS,
  viVoices, speak, placeholderAvatar, cropPortrait, currentAvatar, setAvatar, roundRect,
  renderChart, renderCard, renderTickerStrip, prepareAssets, drawFrame, drawEmpty, buildJob, makePlayer};
})(window);
