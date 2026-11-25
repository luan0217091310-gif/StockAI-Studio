# DECISIONS — Nhật ký quyết định & kết quả [KIỂM CHỨNG]

| Ngày | Mục | Quyết định / Kết quả kiểm chứng |
| :-- | :-- | :-- |
| 23/11/2026 | Môi trường | Cài bằng winget: FFmpeg 9.1 full build (Gyan) — có đủ `ass`, `zoompan`, `showwaves`, `xfade`, `loudnorm`, encoder `libx264`. `uv` 0.13.9, Python 3.12.16. |
| 23/11/2026 | Font | Be Vietnam Pro Regular/SemiBold/Bold + OFL.txt tải từ github.com/google/fonts (ofl/bevietnampro). |
| 23/11/2026 | RSS (9.1) | Chạy thật: CafeF 50 tin, Vietstock 20 tin, VnEconomy 50 tin → sau lọc + chống trùng + xếp hạng còn 20 tin. |
| 23/11/2026 | PublicVci (D7) [KIỂM CHỨNG] | `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart` body `{timeFrame:"ONE_DAY", symbols:["VNINDEX"], to, countBack}` → mảng `{t,o,h,l,c,v}`. Đã gọi thật được 60 phiên (phiên 23/11/2026 close 1.697,14). Endpoint KHÔNG chính thức, chỉ bật ở DEMO. |
| 23/11/2026 | SSI FastConnect [KIỂM CHỨNG] | Adapter viết theo tài liệu `fc-data.ssi.com.vn` (AccessToken, DailyIndex). CHƯA kiểm chứng do chưa có tài khoản SSI (D1 chưa chốt). |
| 23/11/2026 | Thư mục dữ liệu | Khi dev dùng `STOCKAI_DATA_DIR=./data` (đã có trong `.gitignore`). |
| 23/11/2026 | edge-tts 7.3.1 [KIỂM CHỨNG] | `boundary="WordBoundary"` hoạt động, trả mốc từng từ. Dịch vụ thỉnh thoảng trả `NoAudioReceived` ngẫu nhiên với cùng tham số → thêm retry 5 lần (backoff 1,5s·n); vẫn lỗi → fallback audio im lặng + mốc ước lượng, log WARN. |
| 23/11/2026 | Windows App Control | Máy chặn `.venv\Scripts\stockai.exe` (os error 4551) → dùng `uv run python -m stockai ...` (thêm `stockai/__main__.py`). |
| 23/11/2026 | FFmpeg 9.1 | Dùng cú pháp `-/filter_complex <file>` (thay `-filter_complex_script` đã deprecated). |
| 23/11/2026 | DemoMotion | Phóng to ×2 (2160px) thay vì ×4 trước `zoompan` để render nhanh hơn ~3 lần; vẫn mượt. |
| 23/11/2026 | B-roll | Chuỗi `chart → card1..n → chart …` lặp để mỗi đoạn 6–8s (Blueprint 9.7) thay vì kéo dài mỗi đoạn tới ~15s; luôn kết thúc bằng chart. |
| 23/11/2026 | Nhãn AI | Thêm input `ai_label.png` (trong suốt) overlay ngay sau B-roll để nhãn luôn nằm trên biểu đồ/thẻ tin (Mục 10.5). |
| 23/11/2026 | Factcheck | Whitelist từ 3 chữ in hoa không phải mã CK (TIN, SMA, RSI…). |
| 23/11/2026 | DB | `save_snapshot` dùng `ON CONFLICT DO UPDATE` thay `INSERT OR REPLACE` (tránh vỡ khóa ngoại job cũ). Thêm phụ thuộc `six` (mplfinance cần). |
| 23/11/2026 | safe_zone_check.png | Luôn xuất (chỉ 1 frame) để người dùng tự kiểm bố cục. |
| 23/11/2026 | Windows App Control (2) | Máy chặn `_multiprocessing.pyd` (chưa ký) của Python do uv tải → APScheduler import `ProcessPoolExecutor` bị vỡ. `stockai/__init__.py` thay bằng module rỗng nếu import lỗi (app không dùng multiprocessing). |
| 23/11/2026 | UI | Dùng CSS thuần + CSS variables (Blueprint cho phép thay Tailwind) → không cần tải gì, chạy offline. Font phục vụ từ `assets/fonts`. |
| 23/11/2026 | Token | Không nhúng token vào HTML; cửa sổ mở `/?t=token`, UI lưu sessionStorage rồi xóa khỏi URL. |

## 23/11/2026 — M8: không dùng PyInstaller
- Máy có Windows Application Control: `.venv\Scripts\pythonw.exe` (bản do uv tạo) bị chặn; `pythonw.exe` của Python gốc uv (`%APPDATA%\uv\python\cpython-3.12-*`) chạy được. Exe PyInstaller chưa ký sẽ bị chặn tương tự.
- Giải pháp: lối tắt → Python gốc `pythonw.exe` + `launcher.pyw` (site.addsitedir .venv). Khay bằng pystray (`run_detached`), 1 phiên qua `data/running.json`.
- Chạy không console thì ffmpeg con thoát mã 0xC000013A → luôn tạo với `stdin=DEVNULL`, `CREATE_NO_WINDOW`.

## 23/11/2026 — Hybrid avatar
- Chia audio: head 7s / mid / tail 8s (audio < 18s → khớp môi toàn bộ). Chi phí chỉ tính head+tail. Từng đoạn chuẩn hóa 1080×976/30fps rồi nối bằng concat filter qua `-/filter_complex` file.

## 26/11/2026 — Web demo v2, giao diện mới, sửa backend
- **Web demo** (`demo/`) viết lại: `index.html` (trang giới thiệu) + `app.html` (Studio). Logic nghiệp vụ tách vào `demo/assets/engine.js` (port từ Python: chỉ báo, xếp hạng tin, factcheck, template, cue phụ đề, layout 9:16) để cả 2 trang dùng chung. JS thuần, không build, chạy được cả qua `file://`. Bản cũ nằm trong lịch sử git.
- **Lỗi tìm được bằng phép thử 1.800 tổ hợp** (ngày × loại phiên × kiểu hook): template của bản web cũ ra 220–232 từ → hậu kiểm chặn, job FAILED. Đã rút gọn câu kịch bản + bước cắt bớt như `template_fallback.py` → 0/1.800 lỗi, 200–212 từ.
- **Deploy [KIỂM CHỨNG]**: thêm `wrangler.jsonc` (assets `./demo`, `not_found_handling: 404-page`) thay vì để Cloudflare tự đoán thư mục. `npx wrangler@4 deploy --dry-run` (wrangler 4.168.0, 26/11/2026) đọc đúng 20 file. `demo/_headers`: CSP chỉ `'self'` (style cho phép inline vì canvas/JS đặt style), `frame-ancestors 'none'`, `X-Frame-Options: DENY`, Referrer-Policy, Permissions-Policy; cache dài cho font.
- **Chuẩn web** tham khảo lộ trình andreasbm/web-skills (accessibility, performance, security, SEO): skip-link, landmark, `aria-live` cho log/toast, `role=dialog` cho drawer/bảng lệnh, `:focus-visible`, `prefers-reduced-motion`, script `defer`, JSON-LD SoftwareApplication, canonical, `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, ảnh OG 1200×630.
- **Thiết kế**: design system chung (emerald = thương hiệu/tăng, violet = AI). Bớt "mùi AI": gradient chữ chỉ ở hero, tiêu đề section 2 vế (vế sau màu xám), nhãn đánh số "01 / …", icon SVG thay ký tự ✓ ⏱ ∿ ▦ ◉ ⚙. Giao diện app thật (`ui/styles.css`) dùng cùng token, giữ nguyên class/ID nên `ui/app.js` gần như không đổi.
- **Backend**: (1) `Orchestrator.publish` có `publish_lock`; đang đăng hoặc job khác đang chạy → 409 `JOB_RUNNING` (chống bấm Duyệt & Đăng 2 lần). (2) Bỏ thuộc tính dùng chung `_tiktok_privacy`, truyền privacy theo từng lần đăng. (3) Chạy bù **mọi** lịch bị lỡ, lần lượt theo giờ (trước đây chỉ lịch đầu tiên, lịch sau bị bỏ không cảnh báo). (4) Đọc lại TTS khi audio ngoài 45–95s mà lỗi → giữ audio trước, không làm hỏng job. (5) Telegram đóng file video/thumbnail bằng `ExitStack`. (6) `PUT /api/jobs/{id}` job không tồn tại → 404. (7) `/api/status` trả `market.spark` (30 giá đóng cửa) cho sparkline.
- Máy này: Application Control đôi khi chặn `_sqlite3.pyd` ở lần chạy pytest đầu tiên; chạy lại là qua (không phải lỗi code).
- `demo/assets/engine.js` chứa bản sao tọa độ `layout.py` (hằng `L`) vì trình duyệt không đọc được Python. Nguồn sự thật vẫn là `stockai/layout.py`; đổi tọa độ thì phải đổi cả hai.
