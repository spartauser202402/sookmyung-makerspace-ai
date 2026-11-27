"""
seed.py — 오늘~7일치 슬롯 생성 + 일부 슬롯을 만석 처리

실행: python db/seed.py
"""
import sqlite3
import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "makerspace.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

SLOT_HOURS = [11, 13, 15, 17]
MACHINES = [1, 2, 3]  # 3D 프린터 3대

# 데모용: 꽉 찬 슬롯으로 만들 (slot_date, slot_hour, machine_no) 목록
# offset은 주말을 건너뛴 평일 기준 (3=월, 4=화, 5=수 등)
FULL_SLOTS = [
    # (날짜 offset, 시간, 장비) — 주말 건너뛴 첫 평일 기준
    (3, 11, 1),
    (3, 11, 2),
    (3, 11, 3),  # 첫 평일 11시 모든 장비 꽉 참
    (3, 13, 1),  # 첫 평일 13시 장비 1 꽉 참
    (4, 15, 1),  # 그 다음 평일 15시 장비 1 꽉 참
]


def init_db(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    print("[OK] Schema applied.")


def seed_slots(conn: sqlite3.Connection) -> None:
    today = date.today()
    inserted = 0
    for day_offset in range(1, 8):  # 내일~7일 후 (당일 제외)
        d = today + timedelta(days=day_offset)
        # 주말 제외
        if d.weekday() >= 5:
            continue
        date_str = d.strftime("%Y-%m-%d")
        for hour in SLOT_HOURS:
            for machine in MACHINES:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO slots (slot_date, slot_hour, machine_no) VALUES (?,?,?)",
                        (date_str, hour, machine),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass
    conn.commit()
    print(f"[OK] Slots seeded: {inserted} rows (weekdays only, 1~7 days ahead).")


def seed_full_slots(conn: sqlite3.Connection) -> None:
    """일부 슬롯에 예약을 채워서 만석으로 만든다."""
    today = date.today()
    filled = 0
    for day_offset, hour, machine in FULL_SLOTS:
        d = today + timedelta(days=day_offset)
        date_str = d.strftime("%Y-%m-%d")
        row = conn.execute(
            "SELECT slot_id FROM slots WHERE slot_date=? AND slot_hour=? AND machine_no=?",
            (date_str, hour, machine),
        ).fetchone()
        if row is None:
            continue
        slot_id = row[0]
        # 이미 예약된 경우 스킵
        existing = conn.execute(
            "SELECT COUNT(*) FROM reservations WHERE slot_id=? AND status='confirmed'",
            (slot_id,),
        ).fetchone()[0]
        if existing >= 1:
            continue
        conn.execute(
            """INSERT INTO reservations (slot_id, student_name, email)
               VALUES (?, '더미학생', 'dummy@sookmyung.ac.kr')""",
            (slot_id,),
        )
        conn.execute(
            "INSERT INTO logs (event_type, description) VALUES ('reservation', ?)",
            (f"seed: slot_id={slot_id} ({date_str} {hour}시 장비{machine}) 만석 처리",),
        )
        filled += 1
    conn.commit()
    print(f"[OK] Full-slot reservations seeded: {filled} slots made full.")


def print_summary(conn: sqlite3.Connection) -> None:
    slots_total = conn.execute("SELECT COUNT(*) FROM slots").fetchone()[0]
    reservations_total = conn.execute(
        "SELECT COUNT(*) FROM reservations WHERE status='confirmed'"
    ).fetchone()[0]
    print(f"\nSummary:")
    print(f"   Total slots     : {slots_total}")
    print(f"   Full slots      : {reservations_total}")
    print(f"   Available slots : {slots_total - reservations_total}")
    print(f"   DB path         : {DB_PATH}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        init_db(conn)
        seed_slots(conn)
        seed_full_slots(conn)
        print_summary(conn)
    finally:
        conn.close()
    print("\nSeed complete. Run `python db/seed.py` again to reset (idempotent).")
