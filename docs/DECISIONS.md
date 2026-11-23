# DECISIONS — Nhật ký quyết định & kết quả [KIỂM CHỨNG]

| Ngày | Mục | Quyết định / Kết quả kiểm chứng |
| :-- | :-- | :-- |
| 23/11/2026 | Môi trường | Cài bằng winget: FFmpeg 9.1 full build (Gyan) — có đủ `ass`, `zoompan`, `showwaves`, `xfade`, `loudnorm`, encoder `libx264`. `uv` 0.13.9, Python 3.12.16. |
| 23/11/2026 | Font | Be Vietnam Pro Regular/SemiBold/Bold + OFL.txt tải từ github.com/google/fonts (ofl/bevietnampro). |
| 23/11/2026 | RSS (9.1) | Chạy thật: CafeF 50 tin, Vietstock 20 tin, VnEconomy 50 tin → sau lọc + chống trùng + xếp hạng còn 20 tin. |
| 23/11/2026 | PublicVci (D7) [KIỂM CHỨNG] | `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart` body `{timeFrame:"ONE_DAY", symbols:["VNINDEX"], to, countBack}` → mảng `{t,o,h,l,c,v}`. Đã gọi thật được 60 phiên (phiên 23/11/2026 close 1.697,14). Endpoint KHÔNG chính thức, chỉ bật ở DEMO. |
| 23/11/2026 | SSI FastConnect [KIỂM CHỨNG] | Adapter viết theo tài liệu `fc-data.ssi.com.vn` (AccessToken, DailyIndex). CHƯA kiểm chứng do chưa có tài khoản SSI (D1 chưa chốt). |
| 23/11/2026 | Thư mục dữ liệu | Khi dev dùng `STOCKAI_DATA_DIR=./data` (đã có trong `.gitignore`). |
