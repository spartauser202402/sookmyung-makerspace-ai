"""
tests/test_reservation.py — A 예약 Tool 단위 테스트
"""
import sys
import os
import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import pytest

SCHEMA_PATH = ROOT / "db" / "schema.sql"


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """각 테스트마다 깨끗한 임시 DB 생성."""
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    tomorrow = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
    for hour in [11, 13, 15, 17]:
        for machine in [1, 2, 3]:
            conn.execute(
                "INSERT OR IGNORE INTO slots (slot_date, slot_hour, machine_no) VALUES (?,?,?)",
                (tomorrow, hour, machine),
            )
    conn.commit()
    conn.close()

    import db_utils
    monkeypatch.setattr(db_utils, "_DB_PATH", db_file)
    return str(db_file), tomorrow


# ── 1. 예약 성공 ────────────────────────────────────────────
def test_reservation_success(test_db):
    db_path, tomorrow = test_db
    from reservation_adapter import make_reservation
    result = make_reservation(
        target_date=tomorrow,
        target_hour=13,
        student_name="강채린",
        email="chaerin@test.com",
    )
    assert result["success"], f"예약 실패: {result['message']}"
    assert result["reservation_id"] is not None
    assert result["slot_date"] == tomorrow
    assert result["slot_hour"] == 13
    print(f"[PASS] 예약 성공: {result['message']}")


# ── 2. 만석 → 대기 등록 ─────────────────────────────────────
def test_waitlist_registration_when_full(test_db):
    db_path, tomorrow = test_db

    from reservation_adapter import make_reservation
    for i, name in enumerate(["학생A", "학생B", "학생C"]):
        r = make_reservation(
            target_date=tomorrow, target_hour=11,
            student_name=name, email=f"s{i}@test.com",
        )
        assert r["success"], f"사전 예약 실패: {r['message']}"

    overflow = make_reservation(
        target_date=tomorrow, target_hour=11,
        student_name="대기자D", email="d@test.com",
    )
    assert not overflow["success"]
    assert "만석" in overflow["message"]
    print(f"[PASS] 만석 감지: {overflow['message']}")

    from waitlist_db import add_to_waitlist
    w = add_to_waitlist(
        slot_date=tomorrow, slot_hour=11,
        student_name="대기자D", email="d@test.com",
    )
    assert w["success"], f"대기 등록 실패: {w['message']}"
    assert w["waitlist_id"] is not None
    print(f"[PASS] 대기 등록: {w['message']}")


# ── 3. 취소 → Monitor 감지 → 자동 배정 ──────────────────────
def test_cancel_then_auto_assign(test_db):
    db_path, tomorrow = test_db

    from reservation_adapter import make_reservation, cancel_reservation
    from waitlist_db import add_to_waitlist, get_active_waitlist
    from scheduler import check_and_assign_waitlist

    reservation_ids = []
    for i, name in enumerate(["학생A", "학생B", "학생C"]):
        r = make_reservation(
            target_date=tomorrow, target_hour=15,
            student_name=name, email=f"s{i}@test.com",
        )
        assert r["success"]
        reservation_ids.append(r["reservation_id"])

    w = add_to_waitlist(
        slot_date=tomorrow, slot_hour=15,
        student_name="대기자E", email="e@test.com",
    )
    assert w["success"]

    wl = get_active_waitlist()
    assert len(wl["entries"]) == 1
    print(f"[PASS] 대기 목록 확인: {wl['message']}")

    result_no_cancel = check_and_assign_waitlist()
    assert len(result_no_cancel["assignments"]) == 0
    print(f"[PASS] 취소 전 Monitor: {result_no_cancel['message']}")

    cancel_result = cancel_reservation(reservation_ids[0])
    assert cancel_result["success"], f"취소 실패: {cancel_result['message']}"
    print(f"[PASS] 취소 완료: {cancel_result['message']}")

    result_after = check_and_assign_waitlist()
    assert len(result_after["assignments"]) == 1
    assigned = result_after["assignments"][0]
    assert assigned["student_name"] == "대기자E"
    assert assigned["slot_date"] == tomorrow
    assert assigned["slot_hour"] == 15
    print(f"[PASS] 자동 배정: {result_after['message']}")


# ── 4. 시간표 파서 — 공강 슬롯 계산 ─────────────────────────
def test_timetable_parser_free_slots():
    from timetable_parser import parse_timetable_and_find_free_slots

    timetable = "운영체제 월 09:00-11:50 목 09:00-11:50\n자료구조 화 13:00-14:50"
    result = parse_timetable_and_find_free_slots(
        timetable_text=timetable,
        target_days="MON,TUE,WED,THU,FRI",
    )
    mon_11 = [s for s in result["free_slots"] if s["day"] == "MON" and s["hour"] == 11]
    assert not mon_11, "월 11시가 공강으로 잘못 분류됨"

    tue_13 = [s for s in result["free_slots"] if s["day"] == "TUE" and s["hour"] == 13]
    assert not tue_13, "화 13시가 공강으로 잘못 분류됨"

    wed_11 = [s for s in result["free_slots"] if s["day"] == "WED" and s["hour"] == 11]
    assert wed_11, "수 11시가 공강으로 감지되지 않음"

    print(f"[PASS] 시간표 파서: {result['message']}")
    print(f"       공강 슬롯 수: {len(result['free_slots'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
