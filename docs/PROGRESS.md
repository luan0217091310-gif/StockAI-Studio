# PROGRESS — Nhật ký tiến độ

> Cập nhật sau mỗi phần việc. Mới nhất ở trên cùng.

## 23/11/2026 — đợt 2
- [x] M2: LLM providers (Gemini, OpenAI-compatible, TemplateFallback), prompt đúng Mục 9.4, hậu kiểm + gọi lại có feedback + fallback.
- [x] M3: chuẩn hóa TTS, edge-tts (WordBoundary + retry), offline TTS, ElevenLabs adapter, subtitles SRT/ASS (≤2 dòng, ≤800px).
- [x] M4: ffmpeg runner + preflight, chart (mplfinance), cards (Pillow), DemoMotion, composer 2 giai đoạn, kiểm tra ffprobe, thumbnail, safe_zone_check.
- [x] Publishers: dry-run, Telegram, Facebook Reels, YouTube (OAuth), TikTok (nháp, is_aigc).
- [x] Orchestrator: lock, cancel, retry từ bước lỗi, manifest + checksum, job_events.
- [x] CLI: `python -m stockai preflight | run | render-sample | serve | db migrate | cleanup | youtube-login`.
- [x] **Chạy thật end-to-end**: RSS thật + Vietcap thật → final.mp4 1080×1920, 30fps, 81,9s, 6,3 MB, đạt ffprobe.
- [ ] Còn lại: API + WebSocket + bảo mật, UI 5 tab nối API, scheduler, app.py (pywebview), tests, README, báo cáo.

## 23/11/2026 — đợt 1
- [x] Bản demo giao diện chạy trong trình duyệt (`demo/index.html`).
- [x] Cài môi trường: FFmpeg 9.1, uv 0.13.9, Python 3.12, font Be Vietnam Pro.
- [x] M0/M1 lõi: config, layout, models, errors, secrets, DB, chỉ báo, RSS, provider thị trường.
