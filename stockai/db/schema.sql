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
