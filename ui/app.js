// StockAI Studio — UI (ES module, không cần build). Gọi REST với X-App-Token, nhận sự kiện qua WebSocket.
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const qs = new URLSearchParams(location.search);
let TOKEN = qs.get("t");
try { if (TOKEN) sessionStorage.setItem("stockai.t", TOKEN); else TOKEN = sessionStorage.getItem("stockai.t"); } catch { /* bỏ qua */ }
if (TOKEN && qs.get("t")) history.replaceState(null, "", "/");

const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nf = d => new Intl.NumberFormat("vi-VN", {minimumFractionDigits:d, maximumFractionDigits:d});
const fmt = (x, d=2) => nf(d).format(x);
const sgn = (x, d=2) => (x >= 0 ? "+" : "-") + fmt(Math.abs(x), d);
const media = (job, f) => `/media/${job}/${encodeURIComponent(f)}?token=${encodeURIComponent(TOKEN)}`;
const SESSION = {PRE_MARKET:"Trước phiên", POST_MARKET:"Sau phiên", ADHOC:"Đột xuất"};
const PF = {telegram:"Telegram", facebook:"Facebook Reels", youtube:"YouTube Shorts", tiktok:"TikTok"};
const STATUS = {PENDING:["Chờ","b-dry"], RUNNING:["Đang chạy","b-run"], WAITING_APPROVAL:["Chờ duyệt","b-wait"], PUBLISHING:["Đang đăng","b-run"],
  COMPLETED:["Hoàn tất","b-ok"], FAILED:["Lỗi","b-fail"], CANCELLED:["Đã hủy","b-fail"], SKIPPED:["Bỏ qua","b-dry"]};
const DISCLAIMER = "Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.";
const AI_DECL = "Video có sử dụng AI (MC ảo, giọng đọc tổng hợp).";

async function api(path, opts = {}) {
  const r = await fetch(path, {...opts, headers: {"X-App-Token": TOKEN, ...(opts.body && !(opts.body instanceof FormData) ? {"Content-Type":"application/json"} : {}), ...(opts.headers||{})}});
  const data = await r.json().catch(() => ({}));
  if (!r.ok) { const e = data.error || {}; throw Object.assign(new Error(e.message || r.statusText), {code:e.code, hint:e.hint, status:r.status}); }
  return data;
}
const post = (p, b) => api(p, {method:"POST", body: b instanceof FormData ? b : JSON.stringify(b ?? {})});
const put = (p, b) => api(p, {method:"PUT", body: JSON.stringify(b)});
const del = p => api(p, {method:"DELETE"});

let toastT;
function toast(msg, kind="ok") { const t = $("#toast"); t.textContent = msg; t.style.borderLeftColor = {ok:"#10B981", warn:"#F59E0B", err:"#F43F5E", info:"#3B82F6"}[kind]; t.style.display = "block"; clearTimeout(toastT); toastT = setTimeout(() => t.style.display = "none", 5000); }
const fail = e => toast((e.message || e) + (e.hint ? " — " + e.hint : ""), "err");

if (!TOKEN) { document.body.innerHTML = `<div style="padding:40px;font-size:18px">Thiếu token phiên. Hãy mở ứng dụng bằng <code>uv run python app.py</code> (link có dạng /?t=...).</div>`; throw new Error("no token"); }

/* ---------------- điều hướng ---------------- */
function switchTab(t) { $$("#nav button").forEach(b => b.classList.toggle("on", b.dataset.tab === t)); $$(".tab").forEach(s => s.classList.toggle("on", s.id === "tab-" + t));
  ({lib: loadJobs, sched: loadSchedules, set: loadSettings, char: loadChar})[t]?.(); }
$$("#nav button").forEach(b => b.onclick = () => switchTab(b.dataset.tab));

/* ---------------- Bảng điều khiển ---------------- */
const STEPS = ["1. Thu thập", "2. AI biên tập", "3. Giọng và avatar", "4. Dựng video", "5. Xuất bản"];
const RANGE = [[0,20],[20,35],[35,70],[70,95],[95,100]];
$("#steps").innerHTML = STEPS.map((n,i) => `<div class="step" id="st${i+1}">${n}<div class="bar"></div></div>`).join("");
let status = {}, nextAt = null, logLines = [], currentJob = null;

function setProgress(step, pct) {
  $("#progBar").style.width = pct + "%";
  for (let i = 1; i <= 5; i++) { const el = $("#st" + i), [a,b] = RANGE[i-1];
    const f = Math.max(0, Math.min(1, (pct - a) / (b - a)));
    el.className = "step " + (pct >= b ? "done" : i === step ? "doing" : ""); el.querySelector(".bar").style.width = (f*100) + "%"; }
}
function termWrite(ev) {
  const term = $("#term"); if (!logLines.length) term.innerHTML = "";
  const ts = new Date(ev.ts || Date.now()).toLocaleTimeString("vi-VN", {hour12:false});
  const lv = ev.level || "INFO";
  logLines.push(`[${ts}] ${lv.padEnd(7)} ${ev.message}`);
  const d = document.createElement("div"); d.className = lv;
  d.innerHTML = `<span class="ts">[${ts}]</span> ${ev.step ? "B" + ev.step + " " : ""}${{SUCCESS:"✔",WARN:"⚠",ERROR:"✖"}[lv] || "›"} ${esc(ev.message)}`;
  term.appendChild(d); if (term.children.length > 1500) term.firstChild.remove(); term.scrollTop = term.scrollHeight;
}
$("#copyLog").onclick = () => { navigator.clipboard?.writeText(logLines.join("\n")); toast("Đã sao chép log"); };
$("#clrLog").onclick = () => { logLines = []; $("#term").innerHTML = '<span class="muted">Log trống.</span>'; };

async function refreshStatus() {
  try { status = await api("/api/status"); } catch (e) { return; }
  const m = status.market;
  if (m) { $("#cIdx").textContent = fmt(m.close); $("#cChg").innerHTML = `<span class="${m.change >= 0 ? "up" : "down"}">${sgn(m.change)} (${sgn(m.change_pct)}%)</span> · phiên ${m.session_date.split("-").reverse().join("/")}`;
    const q = {LIVE:["live","b-live"], CACHED:["cached","b-cache"], SYNTHETIC:["minh họa","b-syn"]}[m.data_quality]; $("#qBadge").textContent = q[0]; $("#qBadge").className = "badge " + q[1];
    $("#cSpark").innerHTML = sparkSvg(m.spark || [], m.change >= 0); }
  $("#cVid").textContent = status.videos; $("#cWait").textContent = `${status.waiting} chờ duyệt`;
  $("#navWait").innerHTML = status.waiting ? `<span class="badge b-wait">${status.waiting}</span>` : "";
  const prod = status.mode === "PRODUCTION";
  $("#cMode").textContent = prod ? "Production" : "Demo";
  $("#cCost").textContent = prod ? `$${(status.cost_month_usd||0).toFixed(2)} tháng này` : "0 đồng";
  $("#banner").className = "banner" + (prod ? " prod" : "");
  $("#banner").textContent = prod ? "PRODUCTION · luôn duyệt trước khi đăng" : "Chế độ demo · dữ liệu công khai/minh họa · avatar chuyển động nhẹ · 0 đồng";
  nextAt = status.next_run_at ? new Date(status.next_run_at) : null;
  setRunning(!!status.running_job);
  if (status.running_job && currentJob !== status.running_job) {  // mở trang giữa lúc job đang chạy → nạp log cũ
    currentJob = status.running_job; $("#jobLbl").textContent = "· job " + currentJob.slice(0,8);
    const j = await api("/api/jobs/" + currentJob).catch(() => null);
    if (j) { logLines = []; j.events.forEach(e => termWrite({...e, ts: e.ts})); setProgress(j.current_step, j.progress_pct); }
  }
  if (status.interrupted && !refreshStatus.warned) { refreshStatus.warned = true; toast(`${status.interrupted} job bị gián đoạn lần trước đã chuyển sang Lỗi (INTERRUPTED)`, "warn"); }
  $("#pfBanner").innerHTML = status.preflight_ok === false ? `<div class="errbox">⚠ Môi trường chưa đủ (FFmpeg/filter/font). Xem Cài đặt → Kiểm tra môi trường. Gợi ý: <code>winget install Gyan.FFmpeg</code></div>` : "";
}
function sparkSvg(v, up) {  // sparkline 30 phiên (SVG thuần, không cần thư viện)
  if (v.length < 2) return "";
  const lo = Math.min(...v), hi = Math.max(...v), W = 160, H = 44, col = up ? "#10B981" : "#F43F5E";
  const pts = v.map((x, i) => `${(i / (v.length - 1) * W).toFixed(1)},${(H - 4 - (x - lo) / (hi - lo || 1) * (H - 10)).toFixed(1)}`).join(" ");
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><defs><linearGradient id="sg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${col}" stop-opacity=".35"/><stop offset="1" stop-color="${col}" stop-opacity="0"/></linearGradient></defs><polygon points="0,${H} ${pts} ${W},${H}" fill="url(#sg)"/><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`;
}
function tickCountdown() {
  if (!nextAt) { $("#cNext").textContent = "--:--"; $("#cCount").textContent = "Chưa có lịch đang bật"; return; }
  const s = Math.max(0, Math.floor((nextAt - new Date()) / 1000));
  $("#cNext").textContent = nextAt.toLocaleTimeString("vi-VN", {hour:"2-digit", minute:"2-digit", hour12:false});
  const day = s >= 86400 ? ` (${["CN","T2","T3","T4","T5","T6","T7"][nextAt.getDay()]})` : "";
  $("#cCount").textContent = `còn ${String(Math.floor(s/3600)).padStart(2,"0")}:${String(Math.floor(s/60)%60).padStart(2,"0")}:${String(s%60).padStart(2,"0")}${day}`;
}
function setRunning(on) { const b = $("#runBtn"); b.classList.toggle("busy", on); b.querySelector("span").textContent = on ? "Hủy job đang chạy" : "Chạy quy trình ngay"; }
$("#runBtn").onclick = async () => {
  if ($("#runBtn").classList.contains("busy")) { if (confirm("Hủy job đang chạy?")) { await post("/api/pipeline/cancel").catch(fail); } return; }
  try { logLines = []; $("#term").innerHTML = ""; setProgress(0, 0);
    const r = await post("/api/pipeline/run", {session_type: $("#sessSel").value, offline: $("#offChk").checked, platforms: ["telegram"]});
    currentJob = r.job_id; $("#jobLbl").textContent = "· job " + r.job_id.slice(0,8); setRunning(true); toast("Đã bắt đầu job " + r.job_id.slice(0,8), "info");
  } catch (e) { if (e.status === 409) toast("Đang có job chạy (409) — vui lòng chờ", "warn"); else fail(e); }
};
async function showDashVideo(jobId) {
  const box = $("#dashV");
  let j = null;
  try { j = jobId ? await api("/api/jobs/" + jobId) : (await api("/api/jobs?limit=20")).find(x => x.final_video_path); } catch { /* */ }
  if (!j || !j.final_video_path) return;
  box.innerHTML = `<video controls playsinline poster="${media(j.id, "thumbnail.jpg")}" src="${media(j.id, "final.mp4")}"></video>`;
  $("#dashCap").innerHTML = `${esc(j.video_title || "")}<br><span class="badge ${STATUS[j.status]?.[1]}">${STATUS[j.status]?.[0]}</span> <a href="#" id="toLib">Mở trong Kho nội dung</a>`;
  $("#toLib").onclick = e => { e.preventDefault(); selected = j.id; switchTab("lib"); };
}

/* ---------------- WebSocket ---------------- */
function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws/events?token=${encodeURIComponent(TOKEN)}`);
  ws.onopen = () => $("#conn").classList.add("on");
  ws.onclose = () => { $("#conn").classList.remove("on"); setTimeout(connectWS, 2000); };
  ws.onmessage = m => { const ev = JSON.parse(m.data);
    if (ev.type === "log") { if (ev.job_id && ev.job_id !== currentJob) { currentJob = ev.job_id; logLines = []; $("#jobLbl").textContent = "· job " + ev.job_id.slice(0,8); setRunning(true); } termWrite(ev); }
    else if (ev.type === "progress") setProgress(ev.step, ev.progress);
    else if (ev.type === "job_status") { refreshStatus();
      if (ev.status === "WAITING_APPROVAL") { toast("Video đã dựng xong — đang chờ bạn duyệt", "warn"); showDashVideo(ev.job_id); }
      if (ev.status === "COMPLETED") { setProgress(5, 100); showDashVideo(ev.job_id); }
      if (["FAILED","CANCELLED"].includes(ev.status)) { const st = $$(".step.doing")[0]; st && st.classList.add("err"); }
      if (["COMPLETED","FAILED","CANCELLED","SKIPPED","WAITING_APPROVAL"].includes(ev.status)) setRunning(false);
      if ($("#tab-lib").classList.contains("on")) loadJobs(); }
    else if (ev.type === "schedule") { nextAt = ev.next_run_at ? new Date(ev.next_run_at) : null; }
  };
}

/* ---------------- Nhân vật & giọng ---------------- */
let settings = {}, pendingFile = null;
async function loadChar() {
  settings = await api("/api/settings").catch(() => settings);
  const a = await api("/api/assets").catch(() => ({}));
  if (a.avatar) { $("#avImg").src = `/asset/${a.avatar.id}?token=${encodeURIComponent(TOKEN)}`;
    $("#avStatus").innerHTML = a.avatar.is_placeholder ? "Đang dùng <b>ảnh mẫu</b> do app tự vẽ (is_placeholder=1)." : `Đang dùng ảnh của <b>${esc(a.avatar.consent?.subject_name)}</b> · ${a.avatar.width}×${a.avatar.height}px · đồng ý ghi nhận ${esc(a.avatar.consent?.created_at)}`; }
  else { $("#avImg").removeAttribute("src"); $("#avStatus").textContent = "Chưa có ảnh — lần chạy đầu sẽ tạo ảnh mẫu."; }
  $("#logoSt").textContent = a.logo ? `Đang dùng logo ${a.logo.width}×${a.logo.height}` : "Chưa có logo (dùng biểu tượng mặc định)";
  $("#bgmSt").textContent = a.bgm ? `Nhạc nền ${Math.round(a.bgm.duration_s)} giây` : "Không có nhạc nền";
  $("#avProv").value = settings["avatar.provider"] || "demo"; $("#falModel").value = settings["avatar.fal_model"];
  $("#maxCost").value = settings["avatar.max_cost_usd"]; $("#voiceSel").value = settings["tts.voice"]; $("#numMode").value = settings["tts.number_mode"] || "engine";
  $("#rate").value = parseInt(settings["tts.rate"] || "5"); updRate(); renderCost();
}
const updRate = () => $("#rateLbl").textContent = ($("#rate").value >= 0 ? "+" : "") + $("#rate").value + "%";
$("#rate").oninput = updRate;
const PRICE = {"fal-ai/kling-video/ai-avatar/v2/standard":0.0562, "fal-ai/kling-video/ai-avatar/v2/pro":0.115, "fal-ai/bytedance/omnihuman":0.14};
function renderCost() { const p = $("#avProv").value, D = 75;
  const c = p === "demo" ? 0 : p === "heygen" ? 0.10*D : p === "hybrid" ? 15*PRICE[$("#falModel").value] : PRICE[$("#falModel").value]*D;
  $("#costEst").innerHTML = p === "demo" ? "Ước tính: <b>0 đồng/video</b> (ảnh thật + chuyển động nhẹ + sóng âm, không khớp môi)." :
    `Ước tính ≈ <b>$${c.toFixed(2)}/video</b> (video 75 giây) · ≈ $${(c*44).toFixed(0)}/tháng cho 44 video.<br><span class="small">Chỉ dùng ở PRODUCTION; DEMO luôn dùng DemoMotion. Giá cần kiểm chứng lại trước khi bật.</span>`; }
$("#avProv").onchange = renderCost; $("#falModel").onchange = renderCost;
$("#voiceSave").onclick = async () => { try { await put("/api/settings", {"avatar.provider": $("#avProv").value, "avatar.fal_model": $("#falModel").value, "avatar.max_cost_usd": $("#maxCost").value,
  "tts.voice": $("#voiceSel").value, "tts.rate": ($("#rate").value >= 0 ? "+" : "") + $("#rate").value + "%", "tts.number_mode": $("#numMode").value}); toast("Đã lưu"); } catch (e) { fail(e); } };
$("#ttsBtn").onclick = async () => { $("#ttsBtn").disabled = true; $("#ttsBtn").textContent = "Đang tạo…";
  try { const r = await post("/api/tts/preview", {voice: $("#voiceSel").value, rate: ($("#rate").value >= 0 ? "+" : "") + $("#rate").value + "%", text: $("#ttsText").value});
    const au = $("#ttsAudio"); au.src = r.url + "?token=" + encodeURIComponent(TOKEN); au.style.display = "block"; au.play(); $("#ttsNorm").textContent = "Văn bản đã chuẩn hóa: " + r.text;
  } catch (e) { fail(e); } finally { $("#ttsBtn").disabled = false; $("#ttsBtn").textContent = "🔊 Nghe thử"; } };
function pickAvatar(f) { if (!f || !f.type.startsWith("image/")) return toast("Hãy chọn file ảnh", "warn"); pendingFile = f;
  $("#avImg").src = URL.createObjectURL(f); $("#avStatus").innerHTML = `<span class="muted">Đã chọn: ${esc(f.name)} — nhập tên, tick đồng ý rồi bấm “Tải ảnh lên”.</span>`; updUploadBtn(); }
const updUploadBtn = () => $("#avUpload").disabled = !(pendingFile && $("#consChk").checked && $("#consName").value.trim());
$("#drop").onclick = () => $("#avFile").click(); $("#avFile").onchange = e => pickAvatar(e.target.files[0]);
$("#drop").ondragover = e => { e.preventDefault(); $("#drop").classList.add("over"); }; $("#drop").ondragleave = () => $("#drop").classList.remove("over");
$("#drop").ondrop = e => { e.preventDefault(); $("#drop").classList.remove("over"); pickAvatar(e.dataTransfer.files[0]); };
$("#consChk").onchange = updUploadBtn; $("#consName").oninput = updUploadBtn;
$("#avUpload").onclick = async () => { const fd = new FormData(); fd.append("kind","avatar"); fd.append("file", pendingFile);
  fd.append("consent_subject_name", $("#consName").value.trim()); fd.append("consent_relation", $("#consRel").value); fd.append("consent_statement", $("#consTxt").textContent);
  try { const r = await post("/api/assets/upload", fd); pendingFile = null; toast(r.warning || "Đã lưu ảnh chân dung + bản ghi đồng ý", r.warning ? "warn" : "ok"); loadChar(); } catch (e) { fail(e); } };
$("#avReset").onclick = async () => { await del("/api/assets/avatar").catch(fail); toast("Lần chạy tới sẽ dùng ảnh mẫu"); loadChar(); };
async function uploadSimple(kind, f, lbl) { const fd = new FormData(); fd.append("kind", kind); fd.append("file", f); try { await post("/api/assets/upload", fd); toast("Đã tải " + lbl); loadChar(); } catch (e) { fail(e); } }
$("#logoBtn").onclick = () => $("#logoFile").click(); $("#logoFile").onchange = e => uploadSimple("logo", e.target.files[0], "logo");
$("#bgmBtn").onclick = () => $("#bgmFile").click(); $("#bgmFile").onchange = e => uploadSimple("bgm", e.target.files[0], "nhạc nền");
$("#bgmDel").onclick = async () => { await del("/api/assets/bgm").catch(fail); loadChar(); };

/* ---------------- Kho nội dung ---------------- */
let selected = null, jobsCache = [];
async function loadJobs() {
  const f = $("#libFilter").value;
  jobsCache = await api("/api/jobs?limit=100" + (f ? "&status=" + f : "")).catch(() => []);
  $("#jobList").innerHTML = jobsCache.length ? jobsCache.map(j => { const [lb, cl] = STATUS[j.status] || [j.status, "b-dry"];
    const q = j.data_quality ? `<span class="badge ${j.data_quality==="SYNTHETIC"?"b-syn":j.data_quality==="LIVE"?"b-live":"b-cache"}">${j.data_quality==="SYNTHETIC"?"MINH HỌA":j.data_quality}</span>` : "";
    return `<div class="job ${j.id===selected?"sel":""} ${j.status==="WAITING_APPROVAL"?"wait":""}" data-id="${j.id}"><div><b>${esc(j.video_title || "(chưa có tiêu đề)")}</b>
      <div class="small muted">${new Date(j.created_at.replace(" ","T")+"Z").toLocaleString("vi-VN")} · ${SESSION[j.session_type]} · ${j.trigger} · ${j.duration_s ? fmt(j.duration_s,1)+" giây" : ""} ${j.error_message ? "· " + esc(j.error_message).slice(0,80) : ""}</div></div>
      <div style="white-space:nowrap">${q}<span class="badge ${cl}">${lb}</span></div></div>`; }).join("") : `<div class="muted">Chưa có video. Vào Bảng điều khiển → Chạy quy trình ngay.</div>`;
  $$("#jobList .job").forEach(el => el.onclick = () => { selected = el.dataset.id; loadJobs(); });
  if (!selected && jobsCache[0]) selected = jobsCache[0].id;
  renderDetail();
}
$("#libFilter").onchange = loadJobs;
const PRIV = {telegram:["channel"], facebook:["published"], youtube:["private","unlisted","public"], tiktok:["SELF_ONLY","MUTUAL_FOLLOW_FRIENDS","PUBLIC_TO_EVERYONE"]};
async function renderDetail() {
  const box = $("#jobDetail"); if (!selected) { box.innerHTML = ""; return; }
  let j; try { j = await api("/api/jobs/" + selected); } catch { box.innerHTML = ""; return; }
  const s = j.script, hasV = !!j.final_video_path, synth = j.data_quality === "SYNTHETIC";
  const logs = j.publish_logs.map(l => `<tr><td>${PF[l.platform]}</td><td><span class="badge ${l.status==="SUCCESS"?"b-ok":l.status==="FAILED"?"b-fail":"b-dry"}">${l.status}</span></td><td class="small">${esc(l.privacy_level||"")}</td><td class="small">${l.remote_post_url ? `<a href="${esc(l.remote_post_url)}" target="_blank">mở bài</a>` : esc(l.error_message||"")}</td></tr>`).join("");
  box.innerHTML = `<div class="detail">
    <div class="phone">
      <div class="vbox">${hasV ? `<video id="libVideo" controls playsinline poster="${media(j.id,"thumbnail.jpg")}" src="${media(j.id,"final.mp4")}"></video>` : `<div class="empty">Chưa có video<br>${esc(j.error_message||"")}</div>`}
        <div class="sz" id="szOv"><div style="left:0;right:0;top:0;height:6.25%"></div><div style="left:0;right:0;top:75%;bottom:0"></div><div style="left:88.9%;right:0;top:43.75%;height:31.25%"></div></div></div>
      <div class="row small" style="justify-content:center;margin-top:8px"><label><input type="checkbox" id="szChk"> Lớp safe-zone</label></div>
      <div class="row" style="justify-content:center;margin-top:8px">${hasV ? `<a class="btn small" href="${media(j.id,"final.mp4")}" download="stockai_${j.run_date}.mp4">Tải video</a>` : ""}
        <button class="btn small" id="openDir">Mở thư mục</button>${hasV && j.artifacts.includes("safe_zone_check.png") ? `<a class="btn small" href="${media(j.id,"safe_zone_check.png")}" target="_blank">Ảnh kiểm safe-zone</a>` : ""}</div>
      <div class="row" style="justify-content:center;margin-top:8px"><button class="btn small" id="retryBtn" ${["FAILED","CANCELLED"].includes(j.status)?"":"disabled"}>Chạy lại từ bước lỗi</button><button class="btn small danger" id="delBtn">Xóa job</button></div>
      <div class="small muted" style="margin-top:8px">LLM: ${esc(j.llm_provider||"-")} · factcheck ${j.factcheck_passed===1?"ĐẠT":j.factcheck_passed===0?"LLM lỗi → fallback":"-"}<br>Avatar: ${esc(j.avatar_provider||"-")} · chi phí $${(j.est_cost_usd||0).toFixed(2)}</div>
    </div>
    <div class="card">
      <div class="subtabs">${["Bài đăng","Kịch bản","Biểu đồ","Tin nguồn","Phụ đề","Log"].map((n,i)=>`<button data-p="${i}" class="${i===0?"on":""}">${n}</button>`).join("")}</div>
      <div class="pane on" data-p="0">${s ? `
        ${synth ? `<div class="note">⚠ Video dùng DỮ LIỆU MINH HỌA → chỉ được dry-run (lưu bản xem trước), không đăng thật (R-DATA-2, R-PUB-1).</div>` : ""}
        <label class="f">Tiêu đề video (≤ 80 ký tự)</label><input type="text" id="edTitle" maxlength="80" value="${esc(j.video_title)}">
        <label class="f">Bài đăng</label><textarea id="edPost">${esc(j.social_post_text)}</textarea>
        <div class="row" style="margin-top:8px"><button class="btn" id="saveEd">Lưu chỉnh sửa</button><button class="btn" id="copyPost">Copy bài đăng</button><span class="small" id="edCheck"></span></div>
        <h3 style="margin-top:18px">Duyệt &amp; Đăng</h3>
        ${Object.keys(PF).map(p => `<div class="pub"><input type="checkbox" class="pubChk" value="${p}" ${p==="telegram"?"checked":""}><span>${PF[p]}</span><select class="pubPriv" data-p="${p}">${PRIV[p].map(o=>`<option>${o}</option>`).join("")}</select></div>`).join("")}
        <div class="small muted">TikTok: mặc định gửi nháp vào hộp thư TikTok, bật nhãn AI (is_aigc). YouTube: bật containsSyntheticMedia, mặc định private.</div>
        <div class="row" style="margin-top:10px"><button class="btn ok" id="approveBtn" ${j.status==="WAITING_APPROVAL"?"":"disabled"}>Duyệt &amp; Đăng</button>
          <button class="btn" id="repubBtn" ${j.status==="COMPLETED"&&hasV?"":"disabled"}>Đăng thêm nền tảng</button>
          <label class="small"><input type="checkbox" id="dryChk" ${synth?"checked disabled":""}> Chỉ dry-run</label></div>
        ${logs ? `<table style="margin-top:12px"><tr><th>Nền tảng</th><th>Trạng thái</th><th>Quyền riêng tư</th><th>Kết quả</th></tr>${logs}</table>` : ""}
        ${j.publish_preview ? `<details style="margin-top:8px"><summary class="small">publish_preview.json</summary><pre class="box">${esc(JSON.stringify(j.publish_preview,null,2))}</pre></details>` : ""}` : `<div class="muted">Job chưa có kịch bản.</div>`}</div>
      <div class="pane" data-p="1">${s ? `<div class="small muted">${s.video_script.split(/\s+/).length} từ · sentiment ${s.market_sentiment}</div><pre class="box">${esc(s.video_script)}</pre>
        <h3 style="margin-top:12px">2 kịch bản</h3>${s.scenarios.map(x=>`<div><b>${x.name}:</b> ${esc(x.description)}</div>`).join("")}
        <h3 style="margin-top:12px">Tin được chọn</h3>${s.selected_news.map(x=>`<div>• [${x.impact}] ${esc(x.headline)}</div>`).join("")}
        <h3 style="margin-top:12px">Ticker</h3><pre class="box">${esc(s.ticker_text)}</pre>` : ""}</div>
      <div class="pane" data-p="2">${j.artifacts.includes("chart.png") ? `<img src="${media(j.id,"chart.png")}" style="width:100%;border-radius:8px">` : ""}
        <div class="row" style="margin-top:8px">${j.artifacts.filter(a=>/^news_card_\d\.png$/.test(a)).map(a=>`<img src="${media(j.id,a)}" style="width:32%;border-radius:6px">`).join("")}</div></div>
      <div class="pane" data-p="3"><table>${(j.news||[]).map((n,i)=>`<tr><td>#${i}</td><td><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.title)}</a><div class="small muted">${esc(n.summary)}</div></td><td>${esc(n.source)}</td><td class="small">${n.score}</td></tr>`).join("")}</table></div>
      <div class="pane" data-p="4">${j.artifacts.includes("subs.srt") ? `<div class="row"><a class="btn small" href="${media(j.id,"subs.srt")}" download>Tải subs.srt</a><a class="btn small" href="${media(j.id,"subs.ass")}" download>Tải subs.ass</a><a class="btn small" href="${media(j.id,"voice.mp3")}" download>Tải voice.mp3</a></div><pre class="box" id="srtBox" style="margin-top:8px">Đang tải…</pre>` : ""}</div>
      <div class="pane" data-p="5"><pre class="box">${esc(j.events.map(e=>`[${e.ts.slice(11,19)}] B${e.step??"-"} ${e.level.padEnd(7)} ${e.message}`).join("\n"))}</pre></div>
    </div></div>`;
  $$("#jobDetail .subtabs button").forEach(b => b.onclick = () => { $$("#jobDetail .subtabs button").forEach(x => x.classList.toggle("on", x===b)); $$("#jobDetail .pane").forEach(p => p.classList.toggle("on", p.dataset.p === b.dataset.p));
    if (b.dataset.p === "4" && $("#srtBox")) fetch(media(j.id,"subs.srt")).then(r=>r.text()).then(t => $("#srtBox").textContent = t); });
  $("#szChk").onchange = e => $("#szOv").classList.toggle("on", e.target.checked);
  $("#openDir").onclick = () => post("/api/maintenance/open-folder", {job_id: j.id}).catch(fail);
  $("#delBtn").onclick = async () => { if (!confirm("Xóa job và toàn bộ file của nó?")) return; await del("/api/jobs/" + j.id).catch(fail); selected = null; loadJobs(); refreshStatus(); };
  $("#retryBtn").onclick = async () => { try { await post(`/api/jobs/${j.id}/retry`, {}); toast("Đang chạy lại từ bước lỗi", "info"); switchTab("dash"); } catch (e) { fail(e); } };
  if (!s) return;
  const check = () => { const t = $("#edPost").value, errs = [];
    if (!t.includes(DISCLAIMER)) errs.push("thiếu câu miễn trừ"); if (!t.includes(AI_DECL)) errs.push("thiếu khai báo AI");
    ["chắc chắn","mua ngay","bắt đáy ngay","x2 tài khoản","cơ hội cuối cùng"].forEach(b => t.toLowerCase().includes(b) && errs.push(`cụm cấm “${b}”`));
    $("#edCheck").innerHTML = errs.length ? `<span class="down">⚠ ${errs.join(", ")}</span>` : `<span class="up">✓ Đạt kiểm tra pháp lý</span>`; return !errs.length; };
  $("#edPost").oninput = check; check();
  const save = async () => { if (!check()) throw new Error("Bài đăng chưa đạt kiểm tra"); await put("/api/jobs/" + j.id, {video_title: $("#edTitle").value, social_post_text: $("#edPost").value}); };
  $("#saveEd").onclick = () => save().then(() => toast("Đã lưu chỉnh sửa")).catch(fail);
  $("#copyPost").onclick = () => { navigator.clipboard?.writeText($("#edPost").value); toast("Đã copy bài đăng"); };
  const pub = async (path) => { try { await save(); const ps = $$(".pubChk").filter(c => c.checked).map(c => c.value); if (!ps.length) return toast("Chọn ít nhất 1 nền tảng", "warn");
      const privacy = {}; $$(".pubPriv").forEach(x => privacy[x.dataset.p] = x.value);
      const r = await post(`/api/jobs/${j.id}/${path}`, {platforms: ps, privacy, dry_run: $("#dryChk").checked});
      toast(r.results.map(x => `${PF[x.platform]}: ${x.status}`).join(" · ") || "Không có gì để đăng", r.results.some(x => x.status === "FAILED") ? "warn" : "ok"); renderDetail(); refreshStatus();
    } catch (e) { fail(e); } };
  $("#approveBtn").onclick = () => pub("approve"); $("#repubBtn").onclick = () => pub("publish");
}

/* ---------------- Lịch ---------------- */
async function loadSchedules() {
  const rows = await api("/api/schedules").catch(() => []);
  $("#sTable").innerHTML = rows.map(s => `<tr><td><label class="switch"><input type="checkbox" data-tog="${s.id}" ${s.is_active?"checked":""}><span></span></label></td>
    <td><b>${esc(s.name)}</b><div class="small muted">${SESSION[s.session_type]} · ${s.days_of_week==="mon-fri"?"T2–T6":"Cả tuần"} · ${s.target_platforms.map(p=>PF[p]).join(", ")} · ${s.require_approval?"chờ duyệt":"tự đăng (trừ TikTok)"}</div>
      ${s.next_run_at ? `<div class="small muted">Lần tới: ${new Date(s.next_run_at).toLocaleString("vi-VN")}</div>` : ""}</td>
    <td>${String(s.cron_hour).padStart(2,"0")}:${String(s.cron_minute).padStart(2,"0")}</td>
    <td class="small">${s.last_run_at ? esc(s.last_run_at) + "<br>" + (STATUS[s.last_status]?.[0] || "") : "—"}</td>
    <td><button class="btn small" data-edit="${s.id}">Sửa</button> <button class="btn small danger" data-del="${s.id}">Xóa</button></td></tr>`).join("") || `<tr><td colspan="5" class="muted">Chưa có lịch.</td></tr>`;
  const body = s => ({name:s.name, session_type:s.session_type, cron_hour:s.cron_hour, cron_minute:s.cron_minute, days_of_week:s.days_of_week, target_platforms:s.target_platforms, require_approval:!!s.require_approval, is_active:!!s.is_active});
  $$("[data-tog]").forEach(c => c.onchange = async () => { const s = rows.find(x => x.id == c.dataset.tog); await put("/api/schedules/" + s.id, {...body(s), is_active: c.checked}).catch(fail); loadSchedules(); refreshStatus(); });
  $$("[data-del]").forEach(b => b.onclick = async () => { if (!confirm("Xóa lịch này?")) return; await del("/api/schedules/" + b.dataset.del).catch(fail); loadSchedules(); refreshStatus(); });
  $$("[data-edit]").forEach(b => b.onclick = () => { const s = rows.find(x => x.id == b.dataset.edit); $("#sId").value = s.id; $("#sName").value = s.name; $("#sType").value = s.session_type;
    $("#sTime").value = `${String(s.cron_hour).padStart(2,"0")}:${String(s.cron_minute).padStart(2,"0")}`; $("#sDays").value = s.days_of_week === "mon-fri" ? "mon-fri" : "mon-sun";
    $$("#sPf input").forEach(c => c.checked = s.target_platforms.includes(c.value)); $("#sAppr").checked = !!s.require_approval; $("#sFormTitle").textContent = "Sửa lịch #" + s.id; });
}
function formBody() { const [h, m] = $("#sTime").value.split(":").map(Number);
  return {name: $("#sName").value || "Lịch mới", session_type: $("#sType").value, cron_hour: h, cron_minute: m, days_of_week: $("#sDays").value,
    target_platforms: $$("#sPf input").filter(c => c.checked).map(c => c.value), require_approval: $("#sAppr").checked, is_active: true}; }
$("#sSave").onclick = async () => { try { const id = $("#sId").value; if (id) await put("/api/schedules/" + id, formBody()); else await post("/api/schedules", formBody());
  toast("Đã lưu lịch — đồng bộ ngay, không cần khởi động lại"); $("#sNew").click(); loadSchedules(); refreshStatus(); } catch (e) { fail(e); } };
$("#sNew").onclick = () => { $("#sId").value = ""; $("#sFormTitle").textContent = "Thêm lịch"; };
$("#sQuick").onclick = async () => { const d = new Date(Date.now() + 120000);
  try { await post("/api/schedules", {name:"Lịch thử nghiệm", session_type:"PRE_MARKET", cron_hour:d.getHours(), cron_minute:d.getMinutes(), days_of_week:"mon-sun", target_platforms:["telegram"], require_approval:true, is_active:true});
    toast(`Đã tạo lịch lúc ${d.toLocaleTimeString("vi-VN",{hour:"2-digit",minute:"2-digit"})}. Giữ app mở và xem Bảng điều khiển.`, "info"); loadSchedules(); refreshStatus(); } catch (e) { fail(e); } };

/* ---------------- Cài đặt ---------------- */
const KEYS = [["AI","gemini_api_key","Gemini API key","gemini"],["AI","openai_api_key","OpenAI-compatible API key",null],
  ["Dữ liệu","ssi_consumer_id","SSI FastConnect Consumer ID","ssi"],["Dữ liệu","ssi_consumer_secret","SSI FastConnect Consumer Secret",null],
  ["Avatar & Giọng","fal_key","fal.ai key","fal"],["Avatar & Giọng","heygen_api_key","HeyGen API key","heygen"],["Avatar & Giọng","elevenlabs_api_key","ElevenLabs API key",null],
  ["Mạng xã hội","telegram_bot_token","Telegram Bot Token","telegram"],["Mạng xã hội","facebook_page_token","Facebook Page Token","facebook"],
  ["Mạng xã hội","youtube_oauth_token","YouTube OAuth (đăng nhập bằng: uv run python -m stockai youtube-login client_secret.json)","youtube"],["Mạng xã hội","tiktok_access_token","TikTok access token","tiktok"]];
async function loadSettings() {
  settings = await api("/api/settings").catch(() => settings);
  $("#modeSw").checked = settings.mode === "PRODUCTION";
  $$("[data-set]").forEach(el => el.value = settings[el.dataset.set] ?? "");
  let grp = ""; $("#keys").innerHTML = KEYS.map(([g,k,lb,svc]) => { const h = g !== grp ? `<h3 style="margin-top:14px">${g}</h3>` : ""; grp = g;
    return `${h}<label class="f">${esc(lb)} ${settings[k] ? `<span class="badge b-ok">${esc(settings[k])}</span>` : `<span class="badge b-dry">chưa có</span>`}</label>
      <div class="row" style="flex-wrap:nowrap"><input type="password" data-key="${k}" placeholder="${settings[k] ? "Nhập để thay khóa mới" : "Dán khóa vào đây"}" autocomplete="off">
      <button class="btn small" data-savekey="${k}">Lưu</button>${settings[k] ? `<button class="btn small danger" data-delkey="${k}">Xóa</button>` : ""}${svc ? `<button class="btn small" data-test="${svc}">Kiểm tra kết nối</button>` : ""}</div>`; }).join("");
  $$("[data-savekey]").forEach(b => b.onclick = async () => { const i = $(`[data-key="${b.dataset.savekey}"]`); if (!i.value.trim()) return toast("Chưa nhập khóa", "warn");
    await put("/api/settings", {[b.dataset.savekey]: i.value.trim()}).catch(fail); toast("Đã lưu vào keyring hệ điều hành"); loadSettings(); });
  $$("[data-delkey]").forEach(b => b.onclick = async () => { await put("/api/settings", {[b.dataset.delkey]: ""}).catch(fail); loadSettings(); });
  $$("[data-test]").forEach(b => b.onclick = async () => { b.disabled = true; try { const r = await post("/api/settings/test/" + b.dataset.test); toast(`${b.dataset.test}: ${r.message}`, r.ok ? "ok" : "warn"); } catch (e) { fail(e); } finally { b.disabled = false; } });
  const pf = await api("/api/preflight").catch(() => null);
  if (pf) $("#pfTable").innerHTML = pf.items.map(i => `<tr><td>${i.ok ? "✅" : i.name.startsWith("Khóa") ? "➖" : "❌"}</td><td>${esc(i.name)}<div class="small muted">${esc(i.note)}</div></td></tr>`).join("");
  renderProd();
}
async function renderProd() {
  if (!$("#modeSw").checked) { $("#prodCheck").innerHTML = `<div class="info">DEMO: nguồn dữ liệu công khai (không chính thức) → cache → dữ liệu minh họa có nhãn; kịch bản Gemini (nếu có khóa) hoặc mẫu; giọng edge-tts; avatar chuyển động nhẹ; đăng Telegram thật hoặc dry-run. Chi phí 0 đồng.</div>`; return; }
  const r = await api("/api/settings/production-check").catch(() => ({missing:[]}));
  $("#prodCheck").innerHTML = r.ready ? `<div class="info">✓ Đủ điều kiện PRODUCTION.</div>` : `<div class="note"><b>Điều kiện còn thiếu cho PRODUCTION:</b><ul style="margin:6px 0 0;padding-left:18px">${r.missing.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>`;
}
$("#modeSw").onchange = async e => { await put("/api/settings", {mode: e.target.checked ? "PRODUCTION" : "DEMO"}).catch(fail); renderProd(); refreshStatus(); };
$("#setSave").onclick = async () => { const b = {}; $$("[data-set]").forEach(el => b[el.dataset.set] = el.value); try { await put("/api/settings", b); toast("Đã lưu cài đặt"); loadSettings(); } catch (e) { fail(e); } };
$("#cleanBtn").onclick = async () => { const days = parseInt(prompt("Xóa file cũ hơn bao nhiêu ngày?", settings["retention.days"] || "30")); if (!days) return;
  const r = await post("/api/maintenance/cleanup", {older_than_days: days}).catch(fail); if (r) $("#maintMsg").textContent = `Đã xóa ${r.removed_days} ngày, giải phóng ${r.freed_mb} MB.`; };
$("#openData").onclick = () => post("/api/maintenance/open-folder", {}).catch(fail);
$("#diagBtn").onclick = async () => { const r = await api("/api/maintenance/diagnostics").catch(fail); if (!r) return;
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(r, null, 2)], {type:"application/json"})); a.download = "stockai_diagnostics.json"; a.click(); };

/* ---------------- khởi động ---------------- */
connectWS(); refreshStatus(); showDashVideo(); setInterval(tickCountdown, 1000); setInterval(refreshStatus, 30000);
