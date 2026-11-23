# PROGRESS — Nhật ký tiến độ

> Cập nhật sau mỗi phần việc. Mới nhất ở trên cùng.

## 23/11/2026
- [x] Bản demo giao diện chạy trong trình duyệt (`demo/index.html`): 5 tab, chạy pipeline mô phỏng, xem trước 9:16.
- [x] Cài môi trường: FFmpeg 9.1 (đủ filter), uv 0.13.9, Python 3.12, font Be Vietnam Pro.
- [x] M0 (một phần): `pyproject.toml`, `config.py`, `layout.py`, `models.py`, `errors.py`, `secrets.py`, `db/schema.sql`, `migrate.py`, `repo.py`.
- [x] M1 (một phần): `analysis/indicators.py`, `analysis/ranking.py`, `providers/news/rss.py`, chuỗi provider thị trường (Synthetic, CSV, Cache, PublicVci, SSI). Đã chạy thật RSS 3 nguồn và Vietcap.
- [x] M2 (một phần): `analysis/factcheck.py`, `text/vi_normalize.py`, `text/captions.py`.
- [ ] Còn lại: LLM providers, TTS + phụ đề, render, orchestrator, API, UI, scheduler, publishers, CLI, tests.
