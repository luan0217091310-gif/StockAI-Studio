# STOCKAI STUDIO — MASTER BLUEPRINT v3.0

> **Bản đặc tả dành cho AI lập trình (Claude Code / Cursor / Windsurf / Codex)**
> Phiên bản: **3.0** · Cập nhật: **23/11/2026** · Thay thế bản 2.0
> Nền tảng: Desktop **Windows 10/11** & **macOS 13+** · Ngôn ngữ chính: **Python 3.12**
> Giao diện: 100% tiếng Việt

---

## 0. CÁCH DÙNG TÀI LIỆU NÀY

### 0.1. Dành cho bạn (chủ dự án)
1. Tạo repo mới, đặt file này vào `docs/BLUEPRINT.md`.
2. Tạo file `CLAUDE.md` (hoặc `AGENTS.md` nếu dùng Cursor/Codex) ở thư mục gốc, copy nội dung **Phụ lục A**.
3. Mở AI agent, dán **Prompt khởi động** ở **Phụ lục B**.
4. Mỗi phiên làm việc với agent chỉ làm **một milestone** (Mục 15). Xem kết quả, chạy thử, rồi mới cho sang milestone tiếp theo.
5. Trước khi lên PRODUCTION, chốt các quyết định ở **Mục 17**.

### 0.2. Dành cho AI agent
* **PHẢI** = bắt buộc. **NÊN** = mặc định, chỉ bỏ khi có lý do ghi vào `docs/DECISIONS.md`. **CÓ THỂ** = tùy chọn.
* Nhãn **`[KIỂM CHỨNG]`** = thông tin thay đổi nhanh (tên model, endpoint, giá, giới hạn). Trước khi code phần đó, PHẢI đọc lại tài liệu chính thức (link ở Phụ lục C) và ghi kết quả vào `docs/DECISIONS.md`.
* Mã yêu cầu dạng `R-XXX-n` (ví dụ `R-LEGAL-1`) là ràng buộc cứng; khi viết code liên quan hãy ghi mã đó trong docstring/test.
* Khi các mục mâu thuẫn nhau, thứ tự ưu tiên: **Mục 3 (ràng buộc) > Mục 8 (hợp đồng dữ liệu) > Mục 10 (bố cục) > phần còn lại**.
* Không tự bịa số liệu, endpoint, tham số API. Nếu không chắc: viết adapter có test bằng fixture và đánh dấu `[KIỂM CHỨNG]` trong DECISIONS.

---

## 1. TỔNG QUAN SẢN PHẨM

### 1.1. Giá trị cốt lõi
Người làm nội dung chứng khoán mất 3–4 giờ/ngày để đọc tin, vẽ biểu đồ, viết kịch bản, quay, dựng và đăng. **StockAI Studio** chạy trên laptop và làm thay phần lớn công việc đó:

1. Người dùng tải lên **1 ảnh chân dung của chính mình** (hoặc của người đã đồng ý), chọn giọng đọc tiếng Việt.
2. Đặt lịch cố định, ví dụ `07:30` (bản tin trước phiên) và `15:30` (tổng kết sau phiên), thứ 2–6.
3. Hệ thống chạy 5 bước: **Thu thập → AI biên tập → Giọng & Avatar → Dựng video 9:16 → Xuất bản**, rồi **chờ người dùng duyệt** (mặc định) trước khi đăng lên Telegram / Facebook Reels / YouTube Shorts / TikTok.

### 1.2. Phạm vi KHÔNG làm (non-goals)
* Không đặt lệnh, không kết nối tài khoản giao dịch.
* Không khuyến nghị mua/bán/nắm giữ mã cụ thể, không cam kết lợi nhuận.
* Không cào toàn văn bài báo; chỉ dùng tiêu đề + tóm tắt RSS + đường link, và ghi nguồn.
* Không đăng nội dung dựa trên **dữ liệu minh họa** (giả lập) lên mạng xã hội.
* Không dùng ảnh/giọng của người khác khi chưa có sự đồng ý.

### 1.3. Hai chế độ vận hành

| Thành phần | **DEMO** (mặc định khi mới cài, 0 đồng) | **PRODUCTION** (vận hành thật) |
| :--- | :--- | :--- |
| Dữ liệu thị trường | Nguồn công khai không cần khóa (thử nghiệm) → cache SQLite → dữ liệu minh họa có gắn nhãn | SSI FastConnect Data (API chính thức, cần tài khoản SSI) hoặc nguồn có giấy phép |
| Tin tức | RSS thật (CafeF, Vietstock, VnEconomy) | RSS thật |
| LLM | Gemini free tier (`gemini-3.8-flash`) → fallback bộ sinh kịch bản mẫu | Gemini trả phí hoặc API tương thích OpenAI |
| Giọng đọc | `edge-tts` (giọng Neural tiếng Việt) | ElevenLabs / Vbee / FPT.AI (tùy chọn) |
| Avatar | `DemoMotion`: ảnh thật + hiệu ứng chuyển động nhẹ + sóng âm (không khớp môi) | Talking-head API: fal.ai (Kling AI Avatar v2 / OmniHuman) hoặc HeyGen API |
| Đăng bài | Dry-run (lưu bản xem trước) + Telegram thật | Telegram, FB Reels, YouTube Shorts, TikTok (dạng nháp/riêng tư cho tới khi app được duyệt) |

---

## 2. NHỮNG THAY ĐỔI SO VỚI BẢN 2.0 (VÀ LÝ DO)

| # | Bản 2.0 | Bản 3.0 | Lý do |
| :-- | :--- | :--- | :--- |
| 1 | Phụ thuộc `vnstock` | **Bỏ hoàn toàn**; thay bằng lớp `MarketDataProvider` nhiều nguồn | Gói `vnstock` bị PyPI cách ly (quarantine) từ 24/09/2026, không cài được qua pip; giấy phép không phải mã nguồn mở |
| 2 | Gemini 2.5 Pro/Flash | Gemini 3.x, **tên model là cấu hình** | Google khuyến nghị dự án mới dùng 3.5 Flash-Lite hoặc 3.8 Flash; 2.5 chỉ còn cho người dùng cũ |
| 3 | `edge-tts` mặc định có WordBoundary | PHẢI truyền `boundary="WordBoundary"` `[KIỂM CHỨNG]` | Từ bản 7.x mặc định đổi sang SentenceBoundary → phụ đề lệch nếu không chỉnh |
| 4 | `apscheduler>=3.10.4` | `apscheduler>=3.11,<4` | 4.0 vẫn là bản pre-release, API thay đổi liên tục |
| 5 | Ticker ở đáy (y 1820–1920), phụ đề ở giữa mặt MC | **Bố cục v3 theo safe-zone** (Mục 10) | Đáy ~480px bị caption/nút của TikTok/Reels che; phụ đề y 1200–1360 đè lên mặt |
| 6 | Mục tiêu "chống bóp tương tác" | Bỏ; thay bằng **chống nội dung rập khuôn** + duyệt bởi người | Nền tảng nhắm vào nội dung hàng loạt, lặp lại; không có kỹ thuật "chống shadowban" đáng tin |
| 7 | Tự đăng TikTok 100% | Mặc định **gửi nháp / SELF_ONLY**, bật `is_aigc` | App TikTok chưa qua audit chỉ đăng được ở chế độ riêng tư |
| 8 | YouTube quota cũ | Cập nhật quota mới + `containsSyntheticMedia=true` | Google đã đổi quota `videos.insert`; có trường khai báo nội dung tổng hợp |
| 9 | Caption Telegram = toàn bài | Video kèm caption ngắn ≤1024 ký tự + tin nhắn riêng chứa bài đầy đủ | Giới hạn caption của Bot API |
| 10 | — | Nhãn "Nội dung có sử dụng AI" hiển thị + metadata | Luật Trí tuệ nhân tạo VN (134/2025/QH15) hiệu lực từ 01/03/2026 |
| 11 | API key lưu thô trong SQLite | Lưu trong **OS keyring** (Windows Credential Manager / macOS Keychain) | Bảo mật |
| 12 | API localhost không xác thực | Token phiên + kiểm tra `Origin` | Trang web bất kỳ trong trình duyệt có thể gọi `127.0.0.1` |
| 13 | Cửa sổ tin cố định 48h | `từ đầu ngày giao dịch trước` (tối thiểu 48h, tối đa 96h) | Sáng thứ Hai, 48h chỉ phủ Thứ Bảy–Chủ Nhật |
| 14 | Dữ liệu giả lập dự phòng "im lặng" | Gắn nhãn `DỮ LIỆU MINH HỌA` + **chặn đăng** | Tránh phát tán số liệu sai |
| 15 | Pydantic `min_items/max_items` | `min_length/max_length` | Cú pháp Pydantic v2 |
| 16 | RSI không nói rõ cách làm mượt | RSI Wilder (`ewm(alpha=1/14)`) | Khớp với TradingView/AmiBroker |
| 17 | "LocalGPU: MuseTalk/LivePortrait từ 1 ảnh" | Đưa xuống thử nghiệm (M9) | MuseTalk cần video nguồn; LivePortrait cần video điều khiển, không nhận audio trực tiếp |
| 18 | Dữ liệu lưu cạnh mã nguồn | Thư mục dữ liệu người dùng (`platformdirs`) | App cài trong Program Files / Applications không ghi được |
| 19 | Prompt "viết toàn bộ một lần" | Milestone nhỏ, mỗi bước có test và lệnh nghiệm thu | Giảm lỗi dây chuyền, dễ kiểm soát |
| 20 | Chống ảo giác chỉ bằng prompt | Thêm **kiểm tra số liệu bằng code** (`factcheck.py`) | Prompt không đảm bảo |
| 21 | Preflight chỉ kiểm tra có `ffmpeg` | Kiểm tra cả filter `ass`, `zoompan`, `showwaves`, `xfade` và encoder `libx264` | Nhiều bản FFmpeg thiếu libass |

---

## 3. RÀNG BUỘC THỰC TẾ (THÁNG 11/2026) — PHẢI TUÂN THỦ

### 3.1. Pháp lý Việt Nam
* **Luật Trí tuệ nhân tạo số 134/2025/QH15** (hiệu lực 01/03/2026): nội dung AI mô phỏng ngoại hình/giọng nói người thật phải có nhãn nhìn thấy được; audio/ảnh/video do AI tạo phải được đánh dấu ở dạng máy đọc được theo quy định của Chính phủ. `[KIỂM CHỨNG]` nghị định hướng dẫn về định dạng đánh dấu.
  * **R-LEGAL-1:** Mọi video xuất ra PHẢI có nhãn AI hiển thị suốt video (Mục 10) và câu khai báo trong bài đăng: *"Video có sử dụng AI (MC ảo, giọng đọc tổng hợp)."*
  * **R-LEGAL-2:** File MP4 PHẢI có metadata: `-metadata comment="AI-generated content: StockAI Studio; synthetic presenter & voice"`. NÊN bổ sung C2PA ở giai đoạn sau.
  * **R-LEGAL-3:** Trước khi dùng ảnh chân dung cho bất kỳ provider nào, PHẢI có bản ghi đồng ý trong bảng `consents` (người dùng tick: "Tôi là người trong ảnh hoặc đã được người trong ảnh đồng ý").
* **Chứng khoán:** tư vấn đầu tư là hoạt động có điều kiện. **R-LEGAL-4:** Kịch bản và bài đăng không khuyến nghị mua/bán mã cụ thể, luôn kết thúc bằng câu miễn trừ trách nhiệm. Khi thương mại hóa, chủ dự án nên hỏi ý kiến luật sư.

### 3.2. Chính sách nền tảng
* **YouTube:**
  * Chính sách kiếm tiền xếp vào "nội dung không chân thực" các video rập khuôn/lặp lại và **nhân vật AI nói về chủ đề nhạy cảm như tài chính** → kênh dùng MC ảo nói về chứng khoán có rủi ro **không được bật kiếm tiền**. Xem quyết định D2 (Mục 17).
  * `videos.insert` hiện tốn 1 đơn vị trong nhóm quota riêng "Video Uploads", giới hạn 100 lượt/ngày. `[KIỂM CHỨNG]`
  * PHẢI đặt `status.containsSyntheticMedia = true`.
  * Nếu OAuth consent screen ở trạng thái "Testing", refresh token sẽ hết hạn sau khoảng 7 ngày → app phải báo người dùng đăng nhập lại. `[KIỂM CHỨNG]`
* **TikTok (Content Posting API):**
  * App chưa qua audit: mọi bài đăng bị giới hạn ở chế độ riêng tư, tối đa 5 người dùng đăng trong 24h, tài khoản phải để private.
  * Có cờ `is_aigc` để gắn nhãn AI → PHẢI bật.
  * Hướng dẫn của TikTok yêu cầu app cho người dùng tự nhập/chọn metadata và chỉ gửi nội dung sau khi người dùng đồng ý rõ ràng → luồng **duyệt trước khi đăng** là bắt buộc với TikTok.
* **Facebook Reels:** quy trình 3 bước (khởi tạo phiên → upload lên `rupload.facebook.com` → publish); giới hạn **30 bài đăng qua API trong 24 giờ** (cửa sổ trượt).
* **Telegram Bot API:** `sendVideo` tối đa **50 MB**; caption 0–1024 ký tự; tin nhắn thường tối đa 4096 ký tự.

### 3.3. Thư viện & dịch vụ
* **vnstock:** không dùng (bị PyPI cách ly; một số dự án đã gỡ bỏ sau khi đọc mã nguồn và thấy gửi telemetry định kỳ). Nếu sau này PyPI gỡ cách ly và bạn chấp nhận giấy phép, CÓ THỂ viết adapter riêng `VnstockProvider`, cô lập import.
* **Gemini API:** model stable hiện tại gồm `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`. Free tier: giới hạn theo project (xem trong AI Studio), dữ liệu gửi lên có thể được Google dùng để cải thiện sản phẩm → không gửi dữ liệu cá nhân. `[KIỂM CHỨNG]`
* **edge-tts:** là client không chính thức của dịch vụ đọc của Microsoft Edge, có thể ngừng chạy khi Microsoft đổi giao thức → PHẢI có thông báo lỗi rõ ràng và cho phép chọn TTS khác.
* **APScheduler:** dùng 3.11.x (stable).
* **pywebview:** dùng 6.x.

---

## 4. KIẾN TRÚC HỆ THỐNG

### 4.1. Sơ đồ

```text
+------------------------------------------------------------------------------+
|                  CỬA SỔ DESKTOP (pywebview — main thread)                    |
|  [Bảng điều khiển] [Nhân vật & Giọng] [Kho nội dung] [Lịch tự động] [Cài đặt]|
|          |  REST (JSON, header X-App-Token)        |  WebSocket /ws/events   |
+----------|-----------------------------------------|-------------------------+
           v                                         v
+------------------------------------------------------------------------------+
|              BACKEND CỤC BỘ (FastAPI + Uvicorn, thread nền, 127.0.0.1)       |
|  server/api.py  ·  server/ws.py (Event Bus)  ·  server/security.py           |
|  scheduler.py (APScheduler 3.x, Asia/Ho_Chi_Minh)                            |
|                                   |                                          |
|  +--------------------------------v---------------------------------------+  |
|  |                PIPELINE ORCHESTRATOR (pipeline/orchestrator.py)        |  |
|  |  B1 Thu thập ─> B2 AI biên tập ─> B3 Giọng & Avatar ─> B4 Dựng video   |  |
|  |  ─> B5 Xuất bản (hoặc WAITING_APPROVAL)                                |  |
|  |  Mỗi bước gọi qua interface provider (Mục 8) — dễ thay công nghệ       |  |
|  +-----------------------------------------------------------------------+   |
+---------------|--------------------------------------------|-----------------+
                v                                            v
+------------------------------------+   +-------------------------------------+
| DỮ LIỆU CỤC BỘ (platformdirs)      |   | DỊCH VỤ NGOÀI                       |
| stock_ai.db (SQLite, WAL)          |   | RSS: CafeF, Vietstock, VnEconomy    |
| user_assets/ (avatar, logo, bgm)   |   | Thị trường: SSI FC Data / công khai |
| outputs/YYYY-MM-DD/<job_id>/       |   | LLM: Gemini / OpenAI-compatible     |
| temp/  ·  logs/                    |   | TTS: edge-tts / ElevenLabs          |
| OS keyring: API keys, OAuth tokens |   | Avatar: fal.ai / HeyGen             |
+------------------------------------+   | Đăng: Telegram, Meta, YouTube, TikTok|
                                         +-------------------------------------+
```

### 4.2. Mô hình chạy (concurrency)
* **R-RUN-1:** pywebview PHẢI chạy ở main thread (bắt buộc trên macOS). Uvicorn chạy trong thread nền với event loop riêng.
* **R-RUN-2:** Pipeline chạy là một `asyncio.Task` trong loop của server. Scheduler khởi động trong `lifespan` của FastAPI để dùng chung event loop. Tác vụ chặn (matplotlib, Pillow) chạy qua `asyncio.to_thread`. FFmpeg chạy qua `asyncio.create_subprocess_exec` (có timeout, hủy được).
* **R-RUN-3:** Matplotlib dùng backend `Agg`. Chỉ một job render tại một thời điểm.
* **R-RUN-4:** Job lock = `asyncio.Lock` + kiểm tra DB (không có job `RUNNING`/`PUBLISHING`). Khi app khởi động, job còn `RUNNING` từ lần trước → chuyển `FAILED` với `error_code="INTERRUPTED"`.
* **R-RUN-5:** Mọi bước phát sự kiện qua Event Bus → WebSocket + ghi bảng `job_events`.
* **R-RUN-6:** Mỗi bước ghi artifact vào thư mục job và cập nhật `manifest.json`; `retry` bắt đầu lại từ bước lỗi, bỏ qua bước đã có artifact hợp lệ.

### 4.3. Bảo mật cục bộ
* **R-SEC-1:** Server chỉ bind `127.0.0.1`. Cổng mặc định `8765`; nếu bận thì chọn cổng trống và truyền vào cửa sổ.
* **R-SEC-2:** Mỗi lần mở app tạo `app_token` ngẫu nhiên (32 byte). Cửa sổ mở `http://127.0.0.1:{port}/?t={token}`; UI gửi header `X-App-Token` cho REST và query `?token=` cho WebSocket. Thiếu/sai → 401. Request có `Origin` khác `http://127.0.0.1:{port}` → 403. Không bật CORS.
* **R-SEC-3:** API key/token lưu bằng thư viện `keyring` (service `StockAI Studio`). Bảng `settings` chỉ lưu `is_secret=1` và `value=NULL`. API trả về UI dạng che: `AIza••••••1234`.
* **R-SEC-4:** Endpoint phục vụ file chỉ cho phép đường dẫn nằm trong thư mục dữ liệu (chống path traversal).
* **R-SEC-5:** Log và `response_payload` PHẢI che token (regex cho `bot\d+:[\w-]+`, `AIza[\w-]+`, `Bearer \S+`, `access_token=\S+`).

### 4.4. Thư mục dữ liệu
* Mặc định: `platformdirs.user_data_dir("StockAI Studio", "StockAI")`.
* Ghi đè bằng biến môi trường `STOCKAI_DATA_DIR` (khi dev dùng `./data`).
* Cấu trúc: `stock_ai.db`, `user_assets/`, `outputs/YYYY-MM-DD/<job_id>/`, `temp/`, `logs/`.

---

## 5. CÔNG NGHỆ & PHIÊN BẢN

Quản lý môi trường bằng **`uv`** (`pyproject.toml` + `uv.lock`). Python **3.12** (3.13 được nếu mọi wheel có sẵn).

| Gói | Ràng buộc | Dùng cho |
| :--- | :--- | :--- |
| `fastapi` | `>=0.115` | REST + WebSocket |
| `uvicorn[standard]` | `>=0.30` | ASGI server |
| `pydantic` / `pydantic-settings` | `>=2.8` / `>=2.4` | Hợp đồng dữ liệu, cấu hình |
| `python-multipart` | `>=0.0.9` | Upload file |
| `httpx` | `>=0.27` | HTTP client async |
| `tenacity` | `>=9` | Retry |
| `feedparser` | `>=6.0.11` | RSS |
| `beautifulsoup4` | `>=4.12` | Làm sạch HTML |
| `pandas`, `numpy` | `>=2.2`, `>=1.26` | Chỉ báo kỹ thuật |
| `matplotlib`, `mplfinance` | `>=3.9`, `>=0.12.10b0` | Biểu đồ nến |
| `Pillow` | `>=10.4` | Thẻ tin, dải ticker, ảnh nền |
| `edge-tts` | `>=7.3` | TTS miễn phí |
| `google-genai` | mới nhất `[KIỂM CHỨNG]` | Gemini SDK |
| `apscheduler` | `>=3.11,<4` | Lịch chạy |
| `pywebview` | `>=6.1` | Cửa sổ desktop |
| `keyring` | `>=25` | Lưu bí mật |
| `platformdirs` | `>=4` | Thư mục dữ liệu |
| `typer` | `>=0.12` | CLI |
| Dev: `pytest`, `pytest-asyncio`, `ruff` | — | Test, lint |
| Tùy chọn M7: `google-api-python-client`, `google-auth-oauthlib`, `fal-client` | — | YouTube, fal.ai |
| Tùy chọn: `opencv-python-headless` | — | Nhận diện khuôn mặt để crop |

**Không dùng:** `vnstock`, `vnai`, `moviepy` (chậm, khó kiểm soát), Tailwind tải qua CDN lúc chạy (app phải mở được khi mất mạng).

**FFmpeg:** dùng bản cài trên máy (Windows: `winget install Gyan.FFmpeg`; macOS: `brew install ffmpeg`). Settings cho phép chọn đường dẫn `ffmpeg`/`ffprobe` thủ công.

**Font:** đóng gói **Be Vietnam Pro** (Regular, SemiBold, Bold; giấy phép OFL) trong `assets/fonts/`. Mọi text PHẢI chuẩn hóa Unicode **NFC** trước khi render.

---

## 6. CẤU TRÚC THƯ MỤC

```text
stockai-studio/
├── pyproject.toml                 # deps, [project.scripts] stockai = "stockai.cli:app"
├── uv.lock
├── README.md                      # cài FFmpeg, uv sync, chạy app
├── CLAUDE.md                      # quy tắc cho AI agent (Phụ lục A)
├── .env.example                   # chỉ biến không bí mật (STOCKAI_DATA_DIR, LOG_LEVEL)
├── .gitignore                     # data/, .env, *.db, outputs/, temp/
├── docs/
│   ├── BLUEPRINT.md               # file này
│   └── DECISIONS.md               # nhật ký quyết định + kết quả [KIỂM CHỨNG]
├── app.py                         # entry GUI: khởi động server thread + pywebview (fallback trình duyệt)
├── stockai/
│   ├── __init__.py
│   ├── config.py                  # Settings, đường dẫn, hằng số
│   ├── layout.py                  # TỌA ĐỘ KHUNG HÌNH — nguồn sự thật duy nhất (Mục 10)
│   ├── models.py                  # Pydantic contracts (Mục 8)
│   ├── errors.py                  # TransientError, ConfigError, ProviderError, ...
│   ├── secrets.py                 # wrapper keyring
│   ├── cli.py                     # preflight | run [--mode] [--step] [--offline] [--no-publish] | render-sample | serve | db migrate
│   ├── db/
│   │   ├── schema.sql
│   │   ├── migrate.py             # schema_version, migration tuần tự
│   │   └── repo.py                # hàm CRUD
│   ├── server/
│   │   ├── api.py                 # FastAPI app + routers
│   │   ├── ws.py                  # Event Bus → WebSocket
│   │   └── security.py            # token, kiểm tra Origin
│   ├── pipeline/
│   │   ├── orchestrator.py        # 5 bước, lock, cancel, resume
│   │   └── events.py              # schema sự kiện
│   ├── providers/
│   │   ├── market/   base.py ssi_fc.py public_vci.py csv_import.py cache.py synthetic.py
│   │   ├── news/     rss.py
│   │   ├── llm/      base.py gemini.py openai_compat.py template_fallback.py
│   │   ├── tts/      base.py edge.py elevenlabs.py
│   │   ├── avatar/   base.py demo_motion.py fal.py heygen.py
│   │   └── publish/  base.py dry_run.py telegram.py facebook.py youtube.py tiktok.py
│   ├── analysis/
│   │   ├── indicators.py          # SMA20, RSI14 Wilder, hỗ trợ/kháng cự
│   │   ├── ranking.py             # chấm điểm tin nổi bật
│   │   └── factcheck.py           # kiểm tra số liệu trong kịch bản
│   ├── text/
│   │   ├── vi_normalize.py        # chuẩn hóa ký hiệu cho TTS
│   │   └── captions.py            # bộ dựng caption theo từng nền tảng
│   ├── render/
│   │   ├── ffmpeg.py              # chạy ffmpeg/ffprobe, preflight
│   │   ├── chart.py               # biểu đồ 1080x660
│   │   ├── cards.py               # thẻ tin, dải ticker, ảnh nền, nhãn
│   │   ├── subtitles.py           # word timings → cues → SRT + ASS
│   │   └── composer.py            # dựng 2 giai đoạn
│   └── scheduler.py
├── ui/
│   ├── index.html
│   ├── app.js                     # ES modules, không cần build
│   ├── styles.css
│   └── vendor/                    # Tailwind v4 browser build tải về sẵn (chạy offline)
├── assets/
│   └── fonts/                     # BeVietnamPro-*.ttf + OFL.txt
└── tests/
    ├── fixtures/                  # RSS tự tạo, OHLCV CSV, JSON LLM mẫu, audio 8s
    └── test_*.py
```

---

## 7. CƠ SỞ DỮ LIỆU (SQLite)

File `stock_ai.db` trong thư mục dữ liệu. `migrate.py` chạy khi khởi động, ghi `schema_version`.

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);

-- 1. Cấu hình (bí mật nằm trong OS keyring, ở đây chỉ đánh dấu)
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,                         -- NULL khi is_secret = 1
    is_secret   INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2. Tài nguyên người dùng
CREATE TABLE IF NOT EXISTS assets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT NOT NULL CHECK (kind IN ('avatar','logo','bgm')),
    path           TEXT NOT NULL,
    sha256         TEXT NOT NULL,
    width          INTEGER,
    height         INTEGER,
    duration_s     REAL,
    is_active      INTEGER NOT NULL DEFAULT 1,
    is_placeholder INTEGER NOT NULL DEFAULT 0,  -- ảnh mẫu do app tự tạo
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 3. Bản ghi đồng ý sử dụng chân dung (R-LEGAL-3)
CREATE TABLE IF NOT EXISTS consents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id      INTEGER NOT NULL REFERENCES assets(id),
    subject_name  TEXT NOT NULL,
    relation      TEXT NOT NULL CHECK (relation IN ('SELF','AUTHORIZED')),
    statement     TEXT NOT NULL,                -- nguyên văn câu cam kết đã tick
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 4. Tin tức
CREATE TABLE IF NOT EXISTS news_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    source        TEXT NOT NULL,                -- CafeF | Vietstock | VnEconomy
    url           TEXT NOT NULL UNIQUE,
    content_hash  TEXT NOT NULL UNIQUE,         -- SHA-256 tiêu đề đã chuẩn hóa
    summary       TEXT,                         -- ≤ 300 ký tự, không HTML
    published_at  TEXT NOT NULL,                -- ISO 8601 có múi giờ
    fetched_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_items(published_at);

-- 5. Ảnh chụp thị trường (CHỈ lưu dữ liệu thật; không bao giờ lưu SYNTHETIC)
CREATE TABLE IF NOT EXISTS market_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol              TEXT NOT NULL DEFAULT 'VNINDEX',
    session_date        TEXT NOT NULL,          -- YYYY-MM-DD
    close               REAL NOT NULL,
    change              REAL,
    change_pct          REAL,
    volume              REAL,
    value_bn_vnd        REAL,                   -- tỷ VNĐ
    foreign_net_bn_vnd  REAL,                   -- NULL nếu nguồn không có
    sma20               REAL,
    rsi14               REAL,
    support20           REAL,
    resistance20        REAL,
    bars_json           TEXT NOT NULL,          -- ≥ 60 phiên OHLCV để vẽ lại/fallback
    top_movers_json     TEXT,
    source              TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (symbol, session_date, source)
);

-- 6. Lịch chạy
CREATE TABLE IF NOT EXISTS schedules (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    name                   TEXT NOT NULL,
    session_type           TEXT NOT NULL CHECK (session_type IN ('PRE_MARKET','POST_MARKET')),
    cron_hour              INTEGER NOT NULL CHECK (cron_hour BETWEEN 0 AND 23),
    cron_minute            INTEGER NOT NULL CHECK (cron_minute BETWEEN 0 AND 59),
    days_of_week           TEXT NOT NULL DEFAULT 'mon-fri',
    target_platforms_json  TEXT NOT NULL DEFAULT '["telegram"]',
    require_approval       INTEGER NOT NULL DEFAULT 1,
    is_active              INTEGER NOT NULL DEFAULT 1,
    last_run_at            TEXT,
    last_job_id            TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 7. Phiên tạo nội dung
CREATE TABLE IF NOT EXISTS content_jobs (
    id                  TEXT PRIMARY KEY,       -- UUID4
    run_date            TEXT NOT NULL,          -- YYYY-MM-DD theo giờ VN
    session_type        TEXT NOT NULL CHECK (session_type IN ('PRE_MARKET','POST_MARKET','ADHOC')),
    trigger             TEXT NOT NULL CHECK (trigger IN ('MANUAL','SCHEDULE','CATCHUP','RETRY')),
    schedule_id         INTEGER REFERENCES schedules(id),
    mode                TEXT NOT NULL CHECK (mode IN ('DEMO','PRODUCTION')),
    status              TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN
                          ('PENDING','RUNNING','WAITING_APPROVAL','PUBLISHING',
                           'COMPLETED','FAILED','CANCELLED','SKIPPED')),
    current_step        INTEGER NOT NULL DEFAULT 0,   -- 0..5
    progress_pct        INTEGER NOT NULL DEFAULT 0,
    data_quality        TEXT CHECK (data_quality IN ('LIVE','CACHED','SYNTHETIC')),
    market_snapshot_id  INTEGER REFERENCES market_snapshots(id),
    news_ids_json       TEXT,                   -- danh sách id tin đưa vào LLM (theo thứ tự)
    llm_provider        TEXT,
    llm_model           TEXT,
    factcheck_passed    INTEGER,
    script_json         TEXT,                   -- toàn bộ ScriptOutput
    video_title         TEXT,                   -- bản người dùng đã sửa (nếu có)
    social_post_text    TEXT,
    avatar_provider     TEXT,
    avatar_has_lipsync  INTEGER,
    est_cost_usd        REAL,
    artifacts_dir       TEXT,
    final_video_path    TEXT,
    thumbnail_path      TEXT,
    duration_s          REAL,
    ai_label_applied    INTEGER NOT NULL DEFAULT 0,
    error_code          TEXT,
    error_message       TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    started_at          TEXT,
    completed_at        TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_date ON content_jobs(run_date);

-- 8. Nhật ký sự kiện của job (để xem lại log sau khi đóng app)
CREATE TABLE IF NOT EXISTS job_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     TEXT NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
    ts         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    step       INTEGER,
    level      TEXT NOT NULL CHECK (level IN ('DEBUG','INFO','SUCCESS','WARN','ERROR')),
    message    TEXT NOT NULL,
    data_json  TEXT
);

-- 9. Lịch sử đăng
CREATE TABLE IF NOT EXISTS publish_logs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id            TEXT NOT NULL REFERENCES content_jobs(id),
    platform          TEXT NOT NULL CHECK (platform IN ('telegram','facebook','youtube','tiktok')),
    status            TEXT NOT NULL CHECK (status IN ('PENDING','SUCCESS','FAILED','DRY_RUN','SKIPPED')),
    privacy_level     TEXT,
    attempt           INTEGER NOT NULL DEFAULT 1,
    remote_post_id    TEXT,
    remote_post_url   TEXT,
    error_message     TEXT,
    response_payload  TEXT,                     -- đã che token (R-SEC-5)
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Chống đăng trùng: mỗi job chỉ có 1 bản SUCCESS cho mỗi nền tảng
CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_success
    ON publish_logs(job_id, platform) WHERE status = 'SUCCESS';
```

**Khóa cấu hình chính** (`settings.key`): `mode`, `market.symbol` (mặc định `VNINDEX`), `market.providers_order`, `llm.provider`, `llm.model` (`gemini-3.8-flash`), `llm.fallback_model` (`gemini-3.5-flash-lite`), `tts.provider`, `tts.voice`, `tts.rate`, `avatar.provider`, `avatar.fal_model`, `avatar.max_cost_usd`, `publish.default_privacy`, `audio.bgm_db` (`-22`), `render.debug_safe_zone`, `retention.days` (`30`), `schedule.catchup_minutes` (`120`).

**Khóa bí mật** (keyring): `gemini_api_key`, `openai_api_key`, `fal_key`, `heygen_api_key`, `elevenlabs_api_key`, `ssi_consumer_id`, `ssi_consumer_secret`, `telegram_bot_token`, `facebook_page_token`, `youtube_oauth_token`, `tiktok_access_token`. (`telegram_chat_id`, `facebook_page_id` không bí mật, để trong `settings`.)

---

## 8. HỢP ĐỒNG DỮ LIỆU & GIAO DIỆN PROVIDER (`stockai/models.py`)

Các bước chỉ giao tiếp với nhau qua những model này. Agent PHẢI giữ nguyên tên trường; nếu cần thêm trường, ghi vào DECISIONS.

```python
from datetime import date, datetime
from pathlib import Path
from typing import Literal, Protocol, Callable, Awaitable
from pydantic import BaseModel, Field

DataQuality = Literal["LIVE", "CACHED", "SYNTHETIC"]
SessionType = Literal["PRE_MARKET", "POST_MARKET", "ADHOC"]

class OHLCVBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketSnapshot(BaseModel):
    symbol: str = "VNINDEX"
    session_date: date
    bars: list[OHLCVBar]                 # tăng dần theo ngày, ≥ 21 phiên (mục tiêu 60)
    close: float
    change: float
    change_pct: float
    volume: float | None = None
    value_bn_vnd: float | None = None
    foreign_net_bn_vnd: float | None = None
    sma20: float
    rsi14: float
    support20: float
    resistance20: float
    source: str
    data_quality: DataQuality

class NewsItem(BaseModel):
    id: int | None = None
    title: str
    source: str
    url: str
    published_at: datetime               # luôn có tzinfo
    summary: str = Field(default="", max_length=300)
    content_hash: str
    score: float = 0.0

class ScriptContext(BaseModel):          # đầu vào của LLM
    run_date: date
    session_type: SessionType
    market: MarketSnapshot
    news: list[NewsItem]                 # đã xếp hạng, tối đa 20, đánh chỉ số 0..n-1
    hook_style: str                      # xoay vòng theo ngày (Mục 9.4)

class NewsHighlight(BaseModel):
    headline: str = Field(max_length=90) # validator: ≤ 12 từ
    impact: Literal["TÍCH CỰC", "TIÊU CỰC", "TRUNG LẬP"]
    brief: str
    source_index: int                    # chỉ số tin trong ScriptContext.news

class Scenario(BaseModel):
    name: Literal["CƠ SỞ", "THẬN TRỌNG"]
    description: str

class ScriptOutput(BaseModel):
    video_title: str = Field(max_length=80)
    market_sentiment: Literal["BULLISH", "NEUTRAL", "BEARISH"]
    selected_news: list[NewsHighlight] = Field(min_length=3, max_length=4)
    scenarios: list[Scenario] = Field(min_length=2, max_length=2)
    social_post_text: str
    video_script: str                    # 160–220 từ; câu cuối là câu miễn trừ
    ticker_text: str = Field(max_length=140)
    hashtags: list[str] = Field(default_factory=list, max_length=8)

class WordTiming(BaseModel):
    text: str
    start_ms: int
    end_ms: int

class AudioResult(BaseModel):
    audio_path: Path
    srt_path: Path
    ass_path: Path
    duration_s: float
    words: list[WordTiming]

class AvatarResult(BaseModel):
    video_path: Path                     # đã chuẩn hóa 1080x976, 30fps, khớp độ dài audio
    provider: str
    has_lipsync: bool
    duration_s: float
    cost_usd: float = 0.0

class RenderResult(BaseModel):
    final_video_path: Path
    thumbnail_path: Path
    duration_s: float
    width: int
    height: int
    size_bytes: int

class PublishOptions(BaseModel):
    privacy: Literal["public", "unlisted", "private", "draft"] = "private"
    dry_run: bool = False

class PublishResult(BaseModel):
    platform: str
    status: Literal["SUCCESS", "FAILED", "DRY_RUN", "SKIPPED"]
    privacy_level: str | None = None
    remote_post_id: str | None = None
    remote_post_url: str | None = None
    error_message: str | None = None

ProgressCb = Callable[[float, str], Awaitable[None]]   # (0..1, message)

class MarketDataProvider(Protocol):
    name: str
    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]: ...

class LLMProvider(Protocol):
    name: str
    async def generate(self, ctx: ScriptContext, feedback: str | None = None) -> ScriptOutput: ...

class TTSProvider(Protocol):
    name: str
    async def synthesize(self, text: str, voice: str, rate: str, out_dir: Path) -> AudioResult: ...

class AvatarProvider(Protocol):
    name: str
    has_lipsync: bool
    def estimate_cost_usd(self, duration_s: float) -> float: ...
    async def render(self, portrait: Path, audio: Path, size: tuple[int, int],
                     out_dir: Path, on_progress: ProgressCb) -> AvatarResult: ...

class Publisher(Protocol):
    platform: str
    async def check_credentials(self) -> tuple[bool, str]: ...
    async def publish(self, job_id: str, video: Path, title: str, text: str,
                      opts: PublishOptions) -> PublishResult: ...
```

> Ghi chú: `response_schema` của Gemini có thể không hỗ trợ hết ràng buộc Pydantic (độ dài chuỗi, số phần tử). Luôn validate lại bằng `ScriptOutput.model_validate_json()` sau khi nhận kết quả.

---

## 9. ĐẶC TẢ TỪNG MODULE

### 9.1. Tin tức RSS (`providers/news/rss.py`, `analysis/ranking.py`)

**Nguồn mặc định** (đã kiểm tra hoạt động ngày 23/11/2026):

| Nguồn | URL | Ghi chú |
| :--- | :--- | :--- |
| CafeF | `https://cafef.vn/thi-truong-chung-khoan.rss` | ~50 tin; `pubDate` dùng năm 2 chữ số (`Sun, 22 Nov 26 20:09:00 +0700`) |
| Vietstock | `https://vietstock.vn/830/chung-khoan/co-phieu.rss` | ~20 tin |
| VnEconomy | `https://vneconomy.vn/chung-khoan.rss` | ~50 tin; lẫn tin ngoài chứng khoán (vàng, vĩ mô) → cần lọc từ khóa |

Người dùng CÓ THỂ thêm/bớt nguồn trong Cài đặt.

**Quy tắc:**
* HTTP bằng `httpx` (timeout 10s, User-Agent rõ ràng `StockAI-Studio/3.0`), gửi `If-None-Match`/`If-Modified-Since` nếu đã có; tải song song các nguồn; một nguồn lỗi không làm hỏng cả bước.
* Parse bằng `feedparser`; ngày lấy từ `published_parsed` → chuyển sang `Asia/Ho_Chi_Minh`. Không parse được → bỏ tin và ghi WARN (không gán "bây giờ").
* **Cửa sổ thời gian:** `since = min(now − 48h, 00:00 của ngày giao dịch liền trước)` (ngày giao dịch tính theo thứ 2–6), giới hạn tối đa 96h. Ví dụ sáng thứ Hai → lấy tin từ 00:00 thứ Sáu.
* Làm sạch: `BeautifulSoup(...).get_text(" ", strip=True)`, chuẩn hóa NFC, gộp khoảng trắng, cắt `summary` ≤ 300 ký tự ở ranh giới từ.
* Chống trùng: `content_hash = sha256(normalize(title))` với `normalize` = NFC → lowercase → bỏ dấu câu → gộp khoảng trắng. NÊN thêm chống trùng gần đúng: Jaccard theo từ ≥ 0,6 giữa hai tiêu đề → giữ tin sớm hơn, cộng điểm "nhiều nguồn đưa".
* Lọc chủ đề: giữ tin chứa ít nhất một từ khóa thuộc nhóm chứng khoán/vĩ mô (VN-Index, cổ phiếu, chứng khoán, HOSE, HNX, UPCoM, khối ngoại, thanh khoản, lãi suất, tỷ giá, NHNN, Fed, trái phiếu, mã VN30...). Danh sách từ khóa để trong config.
* **Xếp hạng** (`ranking.py`, thuần, có test): `score = 0,5·độ_mới + 0,3·trọng_số_từ_khóa + 0,2·số_nguồn_cùng_đưa`. Lấy tối đa **20 tin** điểm cao nhất.
* Chỉ lưu tiêu đề, tóm tắt, link. Không tải toàn văn.

### 9.2. Dữ liệu thị trường (`providers/market/*`, `analysis/indicators.py`)

**Chuỗi provider** theo `market.providers_order`; thử lần lượt, nguồn đầu tiên thành công được dùng:

| Provider | Chế độ | Mô tả |
| :--- | :--- | :--- |
| `SsiFastConnectProvider` | PRODUCTION | API chính thức FastConnect Data của SSI (cần tài khoản SSI, đăng ký khóa trên iBoard). Dùng nhóm API `DailyIndex` / `DailyOhlc`. `[KIỂM CHỨNG]` URL, tham số, đơn vị |
| `PublicVciProvider` | DEMO (thử nghiệm) | Endpoint công khai không cần xác thực mà website Vietcap dùng. **Không chính thức**, có thể đổi bất kỳ lúc nào, cần đọc điều khoản sử dụng. Chỉ dùng cho demo cá nhân. `[KIỂM CHỨNG]` (xem tài liệu tham khảo ở Phụ lục C) |
| `CsvImportProvider` | Cả hai | Người dùng thả file CSV `date,open,high,low,close,volume` |
| `CacheProvider` | Cả hai | Đọc `market_snapshots` gần nhất → `data_quality = "CACHED"` |
| `SyntheticProvider` | Chỉ DEMO | Random walk có seed cố định → `data_quality = "SYNTHETIC"` |

* **R-DATA-1:** Mọi provider mạng có timeout 15s, retry 2 lần (chỉ với lỗi mạng/5xx), log tên nguồn.
* **R-DATA-2:** Khi `data_quality == "SYNTHETIC"`: biểu đồ và video có watermark lớn **"DỮ LIỆU MINH HỌA – KHÔNG PHẢI SỐ LIỆU THẬT"**, bước Xuất bản bị chặn (chỉ dry-run), UI hiện cảnh báo vàng.
* **R-DATA-3:** Khi `CACHED` và ngày phiên cũ hơn phiên kỳ vọng: kịch bản PHẢI nói rõ "số liệu phiên ngày dd/mm".
* **Xác định phiên:** không tự bịa danh sách ngày lễ. Phiên mới nhất = ngày của bar cuối cùng từ nguồn LIVE. Với lịch `POST_MARKET`, nếu bar cuối ≠ hôm nay → job `SKIPPED` ("Hôm nay không có phiên giao dịch").
* Trường `foreign_net_bn_vnd`, `value_bn_vnd`, `top_movers` là **tùy chọn**: nguồn không có thì để `None`, và kịch bản không được nhắc (factcheck sẽ chặn).

**Chỉ báo** (`indicators.py`, hàm thuần trên `pandas.Series`, có unit test với số liệu tính tay):
* `SMA20 = close.rolling(20).mean()`
* RSI14 Wilder:
  ```python
  delta = close.diff()
  gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
  loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
  rsi = 100 - 100 / (1 + gain / loss)      # loss == 0 → rsi = 100
  ```
* `support20 = low.tail(20).min()`, `resistance20 = high.tail(20).max()`
* `change = close[-1] − close[-2]`, `change_pct = change / close[-2] · 100`

### 9.3. Biểu đồ (`render/chart.py`)
* Kích thước **1080 × 660 px** (khớp vùng B-roll, Mục 10): `figsize=(10.8, 6.6)`, `dpi=100`, backend `Agg`.
* `mplfinance` nến 60 phiên + panel khối lượng + đường SMA20 + 2 đường nét đứt hỗ trợ/kháng cự có nhãn giá.
* Màu: nền `#0F172A`, lưới `#1E293B`, nến tăng `#10B981`, nến giảm `#F43F5E`, SMA20 `#F59E0B`, chữ `#E5E7EB`.
* Tiêu đề góc trái: `VN-INDEX | 1.285,40 (+12,35 | +0,97%)` theo định dạng số Việt Nam; màu theo tăng/giảm. Dòng phụ: `Phiên dd/mm/yyyy · Nguồn: {source}`.
* Font Be Vietnam Pro đăng ký qua `matplotlib.font_manager.fontManager.addfont`.
* Lề phải chừa ≥ 60px; nhãn quan trọng nằm trong `x ≤ 1020`.
* `SYNTHETIC` → watermark chéo bán trong suốt (R-DATA-2).
* Đầu ra: `chart.png`.

### 9.4. AI biên tập (`providers/llm/*`, `analysis/factcheck.py`)

**Dựng ngữ cảnh:** `ScriptContext` serialize thành JSON gọn (số làm tròn 2 chữ số, tin đánh chỉ số). `hook_style` xoay vòng theo ngày trong danh sách: `câu hỏi gợi tò mò`, `con số nổi bật nhất`, `so sánh với phiên trước`, `tin nóng nhất`, `cảnh báo nhẹ nhàng` (giảm tính rập khuôn).

**System prompt (tiếng Việt):**
```text
Bạn là biên tập viên bản tin chứng khoán Việt Nam. Viết bản tin {session_label} ngày {dd/mm/yyyy}
DỰA DUY NHẤT trên DỮ LIỆU THỊ TRƯỜNG và danh sách TIN bên dưới.

QUY TẮC BẮT BUỘC
1. Chỉ dùng con số, mã cổ phiếu, sự kiện có trong dữ liệu. Trường nào null thì không nhắc tới.
2. Không khuyến nghị mua/bán/nắm giữ bất kỳ mã nào. Không cam kết lợi nhuận. Không dùng các cụm
   "chắc chắn", "mua ngay", "bắt đáy ngay", "x2 tài khoản", "cơ hội cuối cùng".
3. Đưa đúng 2 kịch bản: "CƠ SỞ" và "THẬN TRỌNG", dựa trên hỗ trợ, kháng cự, RSI, SMA20 và dòng tiền (nếu có).
4. selected_news: chọn 3–4 tin tác động lớn nhất; source_index phải đúng chỉ số trong danh sách TIN.
5. video_script: 160–220 từ, văn nói của MC tài chính, câu ngắn, dễ nghe. Mở đầu bằng một câu hook
   theo phong cách: {hook_style}. Viết số theo kiểu Việt Nam (1.285,4 điểm; 0,97%).
   Không markdown, không emoji, không ký hiệu đặc biệt.
   Câu cuối PHẢI là: "Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư."
6. social_post_text: gạch đầu dòng, emoji vừa phải, nêu 2 kịch bản, ghi tên nguồn tin,
   kết thúc bằng câu miễn trừ trách nhiệm và dòng "Video có sử dụng AI (MC ảo, giọng đọc tổng hợp)."
7. ticker_text: tối đa 120 ký tự, dạng "VN-INDEX 1.285,4 (+0,97%) | ...".
8. Trả về đúng JSON theo schema.

DỮ LIỆU THỊ TRƯỜNG:
{market_json}

TIN (đã đánh số):
{news_json}
```

**Gọi Gemini** (`gemini.py`) `[KIỂM CHỨNG cú pháp SDK google-genai]`:
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=key)
resp = await client.aio.models.generate_content(
    model=settings.llm_model,                       # mặc định "gemini-3.8-flash"
    contents=user_prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=ScriptOutput,
        temperature=0.5,
    ),
)
out = ScriptOutput.model_validate_json(resp.text)
```
* Lỗi 429/5xx → retry với backoff; hết lượt → thử `llm.fallback_model` → sau đó `TemplateFallbackProvider`.
* `openai_compat.py`: hỗ trợ mọi API kiểu OpenAI (`base_url`, `model`, `api_key`) với JSON mode.

**Hậu kiểm (bắt buộc, chạy bằng code):**
1. Validate Pydantic.
2. `video_script` có 160–220 từ (đếm theo khoảng trắng); mỗi `headline` ≤ 12 từ.
3. Câu cuối `video_script` đúng câu miễn trừ; `social_post_text` chứa câu miễn trừ và dòng khai báo AI (R-LEGAL-1, R-LEGAL-4).
4. Không chứa cụm từ cấm (danh sách trong config, so khớp không phân biệt hoa thường).
5. **Factcheck số liệu** (`factcheck.py`, hàm thuần, test kỹ):
   * Trích mọi số trong `video_script`, `social_post_text`, `ticker_text` bằng regex hỗ trợ `1.285,40`, `1285,4`, `+0,97%`, `-12,35`, `450 tỷ`.
   * Chuẩn hóa về `float`.
   * Tập số hợp lệ = số trong `MarketSnapshot` (sai số tuyệt đối ≤ 0,01 hoặc tương đối ≤ 0,5% sau làm tròn) ∪ số xuất hiện trong tiêu đề/tóm tắt tin đầu vào ∪ ngày/tháng/năm của phiên ∪ các số nhỏ thông dụng (1–10, 14, 20, 60).
   * Mã cổ phiếu (chuỗi 3 chữ in hoa) phải xuất hiện trong dữ liệu đầu vào.
   * Số hoặc mã không hợp lệ → trả danh sách lỗi.
6. Nếu hậu kiểm lỗi: gọi lại LLM **1 lần** với `feedback` liệt kê lỗi. Vẫn lỗi → dùng `TemplateFallbackProvider` và ghi `factcheck_passed = 0` cho lần LLM, log WARN.

**`TemplateFallbackProvider`:** sinh kịch bản tiếng Việt từ 3–5 mẫu câu (chọn theo ngày), điền số từ `MarketSnapshot` và 3 tin điểm cao nhất (impact mặc định `TRUNG LẬP`). Luôn qua được hậu kiểm. Đây là đường chạy chuẩn khi `--offline`.

### 9.5. Giọng đọc & phụ đề (`providers/tts/*`, `text/vi_normalize.py`, `render/subtitles.py`)

**Chuẩn hóa trước khi đọc** (`vi_normalize.py`, có test): `%` → ` phần trăm`; `+12,35 điểm` → `tăng 12,35 điểm`; `-12,35 điểm` → `giảm 12,35 điểm`; `VN-Index`/`VN-INDEX` → `VN-Index`; `|` → `.`; bỏ emoji và ký tự `* # _ ~`. Có tùy chọn `tts.number_mode = "engine" | "words"` (`words` đổi số thành chữ) để dùng nếu nghe thử thấy đọc sai số.

**edge-tts** (`edge.py`) `[KIỂM CHỨNG tham số boundary ở bản đang dùng]`:
```python
import edge_tts
comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
async for chunk in comm.stream():
    if chunk["type"] == "audio":
        audio_file.write(chunk["data"])
    elif chunk["type"] == "WordBoundary":
        start_ms = chunk["offset"] // 10_000            # đơn vị 100 ns → ms
        end_ms = (chunk["offset"] + chunk["duration"]) // 10_000
        words.append(WordTiming(text=chunk["text"], start_ms=start_ms, end_ms=end_ms))
```
* Giọng: `vi-VN-HoaiMyNeural` (nữ), `vi-VN-NamMinhNeural` (nam). `rate` từ `-10%` đến `+20%`, mặc định `+5%`.
* Không nhận được WordBoundary (chỉ có SentenceBoundary) → chia thời gian câu cho từng từ theo tỉ lệ số ký tự; log WARN.
* Kiểm tra độ dài audio bằng `ffprobe`: 45–95 giây. Ngoài khoảng → yêu cầu LLM viết lại ngắn/dài hơn 1 lần, sau đó chỉnh `rate` trong giới hạn.
* Lỗi kết nối/403 từ dịch vụ → `ProviderError` với gợi ý "Cập nhật edge-tts (`uv lock --upgrade-package edge-tts`) hoặc chọn TTS khác trong Cài đặt".
* `ElevenLabsProvider` (tùy chọn): cùng interface; nếu API trả timestamps theo ký tự thì gộp thành từ. `[KIỂM CHỨNG]` model hỗ trợ tiếng Việt.

**Dựng phụ đề** (`subtitles.py`, hàm thuần, test kỹ):
* Gom từ thành cue: tối đa **2 dòng**; mỗi dòng có độ rộng **≤ 800 px** khi đo bằng `ImageFont.truetype("BeVietnamPro-Bold.ttf", 60).getlength()` (tương đương khoảng 24 ký tự); ưu tiên ngắt sau dấu câu; cue dài 0,8–3,5 giây; khoảng hở < 150 ms giữa 2 cue → kéo dài cue trước để tránh nhấp nháy.
* Xuất `subs.srt` (đăng kèm nền tảng) và `subs.ass` (burn-in) theo style ở Mục 10.4.
* Preview 5 giây cho UI: cache theo `(voice, rate, sha1(text))`.

### 9.6. Avatar (`providers/avatar/*`)

**Tiền xử lý chung:** crop ảnh chân dung về đúng tỉ lệ vùng avatar **1080 × 976**. Có `opencv-python-headless` → dùng Haar cascade tìm mặt, đặt tâm mặt ở `x = 540`, mắt ở khoảng 15–20% chiều cao vùng; không có → crop giữa, lệch lên trên. Ảnh < 720px chiều ngang → cảnh báo chất lượng.

**R-AV-1:** Trước khi gọi provider: kiểm tra bản ghi `consents` của asset (R-LEGAL-3); ước tính chi phí `estimate_cost_usd(duration)`, vượt `avatar.max_cost_usd` → dừng và báo người dùng.

**R-AV-2:** Mọi kết quả PHẢI được chuẩn hóa: `1080x976`, `30 fps`, `yuv420p`, độ dài khớp audio ± 0,1 s (ngắn hơn → `tpad=stop_mode=clone`; dài hơn → cắt).

1. **`DemoMotionProvider`** (mặc định, `has_lipsync=False`):
   ```bash
   ffmpeg -y -loop 1 -framerate 30 -i portrait_1080x976.png -t {D} \
     -vf "scale=4320:-1,zoompan=z='1.03+0.03*sin(2*PI*on/180)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x976:fps=30,format=yuv420p" \
     -c:v libx264 -preset veryfast -crf 20 avatar.mp4
   ```
   (Phóng to ×4 trước `zoompan` để tránh rung hình; chu kỳ "nhịp thở" 6 giây.) Sóng âm được thêm ở bước dựng (Mục 10).
2. **`FalAvatarProvider`** (PRODUCTION, `has_lipsync=True`): `avatar.fal_model` cấu hình được, ví dụ `fal-ai/kling-video/ai-avatar/v2/standard`, `fal-ai/kling-video/ai-avatar/v2/pro`, `fal-ai/bytedance/omnihuman`. Luồng: upload ảnh + audio lên storage của fal → gửi job vào queue → kiểm tra trạng thái mỗi 5 giây (timeout 10 phút, báo tiến độ qua `on_progress`) → tải MP4 → chuẩn hóa (R-AV-2). `[KIỂM CHỨNG]` tên model, tham số, giá.
3. **`HeyGenProvider`** (PRODUCTION): HeyGen API v3 với Photo Avatar (`POST /v3/videos`). Ưu tiên gửi audio có sẵn nếu API hỗ trợ (giữ giọng đồng nhất); nếu không thì dùng voice của HeyGen. `[KIỂM CHỨNG]`
4. **`LocalGPUProvider`** (thử nghiệm, M9): chỉ nghiên cứu sau khi sản phẩm chạy ổn. Lưu ý MuseTalk khớp môi trên video có sẵn; LivePortrait cần video điều khiển. Với "1 ảnh + audio" cần mô hình audio-driven khác; VRAM yêu cầu thay đổi theo mô hình.

**Chế độ Hybrid (NÊN có ở M7 để giảm chi phí):** chỉ tạo talking-head khớp môi cho đoạn mở đầu (~10s) và kết (~5s); phần giữa dùng `DemoMotion` hoặc phóng to B-roll. Composer phải hỗ trợ ghép nhiều đoạn avatar theo mốc thời gian.

### 9.7. Dựng video (`render/cards.py`, `render/composer.py`, `render/ffmpeg.py`)
Theo bố cục **Mục 10**. Dựng **2 giai đoạn** để dễ gỡ lỗi:

**Giai đoạn A — tạo thành phần:**
* `base.png` (1080×1920): nền `#0B1120`, header (logo, "BẢN TIN CHỨNG KHOÁN", nhãn phiên, ngày), đường phân cách phát sáng, nhãn AI. Vẽ bằng Pillow.
* `news_card_{i}.png` (1080×660): nền gradient `#0F172A → #111827`, nhãn tác động (TÍCH CỰC `#10B981` / TIÊU CỰC `#F43F5E` / TRUNG LẬP `#F59E0B`), headline Be Vietnam Pro Bold 56–64px tối đa 3 dòng (tự giảm cỡ nếu tràn), `brief` 32px, tên nguồn ở góc dưới.
* `ticker_strip.png` (cao 60): gọi `S` = độ rộng một đoạn `ticker_text + "  •  "`; lặp đoạn đó `ceil(1080/S) + 1` lần để dải luôn phủ kín khung khi cuộn; nền `#111827`, chữ `#E5E7EB` 34px. Cuộn liền mạch bằng `x = -mod(t*140, S)`. (Render bằng Pillow thay cho `drawtext` để tránh lỗi escape `:` `%` và đảm bảo font tiếng Việt.)
* `ai_intro.png`, `disclaimer.png`: ảnh **trong suốt 1080×1920** chứa nhãn AI mở rộng (3 giây đầu) và dải miễn trừ trách nhiệm (4 giây cuối) đúng tọa độ Mục 10.
* `broll.mp4` (1080×660, 30fps, dài = D): thứ tự `chart → card1 → card2 → card3 (→ card4) → chart`; mỗi đoạn 6–8s, co giãn cho tổng = D; chuyển cảnh `xfade=transition=fade:duration=0.4` (offset tính cộng dồn trừ 0,4s mỗi lần chuyển); biểu đồ có zoom nhẹ 1.00→1.04.

**Giai đoạn B — ghép cuối** (viết filtergraph ra file và chạy với `-filter_complex_script`; đặt `cwd` = thư mục job và dùng **đường dẫn tương đối** để tránh lỗi escape đường dẫn Windows):
```text
Inputs: 0 base.png (-loop 1 -t D) · 1 broll.mp4 · 2 avatar.mp4 · 3 ticker_strip.png (-loop 1 -t D)
        4 voice.mp3 · 5 bgm.mp3 (tùy chọn, -stream_loop -1)
        6 disclaimer.png (-loop 1 -t D) · 7 ai_intro.png (-loop 1 -t D)

[0:v][1:v]overlay=0:280[v1];
[v1][2:v]overlay=0:944[v2];
[v2][3:v]overlay=x='-mod(t*140,{S})':y=220[v3];
[4:a]asplit=2[a_voice][a_wave];
[a_wave]showwaves=s=840x60:mode=cline:colors=0x10B981,format=rgba,colorchannelmixer=aa=0.8[wave];
[v3][wave]overlay=120:1410[v4];
[v4]ass=subs.ass:fontsdir=fonts[v5];
[v5][7:v]overlay=0:0:enable='lt(t,3)'[v6];
[v6][6:v]overlay=0:0:enable='gte(t,{D-4})'[vout];
# Có bgm:
[5:a]volume=-22dB[a_bgm];
[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]
# Không có bgm:
[a_voice]loudnorm=I=-14:TP=-1.5:LRA=11[aout]
```
(`{S}`, `{D-4}` là giá trị số do composer điền vào. Biểu thức có dấu phẩy phải nằm trong nháy đơn; viết test render 8 giây để xác nhận filtergraph chạy trên cả Windows và macOS.)

**Mã hóa:**
```text
-map [vout] -map [aout] -r 30 -c:v libx264 -preset veryfast -crf 23 -maxrate 3500k -bufsize 7000k
-pix_fmt yuv420p -c:a aac -b:a 128k -ar 44100 -movflags +faststart
-metadata title="{video_title}" -metadata comment="AI-generated content: StockAI Studio; synthetic presenter & voice"
```
(Giới hạn bitrate để video ~75–90s nằm dưới 48 MB → gửi được qua Telegram.)

**Kiểm tra sau render (bắt buộc, dùng `ffprobe`):** 1080×1920, 30 fps, có luồng audio, `|duration − D| ≤ 0,5s`, kích thước < 48 MB. Sai → `FAILED` kèm thông tin. Tạo `thumbnail.jpg` tại giây thứ 1. Đặt `ai_label_applied = 1`.

**Preflight FFmpeg** (`ffmpeg.py`): chạy `ffmpeg -hide_banner -filters` và `-encoders`, xác nhận có `ass`, `zoompan`, `showwaves`, `xfade`, `loudnorm`, `libx264`. Thiếu → hiển thị trên Dashboard kèm lệnh cài.

**Debug:** `render.debug_safe_zone = true` → phủ lớp đỏ mờ lên vùng bị UI nền tảng che (Mục 10.3) và xuất `safe_zone_check.png` (frame ở giây 5).

### 9.8. Xuất bản (`providers/publish/*`, `text/captions.py`)

**Quy tắc chung:**
* **R-PUB-1:** Không đăng khi `data_quality == "SYNTHETIC"` hoặc `ai_label_applied == 0`.
* **R-PUB-2:** Idempotent — đã có `SUCCESS` cho `(job_id, platform)` thì bỏ qua.
* **R-PUB-3:** Retry tối đa 3 lần cho timeout/5xx/429 (backoff lũy thừa); không retry lỗi 4xx khác.
* **R-PUB-4:** Bật mọi cờ khai báo AI mà nền tảng có (TikTok `is_aigc`, YouTube `containsSyntheticMedia`).
* `captions.py` sinh nội dung riêng cho từng nền tảng theo giới hạn ký tự; thêm hashtag; YouTube thêm `#Shorts`.
* `DryRunPublisher`: ghi `publish_preview.json` (nền tảng, tiêu đề, caption, privacy) và trạng thái `DRY_RUN`.

| Nền tảng | Cách làm |
| :--- | :--- |
| **Telegram** | `sendVideo` (multipart, `supports_streaming=true`, `width/height/duration`, `thumbnail`) với caption ≤ 1024 ký tự (tiêu đề + 2–3 ý chính + "Chi tiết ở tin nhắn bên dưới"), sau đó `sendMessage` bài đầy đủ (≤ 4096 ký tự/tin, chia nhỏ nếu dài, `parse_mode=HTML` có escape). Đây là kênh test thật ở DEMO. |
| **Facebook Reels** | `POST /{page-id}/video_reels` với `upload_phase=start` → upload byte lên `rupload.facebook.com` (header `Authorization: OAuth {token}`) → `upload_phase=finish`, `video_state=PUBLISHED`, `description`. Phiên bản Graph API là cấu hình (ví dụ `v25.0`) `[KIỂM CHỨNG]`. Đếm số Reels đã đăng 24h qua, không vượt 30. |
| **YouTube Shorts** | OAuth installed-app (`google-auth-oauthlib`, loopback), token lưu keyring. `videos.insert` resumable; `snippet` (tiêu đề ≤ 100 ký tự có `#Shorts`, mô tả, tags, `categoryId` cấu hình), `status.privacyStatus` mặc định `private` cho các lần đầu, `selfDeclaredMadeForKids=false`, `containsSyntheticMedia=true`. Token hết hạn → trạng thái "Cần đăng nhập lại". |
| **TikTok** | Content Posting API: gọi `creator_info` trước (lấy `privacy_level_options`, `max_video_post_duration_sec`). Mặc định chế độ **Upload/gửi nháp vào hộp thư TikTok** để người dùng tự hoàn tất trong app; chỉ bật Direct Post khi app đã qua audit. `is_aigc=true`. Phương án thay thế: dịch vụ trung gian đã được audit qua webhook (cấu hình URL). `[KIỂM CHỨNG]` endpoint, tham số. |

**Duyệt bài (human-in-the-loop):**
* `require_approval = 1` (mặc định): sau B4, job → `WAITING_APPROVAL`. UI hiện thông báo; CÓ THỂ gửi bản nháp video vào Telegram chat riêng của chủ kênh. Người dùng xem, sửa tiêu đề/caption, chọn nền tảng + quyền riêng tư (bắt buộc cho TikTok) rồi bấm **Duyệt & Đăng**.
* `require_approval = 0`: tự đăng các nền tảng đã chọn, **trừ TikTok** (luôn cần duyệt).

### 9.9. Lập lịch (`stockai/scheduler.py`)
* APScheduler 3.11 `AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")`, `CronTrigger(day_of_week=..., hour=..., minute=...)`.
* Job id cố định `schedule-{id}`, `replace_existing=True`, `misfire_grace_time=1800`, `coalesce=True`, `max_instances=1`.
* Khi thêm/sửa/bật/tắt/xóa lịch qua API → đồng bộ ngay, không cần khởi động lại.
* **Chạy bù:** lúc khởi động (hoặc khi máy thức dậy), nếu một lịch của hôm nay bị lỡ trong vòng `schedule.catchup_minutes` (mặc định 120) và chưa có job cho lịch đó → tạo job `trigger="CATCHUP"`; quá thời gian → ghi WARN "Đã lỡ lịch".
* **Thử lại:** lỗi tạm thời (mạng, 5xx) → tối đa 3 lần, cách nhau 5 phút; ghi lỗi vào `content_jobs` và `job_events`.
* **Bỏ qua:** lịch `POST_MARKET` mà không có phiên hôm nay → `SKIPPED` (Mục 9.2).
* NÊN chặn máy ngủ khi pipeline đang chạy (Windows `SetThreadExecutionState`; macOS `caffeinate -i -w <pid>`).
* UI PHẢI ghi rõ: **"Lịch chỉ chạy khi ứng dụng đang mở (có thể thu nhỏ xuống khay hệ thống)."** Khay hệ thống và tự khởi động cùng máy làm ở M8.

---

## 10. BỐ CỤC VIDEO 9:16 — PHIÊN BẢN 3 (`stockai/layout.py`)

### 10.1. Thông số chung
`1080 × 1920`, 30 fps, H.264 + AAC, audio −14 LUFS. **Mọi tọa độ dưới đây PHẢI định nghĩa một lần trong `layout.py`** (dataclass) và chỉ được tham chiếu từ đó.

### 10.2. Sơ đồ tọa độ

```text
y=0    +-----------------------------------------------------------+
       |  (vùng bị UI nền tảng che phía trên — chỉ nền, không chữ)  |  Z0  h=120
y=120  +-----------------------------------------------------------+
       | [LOGO] BẢN TIN CHỨNG KHOÁN · TỔNG KẾT PHIÊN   23/11/2026   |  Z1 Header h=100
y=220  +-----------------------------------------------------------+
       | >> VN-INDEX 1.285,4 (+0,97%) | THANH KHOẢN ... (chữ chạy)  |  Z2 Ticker h=60
y=280  +-----------------------------------------------------------+
       | [AI] Nội dung có sử dụng AI           (nhãn cố định)       |
       |                                                           |
       |             VÙNG B-ROLL 1080 x 660                         |  Z3
       |   Biểu đồ VN-Index ↔ Thẻ tin nóng #1..#4 (6–8s/đoạn)       |
       |                                                           |
y=940  +===========================================================+  Z4 Đường phân cách 4px #10B981
y=944  |                                                           |
       |              (đỉnh đầu ~ y 980)                           |
       |            MẶT MC: tâm x=540, mắt ~ y 1090                 |  Z5 Avatar 1080 x 976
       |                                                           |
y=1240 |   +---------------------------------------------------+   |
       |   |   PHỤ ĐỀ 2 DÒNG, x 140–940, đáy chữ tại y=1400     |   |
y=1400 |   +---------------------------------------------------+   |
y=1410 |      ~~~~ sóng âm 840x60 (trang trí) ~~~~                 |
y=1440 | - - - - - - từ đây xuống: bị caption/nút che - - - - - - - |
       |                (chỉ còn thân/vai MC)                      |
y=1920 +-----------------------------------------------------------+
```

| Vùng | x | y | Kích thước | Nội dung |
| :--- | :--- | :--- | :--- | :--- |
| Z0 | 0–1080 | 0–120 | 1080×120 | Nền |
| Z1 Header | 60–1020 | 120–220 | 960×100 | Logo (cao ≤ 72px), tiêu đề, nhãn phiên, ngày |
| Z2 Ticker | 0–1080 | 220–280 | 1080×60 | Dải chữ chạy 140 px/s |
| Z3 B-roll | 0–1080 | 280–940 | 1080×660 | Biểu đồ / thẻ tin |
| Nhãn AI | 76–… | 296–340 | cao 44px | Badge "AI" + "Nội dung có sử dụng AI" (suốt video) |
| Z4 | 0–1080 | 940–944 | 1080×4 | Đường phát sáng |
| Z5 Avatar | 0–1080 | 944–1920 | 1080×976 | Video nhân vật |
| Phụ đề | 140–940 | 1240–1400 | 800×160 | Burn-in ASS |
| Sóng âm | 120–960 | 1410–1470 | 840×60 | `showwaves` (có thể bị che một phần, chỉ trang trí) |
| Miễn trừ | 60–960 | 860–930 | 900×70 | 4 giây cuối, trong vùng B-roll |

### 10.3. Vùng an toàn (safe zone)
* Phía dưới **y ≥ 1440**: bị caption, tên kênh, thanh âm thanh của TikTok/Reels/Shorts che → **không đặt chữ hay thông tin quan trọng**.
* Bên phải **x ≥ 960 khi y ≥ 840**: cột nút like/comment/share → không đặt chữ.
* Phía trên **y < 120**: thanh tab/nút của app → chỉ nền. Reels che sâu hơn (tới ~210px) nên header chỉ chứa thương hiệu; **nhãn AI không được chỉ nằm ở header** (đặt thêm trong Z3).
* Kích thước UI mỗi app thay đổi theo thiết bị/phiên bản → các con số là mặc định thận trọng, chỉnh trong `layout.py`; luôn xem lại bằng chế độ `debug_safe_zone`.

### 10.4. Style phụ đề ASS
```text
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Be Vietnam Pro,60,&H0015CCFA,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,140,140,520,1
```
* Màu ASS là `&HAABBGGRR`: vàng `#FACC15` = `&H0015CCFA`; trắng = `&H00FFFFFF`.
* `Alignment=2` (giữa-dưới), `MarginV=520` → đáy dòng chữ tại y = 1920 − 520 = **1400**; `MarginL/R=140` → chữ nằm trong x 140–940, tránh cột nút bên phải.
* `Fontname` phải trùng tên family bên trong file TTF. Composer copy `assets/fonts/` vào `fonts/` trong thư mục job để `fontsdir=fonts` hoạt động với đường dẫn tương đối.
* Ngắt dòng đã làm sẵn ở bộ dựng cue (dùng `\N`), `WrapStyle: 2` để libass không tự ngắt thêm.
* Có thể tô màu từ đang đọc (karaoke `\k`) ở bản sau.

### 10.5. Nhãn & miễn trừ (R-LEGAL-1)
* Nhãn AI cố định suốt video tại Z3 (trên cả biểu đồ và thẻ tin).
* 3 giây đầu: nhãn mở rộng "Video có sử dụng AI: MC ảo & giọng đọc tổng hợp".
* 4 giây cuối: dải miễn trừ "Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư."
* `SYNTHETIC` → thêm watermark "DỮ LIỆU MINH HỌA" lên toàn bộ Z3.

---

## 11. API NỘI BỘ & WEBSOCKET

Base: `http://127.0.0.1:{port}`. Mọi request `/api/*` PHẢI có header `X-App-Token` (R-SEC-2).

| Method | Endpoint | Chức năng |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Chế độ, job đang chạy, lịch kế tiếp (ISO + số giây đếm ngược), trạng thái preflight tóm tắt |
| `GET` | `/api/preflight` | Chi tiết: FFmpeg + filter, font, quyền ghi thư mục, khóa đã cấu hình, kết nối mạng |
| `POST` | `/api/pipeline/run` | Body `{mode, session_type, platforms[], dry_run, skip_publish}` → `202 {job_id}`; đang có job → `409` |
| `POST` | `/api/pipeline/cancel` | Hủy job đang chạy (dừng giữa các bước, kill ffmpeg) |
| `GET` | `/api/jobs?limit=&offset=&status=` | Danh sách job |
| `GET` | `/api/jobs/{id}` | Chi tiết: script, tin đã chọn, artifacts, publish_logs, events |
| `PUT` | `/api/jobs/{id}` | Sửa `video_title`, `social_post_text` trước khi đăng |
| `POST` | `/api/jobs/{id}/approve` | Body `{platforms[], privacy: {platform: level}}` → bắt đầu đăng |
| `POST` | `/api/jobs/{id}/publish` | Đăng lại / đăng thêm nền tảng |
| `POST` | `/api/jobs/{id}/retry` | Body `{from_step?}` → chạy lại từ bước lỗi |
| `DELETE` | `/api/jobs/{id}` | Xóa job + thư mục artifacts |
| `GET` | `/media/{job_id}/{filename}` | Phục vụ file (hỗ trợ HTTP Range để tua video), chặn path traversal |
| `POST` | `/api/assets/upload` | Multipart `kind=avatar|logo|bgm`; với avatar bắt buộc `consent_subject_name`, `consent_relation`, `consent_statement` |
| `GET` | `/api/assets` | Tài nguyên đang dùng |
| `POST` | `/api/tts/preview` | Body `{voice, rate, text?}` → URL audio 5 giây |
| `GET`/`POST` | `/api/schedules` | Danh sách / tạo lịch |
| `PUT`/`DELETE` | `/api/schedules/{id}` | Sửa (kể cả bật/tắt) / xóa |
| `GET`/`PUT` | `/api/settings` | Đọc (bí mật bị che) / lưu (bí mật vào keyring) |
| `POST` | `/api/settings/test/{service}` | Kiểm tra kết nối: `gemini`, `fal`, `heygen`, `telegram`, `facebook`, `youtube`, `tiktok`, `ssi` |
| `POST` | `/api/maintenance/cleanup` | Body `{older_than_days}` → xóa outputs cũ, trả dung lượng giải phóng |
| `WS` | `/ws/events?token=` | Luồng sự kiện realtime |

**Định dạng lỗi chung:**
```json
{ "error": { "code": "FFMPEG_MISSING_FILTER", "message": "Bản FFmpeg thiếu bộ lọc 'ass'.", "hint": "Cài bản FFmpeg đầy đủ: winget install Gyan.FFmpeg" } }
```

**Sự kiện WebSocket:**
```json
{ "type": "log",        "job_id": "…", "step": 4, "level": "INFO", "message": "Đang dựng B-roll (3/5)", "ts": "2026-11-23T08:31:02.120Z" }
{ "type": "progress",   "job_id": "…", "step": 4, "progress": 82 }
{ "type": "job_status", "job_id": "…", "status": "WAITING_APPROVAL" }
{ "type": "schedule",   "next_run_at": "2026-11-24T07:30:00+07:00" }
```
Tiến độ theo bước: B1 0→20 · B2 20→35 · B3 35→70 · B4 70→95 · B5 95→100.

---

## 12. GIAO DIỆN NGƯỜI DÙNG

* **Công nghệ:** HTML + JavaScript (ES modules) không cần build; Tailwind v4 browser build **tải sẵn vào `ui/vendor/`** để chạy offline (nếu gặp khó thì dùng CSS thuần với CSS variables). Font Be Vietnam Pro.
* **Phong cách Dark Fintech:** nền `#0B1120`, thẻ `#111827` viền `#1F2937`, tăng `#10B981`, giảm `#F43F5E`, nút hành động `#3B82F6`, cảnh báo `#F59E0B`.
* **Bố cục:** sidebar trái 240px + nội dung chính. Toàn bộ chữ tiếng Việt.

**Tab 1 — Bảng điều khiển**
* 4 thẻ: VN-Index phiên gần nhất (kèm badge `LIVE`/`CACHED`/`MINH HỌA`), tổng số video, lịch tiếp theo (đếm ngược), chế độ hiện tại.
* Banner preflight nếu thiếu FFmpeg/filter/font/khóa.
* Nút lớn **`▶ CHẠY QUY TRÌNH NGAY`** (+ nút Hủy khi đang chạy).
* Thanh 5 bước: `1. Thu thập` → `2. AI biên tập` → `3. Giọng & Avatar` → `4. Dựng video` → `5. Xuất bản`.
* **Live Terminal Log** nền đen, màu theo cấp độ, tự cuộn, có nút sao chép log.

**Tab 2 — Nhân vật & Giọng nói**
* Trái: xem trước ảnh chân dung (có khung mô phỏng vùng crop 1080×976), kéo-thả ảnh mới, **ô xác nhận đồng ý bắt buộc** (R-LEGAL-3), tải logo, tải nhạc nền.
* Phải: chọn provider avatar (`Demo – chuyển động nhẹ` / `fal.ai` / `HeyGen`) kèm **ước tính chi phí/video**; chọn giọng; thanh trượt tốc độ; nút **`🔊 Nghe thử`**.

**Tab 3 — Kho nội dung & Duyệt bài**
* Danh sách thẻ theo ngày, lọc theo trạng thái; job `WAITING_APPROVAL` nổi bật.
* Màn hình chi tiết chia đôi:
  * Trái: `<video>` 9:16, nút bật lớp safe-zone, tải về, mở thư mục.
  * Phải: tab *Bài đăng* (soạn thảo + Copy), *Kịch bản*, *Biểu đồ*, *Tin nguồn* (link gốc), *Log*; khu **Duyệt & Đăng** với checkbox nền tảng + chọn quyền riêng tư từng nền tảng; trạng thái đăng từng nền tảng kèm link.

**Tab 4 — Lịch tự động**
* Form: tên, loại phiên (Trước phiên / Sau phiên), giờ & phút, ngày (T2–T6 / cả tuần), nền tảng, công tắc *"Chờ tôi duyệt trước khi đăng"*.
* Bảng lịch: bật/tắt nhanh, sửa, xóa, lần chạy gần nhất + kết quả.
* Ghi chú cố định: *"Lịch chỉ chạy khi ứng dụng đang mở."*

**Tab 5 — Cài đặt**
* Công tắc **DEMO ↔ PRODUCTION** (chuyển sang PRODUCTION hiện danh sách điều kiện còn thiếu).
* Nhóm khóa (ẩn/hiện, nút **Kiểm tra kết nối**): *AI* (Gemini, OpenAI-compatible, tên model), *Dữ liệu* (SSI FastConnect, thứ tự nguồn), *Avatar & Giọng* (fal, HeyGen, ElevenLabs), *Mạng xã hội* (Telegram Bot Token + Chat ID, Facebook Page ID + Token, YouTube đăng nhập OAuth, TikTok).
* Bảo trì: dọn file cũ hơn N ngày, mở thư mục dữ liệu, xuất log chẩn đoán.

---

## 13. LỖI, VẬN HÀNH & ĐÓNG GÓI

### 13.1. Phân loại lỗi (`errors.py`)
| Loại | Ví dụ | Xử lý |
| :--- | :--- | :--- |
| `TransientError` | timeout, 5xx, 429 | Retry theo chính sách của module |
| `ConfigError` | thiếu khóa, FFmpeg thiếu filter | Dừng, `hint` hướng dẫn người dùng |
| `ProviderError` | API trả lỗi nghiệp vụ | Chuyển sang provider dự phòng nếu có |
| `ValidationError` | LLM sai schema, video sai kích thước | Thử lại có giới hạn rồi fallback/FAILED |
| `CancelledError` | người dùng hủy | `CANCELLED`, dọn tiến trình con |

### 13.2. Timeout từng bước
RSS 30s · thị trường 30s · LLM 90s · TTS 60s · avatar API 10 phút · render 5 phút · đăng 5 phút/nền tảng.

### 13.3. Log & dọn dẹp
* Log xoay vòng trong `logs/` (5 file × 5 MB), che bí mật (R-SEC-5).
* Xóa `temp/` sau mỗi job; nút dọn `outputs/` cũ hơn `retention.days`.
* `manifest.json` trong mỗi thư mục job: danh sách artifact + checksum + bước đã xong.

### 13.4. Đóng gói (M8)
* `PyInstaller` chế độ **onedir** (khởi động nhanh hơn, ít bị antivirus báo nhầm so với onefile); kèm `ui/`, `assets/fonts/`.
* FFmpeg: mặc định dùng bản trên máy. Nếu đóng gói kèm FFmpeg có `libx264` → bản build GPL, phải tuân thủ nghĩa vụ giấy phép khi phân phối.
* Windows cần WebView2 Runtime (thường có sẵn trên Windows 10/11); macOS nên ký và notarize để tránh Gatekeeper chặn.
* Khay hệ thống (`pystray`) + tùy chọn tự khởi động cùng máy.

---

## 14. KIỂM THỬ

* `pytest` + `pytest-asyncio`. Test cần mạng đánh dấu `@pytest.mark.network`, mặc định bỏ qua.
* `STOCKAI_OFFLINE=1` (hoặc `--offline`): mọi provider dùng fixture → toàn bộ pipeline chạy không cần mạng, không cần khóa.
* **Fixture** (`tests/fixtures/`): RSS **tự tạo** đúng cấu trúc 3 nguồn (gồm `pubDate` năm 2 chữ số, tin trùng, tin ngoài chủ đề); `ohlcv_vnindex_60.csv`; JSON LLM hợp lệ và JSON có số bịa; audio mẫu 8 giây (tạo bằng `ffmpeg -f lavfi -i sine` hoặc edge-tts khi có mạng).
* **Unit test bắt buộc:** `indicators` (so với số tính tay), `ranking`, chống trùng, cửa sổ thời gian (thứ Hai sáng), `factcheck` (bắt được số bịa, chấp nhận số đúng các định dạng), `vi_normalize`, bộ dựng cue (≤ 2 dòng, mỗi dòng ≤ 800 px, không chồng lấn thời gian), `captions` (giới hạn ký tự từng nền tảng), `layout` (không vùng nào vượt khung; phụ đề, nhãn AI, ticker không giao với vùng bị che ở Mục 10.3).
* **Integration:** `stockai render-sample` (8 giây) → `ffprobe` đúng 1080×1920/30fps/có audio.
* **E2E:** `uv run stockai run --mode demo --offline --no-publish` → `final.mp4` qua mọi kiểm tra Mục 9.7.
* **API test:** `TestClient` — thiếu token → 401, sai Origin → 403, chạy 2 job → 409.
* NÊN có GitHub Actions chạy `ruff` + `pytest` trên Ubuntu và Windows (cài FFmpeg trong CI).

---

## 15. LỘ TRÌNH MILESTONE (CHO AI AGENT)

> Mỗi milestone: agent lập kế hoạch → kiểm chứng `[KIỂM CHỨNG]` liên quan → viết test → code → chạy lệnh nghiệm thu → báo cáo → **dừng chờ duyệt**. Được phép để stub `raise NotImplementedError("M7")` cho phần thuộc milestone sau; không để TODO trong phần thuộc milestone hiện tại.

### M0 — Khung dự án
* `pyproject.toml` (uv), `ruff`, `pytest`; `config.py`, `layout.py`, `models.py`, `errors.py`, `secrets.py`; `db/schema.sql` + `migrate.py`; `cli.py` với `preflight`, `db migrate`; `docs/DECISIONS.md`; `README.md` bản đầu.
* **Nghiệm thu:** `uv run stockai preflight` in bảng trạng thái (FFmpeg + từng filter, font, thư mục dữ liệu, keyring); `uv run pytest -q` xanh; DB tạo đủ 10 bảng (9 bảng nghiệp vụ + `schema_version`).

### M1 — Thu thập & biểu đồ
* RSS (lọc, chống trùng, xếp hạng), các market provider (Synthetic, CSV, Cache, PublicVci thử nghiệm), `indicators.py`, `chart.py`.
* **Nghiệm thu:** `uv run stockai run --step collect --offline` tạo `chart.png` 1080×660 + danh sách tin; chạy có mạng lấy được tin thật 3 nguồn; test chỉ báo & cửa sổ thời gian xanh; dữ liệu SYNTHETIC có watermark.

### M2 — AI biên tập
* `gemini.py`, `openai_compat.py`, `template_fallback.py`, hậu kiểm + `factcheck.py`.
* **Nghiệm thu:** offline → kịch bản mẫu hợp lệ; có khóa Gemini → `ScriptOutput` hợp lệ, qua factcheck; test với JSON có số bịa → bị chặn và fallback.

### M3 — Giọng đọc & phụ đề
* `vi_normalize.py`, `edge.py`, `subtitles.py` (SRT + ASS), preview 5 giây.
* **Nghiệm thu:** tạo `voice.mp3`, `subs.srt`, `subs.ass` từ kịch bản M2; độ dài 45–95s; test cue xanh.

### M4 — Avatar demo & dựng video
* Tạo ảnh chân dung mẫu (placeholder vẽ bằng Pillow, `is_placeholder=1`), crop, `DemoMotionProvider`, `cards.py`, `composer.py` 2 giai đoạn, kiểm tra ffprobe, chế độ debug safe-zone.
* **Nghiệm thu:** `uv run stockai run --mode demo --offline --no-publish` → `final.mp4` đúng Mục 9.7; `safe_zone_check.png` cho thấy phụ đề, nhãn AI, ticker không nằm trong vùng bị che; tiếng Việt hiển thị đúng dấu.

### M5 — Backend, Orchestrator & UI
* `orchestrator.py` (lock, cancel, retry, manifest), `api.py`, `ws.py`, `security.py`, `app.py` (pywebview + fallback trình duyệt), UI 5 tab.
* **Nghiệm thu:** `uv run python app.py` mở cửa sổ; bấm Chạy → thanh tiến trình + log realtime; xem video trong Kho nội dung; sửa caption; API test 401/403/409 xanh.

### M6 — Lịch tự động, Telegram & duyệt bài
* `scheduler.py` (đồng bộ CRUD, chạy bù, retry, skip), `telegram.py`, `dry_run.py`, luồng `WAITING_APPROVAL` → duyệt → đăng.
* **Nghiệm thu:** tạo lịch sau 2 phút → tự chạy → chờ duyệt → duyệt → Telegram nhận video + bài đầy đủ; đồng hồ đếm ngược trên Dashboard đúng; đóng app trong giờ lịch rồi mở lại trong 120 phút → chạy bù.

### M7 — Tích hợp PRODUCTION (mỗi mục sau một cờ bật/tắt)
* `SsiFastConnectProvider`; `FalAvatarProvider` + `HeyGenProvider` + chế độ Hybrid + giới hạn chi phí; `facebook.py`; `youtube.py` (OAuth); `tiktok.py` (gửi nháp); ElevenLabs (tùy chọn).
* **Nghiệm thu:** mỗi tích hợp có nút "Kiểm tra kết nối" chạy được; đăng thử ở chế độ private/nháp thành công; chi phí ước tính hiển thị và được ghi vào job.

### M8 — Đóng gói & phát hành
* PyInstaller onedir cho Windows và macOS, icon, khay hệ thống, tự khởi động, hướng dẫn cài đặt cho người không biết lập trình.
* **Nghiệm thu:** cài trên máy sạch (chỉ có FFmpeg) → chạy demo offline thành công.

### M9 — Thử nghiệm (không bắt buộc)
* `LocalGPUProvider`, phụ đề karaoke, C2PA, gửi bản nháp kèm nút duyệt ngay trong Telegram.

---

## 16. ƯỚC TÍNH CHI PHÍ PRODUCTION `[KIỂM CHỨNG giá trước khi chốt]`

Giả định: video 75 giây, 2 video/ngày, 22 ngày giao dịch/tháng = **44 video/tháng**.

| Avatar | Giá tham khảo | Chi phí/video | Chi phí/tháng |
| :--- | :--- | :--- | :--- |
| DemoMotion (không khớp môi) | 0 | 0 | 0 |
| Kling AI Avatar v2 Standard (fal) | $0,0562/giây | ~$4,22 | ~$185 |
| Kling AI Avatar v2 Pro (fal) | $0,115/giây | ~$8,63 | ~$380 |
| OmniHuman (fal) | $0,14/giây | ~$10,50 | ~$462 |
| HeyGen Photo Avatar 4 (qua Hedra) | $0,10/giây | ~$7,50 | ~$330 |
| **Hybrid** (Kling Standard 15 giây/video) | $0,0562/giây | ~$0,84 | ~$37 |

* LLM (Gemini Flash): mỗi lần chỉ vài nghìn token → chi phí rất thấp; free tier đủ cho demo.
* TTS edge-tts: miễn phí. ElevenLabs/Vbee: theo gói.
* Đăng bài qua API chính thức: không tính phí (dịch vụ trung gian cho TikTok có phí riêng).

---

## 17. RỦI RO & QUYẾT ĐỊNH MỞ (CHỦ DỰ ÁN CHỐT)

| Mã | Câu hỏi | Mặc định nếu chưa chốt |
| :--- | :--- | :--- |
| D1 | Nguồn dữ liệu PRODUCTION: mở tài khoản SSI để dùng FastConnect Data, hay mua dữ liệu có giấy phép? | Chưa bật PRODUCTION cho tới khi có nguồn hợp lệ |
| D2 | YouTube: chấp nhận kênh không kiếm tiền, hay thêm phần người thật (quay intro/outro, bình luận riêng) để tăng tính nguyên bản? | Coi YouTube là kênh phân phối, không tính doanh thu |
| D3 | TikTok: gửi nháp (tự bấm đăng trong app), dùng dịch vụ trung gian đã audit, hay tự xin audit? | Gửi nháp |
| D4 | Nhà cung cấp avatar & ngân sách tháng | DemoMotion; khi bật PRODUCTION dùng Hybrid + Kling Standard |
| D5 | Ảnh chân dung dùng ảnh của ai? Có bản đồng ý chưa? | Chỉ ảnh của chính người dùng |
| D6 | Có clone giọng thật của bạn (ElevenLabs) không? | Không; dùng giọng Neural có sẵn |
| D7 | Dùng endpoint công khai không chính thức (`PublicVciProvider`) trong DEMO? | Bật trong DEMO, ghi rõ "nguồn không chính thức"; tắt ở PRODUCTION |
| D8 | Mức độ tự động: có bao giờ cho đăng không cần duyệt? | Luôn duyệt trong 2 tuần đầu; TikTok luôn duyệt |

**Rủi ro kỹ thuật chính:** edge-tts ngừng hoạt động; endpoint không chính thức đổi cấu trúc; nền tảng đổi API/giới hạn; laptop ngủ hoặc tắt app làm lỡ lịch; video rập khuôn bị giảm phân phối. Biện pháp: mọi thứ qua interface provider, có fallback, có preflight và nút kiểm tra kết nối, có chạy bù, và luôn có người duyệt.

---

## PHỤ LỤC A — NỘI DUNG `CLAUDE.md` / `AGENTS.md`

```markdown
# StockAI Studio — Quy tắc cho AI agent

## Nguồn sự thật
- Đặc tả: docs/BLUEPRINT.md (v3.0). Nhật ký quyết định: docs/DECISIONS.md.
- Thứ tự ưu tiên khi mâu thuẫn: Mục 3 > Mục 8 > Mục 10 > phần còn lại.

## Cách làm việc
- Làm đúng MỘT milestone mỗi phiên (BLUEPRINT Mục 15). Hết milestone thì dừng, báo cáo, chờ duyệt.
- Trước khi code phần có nhãn [KIỂM CHỨNG]: đọc tài liệu chính thức, ghi kết quả + link + ngày vào DECISIONS.md.
- Viết test trước cho hàm thuần. Sau mỗi thay đổi chạy: `uv run ruff check . && uv run pytest -q`.
- Báo cáo cuối milestone gồm: file đã tạo/sửa, output lệnh nghiệm thu, rủi ro còn lại.

## Lệnh
- Cài: `uv sync`
- Kiểm tra môi trường: `uv run stockai preflight`
- Chạy pipeline offline: `uv run stockai run --mode demo --offline --no-publish`
- Mở app: `uv run python app.py`
- Test: `uv run pytest -q` (test cần mạng: `uv run pytest -m network`)

## Ràng buộc cứng
- KHÔNG thêm vnstock/vnai. KHÔNG hardcode API key; bí mật chỉ qua stockai/secrets.py (keyring).
- Tọa độ khung hình chỉ định nghĩa trong stockai/layout.py.
- Các bước chỉ trao đổi dữ liệu qua model trong stockai/models.py.
- Mọi chuỗi hiển thị cho người dùng bằng tiếng Việt; text render phải chuẩn hóa NFC.
- Không đăng nội dung khi data_quality = SYNTHETIC; luôn gắn nhãn AI (R-LEGAL-1, R-PUB-1).
- FFmpeg: dùng -filter_complex_script, cwd = thư mục job, đường dẫn tương đối.
- Không tự bịa endpoint/tham số API: không chắc thì viết adapter + fixture + ghi [KIỂM CHỨNG].
```

---

## PHỤ LỤC B — PROMPT CHO AI AGENT

### B.1. Prompt khởi động (dán ở phiên đầu tiên)
```text
Bạn là kỹ sư Python full-stack cao cấp, phụ trách dự án StockAI Studio.
Đặc tả duy nhất: docs/BLUEPRINT.md (v3.0). Quy tắc làm việc: CLAUDE.md.

BƯỚC 1 — HIỂU (chưa viết code):
a) Tóm tắt kiến trúc trong tối đa 12 gạch đầu dòng.
b) Liệt kê các mục [KIỂM CHỨNG] thuộc M0 và M1, và cách bạn sẽ kiểm chứng.
c) Nêu câu hỏi cần tôi quyết (nếu có). Không hỏi những gì đã có mặc định trong Mục 17.

BƯỚC 2 — LÀM M0 (Mục 15):
- Lập danh sách file sẽ tạo.
- Triển khai, chạy `uv run ruff check . && uv run pytest -q` và `uv run stockai preflight`.
- Ghi quyết định vào docs/DECISIONS.md.
- Báo cáo kết quả (kèm output lệnh) rồi DỪNG, chờ tôi xác nhận trước khi sang M1.
```

### B.2. Prompt cho từng milestone tiếp theo
```text
Tiếp tục milestone M{n} trong docs/BLUEPRINT.md (Mục 15).
1. Liệt kê kế hoạch: file tạo/sửa, test sẽ viết.
2. Kiểm chứng các mục [KIỂM CHỨNG] trong phạm vi M{n}, ghi vào docs/DECISIONS.md.
3. Viết test trước cho hàm thuần, sau đó triển khai.
4. Chạy `uv run ruff check . && uv run pytest -q` và lệnh nghiệm thu của M{n}.
5. Báo cáo: đã làm gì, output lệnh, điểm còn rủi ro. Dừng chờ duyệt.
```

### B.3. Prompt sửa lỗi
```text
Lỗi sau xảy ra khi chạy `{lệnh}`:
{dán log}
Hãy: (1) xác định nguyên nhân gốc, (2) viết test tái hiện lỗi, (3) sửa, (4) chạy lại test + lệnh trên.
Không sửa test cho "qua" nếu test đó đúng với BLUEPRINT.
```

---

## PHỤ LỤC C — NGUỒN THAM KHẢO (đã kiểm tra 23/11/2026)

**Thư viện & dịch vụ**
* vnstock trên PyPI (trạng thái quarantine, giấy phép): https://pypi.org/project/vnstock/
* Ví dụ dự án gỡ vnstock sau quarantine: https://github.com/saladb4o/data-lake/pull/25 · https://github.com/lou1sxluv2302/vn-market-elt/pull/56
* Danh sách model Gemini: https://ai.google.dev/gemini-api/docs/models
* Giá & free tier Gemini: https://ai.google.dev/gemini-api/docs/pricing · Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits
* edge-tts: https://pypi.org/project/edge-tts/ · https://github.com/rany2/edge-tts
* APScheduler (3.x stable, 4.0 pre-release): https://github.com/agronholm/apscheduler
* pywebview: https://pywebview.flowrl.com/
* SSI FastConnect Data: https://guide.ssi.com.vn/ssi-products/fastconnect-data
* Tham khảo endpoint công khai Vietcap (tài liệu reverse-engineer, không chính thức): https://chipheo00.github.io/wealth-vn/docs/development/vn-market/vn-market-api-specs

**Avatar**
* HeyGen API (Photo Avatar, v3): https://developers.heygen.com/photo-avatar.md
* fal.ai Kling AI Avatar v2: https://fal.ai/models/fal-ai/kling-video/ai-avatar/v2/standard · https://fal.ai/models/fal-ai/kling-video/ai-avatar/v2/pro
* fal.ai OmniHuman: https://fal.ai/models/fal-ai/bytedance/omnihuman
* Hedra – HeyGen Photo Avatar 4: https://www.hedra.com/models/video/heygen/photo-avatar-4

**Nền tảng**
* YouTube `videos.insert`: https://developers.google.com/youtube/v3/docs/videos/insert
* YouTube chính sách kiếm tiền (nội dung không chân thực): https://support.google.com/youtube/answer/1311392
* TikTok Direct Post: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post · Hướng dẫn chia sẻ nội dung: https://developers.tiktok.com/doc/content-sharing-guidelines
* Facebook Reels Publishing API: https://developers.facebook.com/docs/video-api/guides/reels-publishing
* Telegram Bot API `sendVideo`: https://core.telegram.org/bots/api#sendvideo

**Pháp lý**
* Luật Trí tuệ nhân tạo 134/2025/QH15: https://english.luatvietnam.vn/law-no-134-2025-qh15-dated-december-10-2025-of-the-national-assembly-on-artificial-intelligence-422299-doc1.html
* Tóm tắt nghĩa vụ gắn nhãn (Rajah & Tann): https://www.rajahtannasia.com/viewpoints/new-law-on-artificial-intelligence-takes-effect-on-1-march-2026/

**RSS**
* CafeF: https://cafef.vn/thi-truong-chung-khoan.rss · Vietstock: https://vietstock.vn/830/chung-khoan/co-phieu.rss · VnEconomy: https://vneconomy.vn/chung-khoan.rss
