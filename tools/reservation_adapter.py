"""
reservation_adapter.py — 예약 시도 / 취소 / 조회

Adapter 패턴: 현재는 SQLite 자체 DB를 백엔드로 사용.
나중에 학교 실제 시스템으로 교체 시 이 파일만 바꾸면 됨.
학번/비밀번호를 절대 받거나 저장하지 않음.
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from db_utils import get_connection

VALID_HOURS = [11, 13, 15, 17]


@tool(permission=ToolPermission.READ_ONLY)
def check_available_slots(
    target_date: str,
    target_hour: int,
) -> dict:
    """특정 날짜·시간의 예약 가능한 3D 프린터 슬롯을 조회합니다.

    Args:
        target_date (str): 조회할 날짜 (YYYY-MM-DD 형식, 예: 2026-11-30).
        target_hour (int): 조회할 시간 (11, 13, 15, 17 중 하나).
    Returns:
        dict: slots(list of slot dicts), message(str).
    """
    if target_hour not in VALID_HOURS:
        return {"slots": [], "message": "유효하지 않은 시간입니다. 11/13/15/17시 중 선택하세요."}
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT s.slot_id, s.slot_date, s.slot_hour, s.machine_no, s.capacity,
                   COUNT(r.reservation_id) AS confirmed_count
            FROM slots s
            LEFT JOIN reservations r
                   ON r.slot_id = s.slot_id AND r.status = 'confirmed'
            WHERE s.slot_date = ? AND s.slot_hour = ? AND s.is_active = 1
            GROUP BY s.slot_id
            """,
            (target_date, target_hour),
        ).fetchall()

        slots = [
            {
                "slot_id": row["slot_id"],
                "slot_date": row["slot_date"],
                "slot_hour": row["slot_hour"],
                "machine_no": row["machine_no"],
                "is_available": row["confirmed_count"] < row["capacity"],
                "confirmed_count": row["confirmed_count"],
            }
            for row in rows
        ]
        available = [s for s in slots if s["is_available"]]
        msg = (
            f"{target_date} {target_hour}시: "
            f"전체 {len(slots)}대 중 {len(available)}대 예약 가능."
            if slots
            else f"{target_date} {target_hour}시 슬롯이 없습니다."
        )
        return {"slots": slots, "message": msg}
    finally:
        conn.close()


@tool(permission=ToolPermission.WRITE_ONLY)
def make_reservation(
    target_date: str,
    target_hour: int,
    student_name: str,
    email: str,
) -> dict:
    """메이커스페이스 3D 프린터를 예약합니다.

    Args:
        target_date (str): 예약 날짜 (YYYY-MM-DD 형식, 예: 2026-11-30).
        target_hour (int): 예약 시간 (11, 13, 15, 17 중 하나).
        student_name (str): 예약자 이름 (학번 아님).
        email (str): 알림 수신 이메일 주소.
    Returns:
        dict: success(bool), reservation_id(int|None), slot_id(int|None),
              slot_date(str|None), slot_hour(int|None), machine_no(int|None), message(str).
    """
    if target_hour not in VALID_HOURS:
        return {"success": False, "reservation_id": None, "slot_id": None,
                "slot_date": None, "slot_hour": None, "machine_no": None,
                "message": "유효하지 않은 시간입니다. 11/13/15/17시 중 선택하세요."}

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT s.slot_id, s.machine_no, COUNT(r.reservation_id) AS cnt
            FROM slots s
            LEFT JOIN reservations r
                   ON r.slot_id = s.slot_id AND r.status = 'confirmed'
            WHERE s.slot_date = ? AND s.slot_hour = ? AND s.is_active = 1
            GROUP BY s.slot_id
            HAVING cnt < s.capacity
            ORDER BY s.machine_no ASC
            LIMIT 1
            """,
            (target_date, target_hour),
        ).fetchone()

        if row is None:
            return {"success": False, "reservation_id": None, "slot_id": None,
                    "slot_date": target_date, "slot_hour": target_hour, "machine_no": None,
                    "message": f"{target_date} {target_hour}시는 모든 장비가 만석입니다. 대기열에 등록해 드릴까요?"}

        slot_id = row["slot_id"]
        machine_no = row["machine_no"]
        cur = conn.execute(
            "INSERT INTO reservations (slot_id, student_name, email) VALUES (?,?,?)",
            (slot_id, student_name, email),
        )
        reservation_id = cur.lastrowid
        conn.execute(
            "INSERT INTO logs (event_type, entity_id, description) VALUES ('reservation', ?, ?)",
            (reservation_id, f"{student_name} -> {target_date} {target_hour}시 장비{machine_no}"),
        )
        conn.commit()
        return {
            "success": True,
            "reservation_id": reservation_id,
            "slot_id": slot_id,
            "slot_date": target_date,
            "slot_hour": target_hour,
            "machine_no": machine_no,
            "message": (
                f"예약 완료! {target_date} {target_hour}시 장비 {machine_no}번 "
                f"(예약번호 {reservation_id}). 반드시 .gcode 파일을 "
                f"makerspace@sookmyung.ac.kr로 전송해 주세요."
            ),
        }
    finally:
        conn.close()


@tool(permission=ToolPermission.WRITE_ONLY)
def cancel_reservation(reservation_id: int) -> dict:
    """예약을 취소합니다. 단, 당일 취소는 불가합니다.

    Args:
        reservation_id (int): 취소할 예약 번호.
    Returns:
        dict: success(bool), reservation_id(int), slot_id(int|None),
              slot_date(str|None), slot_hour(int|None), machine_no(int|None), message(str).
    """
    from datetime import date as _date
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT r.reservation_id, r.status, r.slot_id,
                   s.slot_date, s.slot_hour, s.machine_no
            FROM reservations r JOIN slots s ON r.slot_id = s.slot_id
            WHERE r.reservation_id = ?
            """,
            (reservation_id,),
        ).fetchone()
        if row is None:
            return {"success": False, "reservation_id": reservation_id, "slot_id": None,
                    "slot_date": None, "slot_hour": None, "machine_no": None,
                    "message": f"예약번호 {reservation_id}를 찾을 수 없습니다."}
        if row["status"] == "cancelled":
            return {"success": False, "reservation_id": reservation_id,
                    "slot_id": row["slot_id"], "slot_date": row["slot_date"],
                    "slot_hour": row["slot_hour"], "machine_no": row["machine_no"],
                    "message": "이미 취소된 예약입니다."}
        if row["slot_date"] == str(_date.today()):
            return {"success": False, "reservation_id": reservation_id,
                    "slot_id": row["slot_id"], "slot_date": row["slot_date"],
                    "slot_hour": row["slot_hour"], "machine_no": row["machine_no"],
                    "message": "당일 취소는 불가합니다 (이용수칙 3조)."}
        conn.execute(
            "UPDATE reservations SET status='cancelled', cancelled_at=datetime('now','localtime') WHERE reservation_id=?",
            (reservation_id,),
        )
        conn.execute(
            "INSERT INTO logs (event_type, entity_id, description) VALUES ('cancellation', ?, ?)",
            (reservation_id, f"예약 {reservation_id} 취소됨"),
        )
        conn.commit()
        return {"success": True, "reservation_id": reservation_id,
                "slot_id": row["slot_id"], "slot_date": row["slot_date"],
                "slot_hour": row["slot_hour"], "machine_no": row["machine_no"],
                "message": f"예약번호 {reservation_id} 취소 완료."}
    finally:
        conn.close()
