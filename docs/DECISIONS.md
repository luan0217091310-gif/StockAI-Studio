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
