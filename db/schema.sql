-- 숙명 메이커스페이스 AI 코파일럿 — 자체 예약 DB
-- SQLite (개발) / PostgreSQL (운영) 호환 DDL

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─────────────────────────────────────────
-- 1. slots: 예약 가능한 슬롯 (오늘~7일)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS slots (
    slot_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_date   TEXT NOT NULL,          -- YYYY-MM-DD
    slot_hour   INTEGER NOT NULL        -- 11, 13, 15, 17 only (enum)
                CHECK(slot_hour IN (11, 13, 15, 17)),
    machine_no  INTEGER NOT NULL        -- 장비 번호 (1, 2, 3)
                CHECK(machine_no IN (1, 2, 3)),
    capacity    INTEGER NOT NULL DEFAULT 1,  -- 슬롯당 정원 (1대 = 1인)
    is_active   INTEGER NOT NULL DEFAULT 1,  -- 0 = 비활성(공휴일 등)
    UNIQUE(slot_date, slot_hour, machine_no)
);

-- ─────────────────────────────────────────
-- 2. reservations: 확정 예약
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id         INTEGER NOT NULL REFERENCES slots(slot_id),
    student_name    TEXT NOT NULL,       -- 학생 이름 (학번 저장 안 함)
    email           TEXT NOT NULL,       -- 알림용 이메일
    status          TEXT NOT NULL DEFAULT 'confirmed'
                    CHECK(status IN ('confirmed', 'cancelled')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    cancelled_at    TEXT                 -- NULL이면 취소 안 됨
);

-- ─────────────────────────────────────────
-- 3. waitlist: 대기열 (슬롯 만석 시)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS waitlist (
    waitlist_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id         INTEGER NOT NULL REFERENCES slots(slot_id),
    student_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'waiting'
                    CHECK(status IN ('waiting', 'assigned', 'expired')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    assigned_at     TEXT                 -- 자동 배정 완료 시각
);

-- ─────────────────────────────────────────
-- 4. logs: 모든 이벤트 append-only 로그
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS logs (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT NOT NULL,           -- reservation, cancellation, waitlist, assignment, email
    entity_id   INTEGER,                 -- reservation_id or waitlist_id
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_reservations_slot   ON reservations(slot_id, status);
CREATE INDEX IF NOT EXISTS idx_waitlist_slot_status ON waitlist(slot_id, status);
CREATE INDEX IF NOT EXISTS idx_slots_date_hour     ON slots(slot_date, slot_hour);
