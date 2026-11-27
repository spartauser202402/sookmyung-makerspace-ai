"""
scheduler.py — 취소 감지 + 대기자 자동 배정 (Monitor Tool)
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from db_utils import get_connection


@tool(permission=ToolPermission.READ_WRITE)
def check_and_assign_waitlist() -> dict:
    """대기열을 순회하여 취소로 빈 슬롯에 대기자를 자동 배정합니다.

    Monitor Agent가 5~10분 간격으로 호출합니다.
    Returns:
        dict: assignments(list), checked_waitlist_count(int), message(str).
    """
    conn = get_connection()
    assignments = []
    try:
        waiting = conn.execute(
            """
            SELECT w.waitlist_id, w.slot_id, s.slot_date, s.slot_hour,
                   w.student_name, w.email
            FROM waitlist w JOIN slots s ON w.slot_id = s.slot_id
            WHERE w.status = 'waiting'
            ORDER BY w.created_at ASC
            """
        ).fetchall()

        processed_slots: set = set()

        for entry in waiting:
            slot_id = entry["slot_id"]
            if slot_id in processed_slots:
                continue

            free_slot = conn.execute(
                """
                SELECT s.slot_id, s.machine_no
                FROM slots s
                LEFT JOIN reservations r
                       ON r.slot_id = s.slot_id AND r.status = 'confirmed'
                WHERE s.slot_date = ? AND s.slot_hour = ? AND s.is_active = 1
                GROUP BY s.slot_id
                HAVING COUNT(r.reservation_id) < s.capacity
                ORDER BY s.machine_no ASC
                LIMIT 1
                """,
                (entry["slot_date"], entry["slot_hour"]),
            ).fetchone()

            if free_slot is None:
                continue

            cur = conn.execute(
                "INSERT INTO reservations (slot_id, student_name, email) VALUES (?,?,?)",
                (free_slot["slot_id"], entry["student_name"], entry["email"]),
            )
            reservation_id = cur.lastrowid

            conn.execute(
                "UPDATE waitlist SET status='assigned', assigned_at=datetime('now','localtime') WHERE waitlist_id=?",
                (entry["waitlist_id"],),
            )
            conn.execute(
                "INSERT INTO logs (event_type, entity_id, description) VALUES ('assignment', ?, ?)",
                (entry["waitlist_id"],
                 f"자동 배정: 대기{entry['waitlist_id']} -> 예약{reservation_id} ({entry['slot_date']} {entry['slot_hour']}시 장비{free_slot['machine_no']})"),
            )
            assignments.append({
                "waitlist_id": entry["waitlist_id"],
                "reservation_id": reservation_id,
                "student_name": entry["student_name"],
                "email": entry["email"],
                "slot_date": entry["slot_date"],
                "slot_hour": entry["slot_hour"],
                "machine_no": free_slot["machine_no"],
            })
            processed_slots.add(slot_id)

        conn.commit()

        if assignments:
            names = ", ".join(a["student_name"] for a in assignments)
            msg = f"{len(assignments)}명 자동 배정 완료: {names}"
        else:
            msg = f"대기 {len(waiting)}건 확인, 현재 배정 가능한 빈 자리 없음."

        return {"assignments": assignments, "checked_waitlist_count": len(waiting), "message": msg}
    finally:
        conn.close()
