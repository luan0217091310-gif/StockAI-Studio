# PROGRESS — Nhật ký tiến độ

> Cập nhật sau mỗi phần việc. Mới nhất ở trên cùng.

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
