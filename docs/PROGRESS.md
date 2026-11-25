# PROGRESS — Nhật ký tiến độ

> Cập nhật sau mỗi phần việc. Mới nhất ở trên cùng.

## 26/11/2026 — đợt 6 (thiết kế lại + web demo + backend)
- [x] Web demo mới: trang giới thiệu (hero video 9:16 dựng thật bằng canvas, pipeline cuộn, bento, playground factcheck, bộ ước tính chi phí, FAQ) + Studio (sidebar thu gọn, KPI sparkline, stepper 5 bước, terminal lọc cấp độ, drawer chi tiết, lịch dạng tuần, bảng lệnh Ctrl K, phím tắt 1–5).
- [x] Deploy Cloudflare: `wrangler.jsonc`, `_headers` (CSP…), `404.html`, `robots.txt`, `sitemap.xml`, manifest, ảnh OG.
- [x] Giao diện app desktop dùng cùng design system; sparkline VN-Index.
- [x] Backend: publish lock (409), privacy TikTok theo lượt, chạy bù mọi lịch lỡ, TTS đọc lại an toàn, đóng file Telegram, 404 khi sửa job không tồn tại. +6 test hồi quy → 60 test đạt, ruff sạch.
- [x] Kiểm thử bằng trình duyệt thật (Edge headless qua CDP): landing desktop/mobile, Studio đủ 5 tab, app thật chạy offline ra final.mp4 78,5s — không lỗi console.

## 23/11/2026 — đợt 5 (M8 + phần dở)
- [x] Bản nháp Telegram riêng khi chờ duyệt (`telegram.draft_chat_id`, lỗi chỉ cảnh báo).
- [x] Hybrid avatar: head 7s + tail 8s khớp môi, giữa DemoMotion, concat → avatar.mp4 (+2 test).
- [x] M8: `stockai/desktop.py` (icon, khay pystray, 1 phiên, lối tắt, Startup), `launcher.pyw`, `CaiDat.bat`, CLI `install` / `autostart`.
- [x] Sửa: ffmpeg bị kill 0xC000013A khi app chạy không console → stdin=DEVNULL + CREATE_NO_WINDOW.
- [x] Kiểm chứng: mở từ lối tắt (pythonw, --tray) → job thật LIVE → final.mp4 74,1s; phiên thứ 2 tự thoát. ruff sạch, 54 test pass.

## 23/11/2026 — đợt 4 (hoàn thiện bản demo)
- [x] Chạy app thật, chụp UI, chạy job qua API (giọng edge-tts thật, 74,1s), duyệt dry-run 4 nền tảng.
- [x] Sửa: privacy riêng của TikTok (SELF_ONLY) làm vỡ bước đăng → ánh xạ về tập chuẩn + test hồi quy.
- [x] Sửa: UI nạp lại log khi mở trang giữa lúc job chạy; thẻ tin thêm "…" khi cắt tóm tắt.
- [x] README, CLAUDE.md, .env.example, MoStockAI.bat, BAO_CAO.md (tổng kết + hướng dẫn sử dụng).
- [ ] Chưa làm: M8 (đóng gói PyInstaller, khay hệ thống), Hybrid avatar nhiều đoạn, kiểm chứng thật các API trả phí (cần khóa).

## 23/11/2026 — đợt 3
- [x] M5: FastAPI đủ endpoint Mục 11, WebSocket, token + Origin, path traversal, UI 5 tab nối API.
- [x] M6: Scheduler (đồng bộ CRUD, chạy bù, retry, skip), luồng chờ duyệt → đăng.
- [x] Tests: 52 pass.

## 23/11/2026 — đợt 2
- [x] M2–M4, publishers, orchestrator, CLI. Chạy thật end-to-end ra final.mp4.

## 23/11/2026 — đợt 1
- [x] Demo HTML, cài môi trường (FFmpeg, uv, Python 3.12, font), M0/M1 lõi.
