# StockAI Studio — Quy tắc cho AI agent

## Nguồn sự thật
- Đặc tả: docs/BLUEPRINT.md (v3.0). Nhật ký quyết định: docs/DECISIONS.md. Tiến độ: docs/PROGRESS.md.
- Thứ tự ưu tiên khi mâu thuẫn: Mục 3 > Mục 8 > Mục 10 > phần còn lại.

## Cách làm việc
- Làm đúng MỘT milestone mỗi phiên (BLUEPRINT Mục 15). Hết milestone thì dừng, báo cáo, chờ duyệt.
- Trước khi code phần có nhãn [KIỂM CHỨNG]: đọc tài liệu chính thức, ghi kết quả + link + ngày vào DECISIONS.md.
- Viết test trước cho hàm thuần. Sau mỗi thay đổi chạy: `uv run ruff check . && uv run python -m pytest -q`.
- Báo cáo cuối milestone gồm: file đã tạo/sửa, output lệnh nghiệm thu, rủi ro còn lại.

## Lệnh (máy này chặn file .exe do uv tạo → luôn dùng `python -m stockai`)
- Cài: `uv sync`
- Kiểm tra môi trường: `uv run python -m stockai preflight`
- Chạy pipeline offline: `uv run python -m stockai run --mode demo --offline --no-publish`
- Mở app: `uv run python app.py` (hoặc `--browser`)
- Test: `uv run python -m pytest -q` (test cần mạng/chậm: `-m network`)

## Ràng buộc cứng
- KHÔNG thêm vnstock/vnai. KHÔNG hardcode API key; bí mật chỉ qua stockai/secrets.py (keyring).
- Tọa độ khung hình chỉ định nghĩa trong stockai/layout.py.
- Các bước chỉ trao đổi dữ liệu qua model trong stockai/models.py.
- Mọi chuỗi hiển thị cho người dùng bằng tiếng Việt; text render phải chuẩn hóa NFC.
- Không đăng nội dung khi data_quality = SYNTHETIC; luôn gắn nhãn AI (R-LEGAL-1, R-PUB-1).
- FFmpeg: dùng `-/filter_complex <file>`, cwd = thư mục job, đường dẫn tương đối.
- Không tự bịa endpoint/tham số API: không chắc thì viết adapter + fixture + ghi [KIỂM CHỨNG].
