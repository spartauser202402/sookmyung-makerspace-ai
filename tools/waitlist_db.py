"""
waitlist_db.py — 대기열 등록 / 조회 / 상태 업데이트
학번/비밀번호를 절대 받거나 저장하지 않음.
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from db_utils import get_connection


@tool(permission=ToolPermission.WRITE_ONLY)
def add_to_waitlist(
    slot_date: str,
    slot_hour: int,
    student_name: str,
    email: str,
) -> dict:
    """만석 슬롯의 대기열에 등록합니다.

    Args:
        slot_date (str): 대기할 날짜 (YYYY-MM-DD).
        slot_hour (int): 대기할 시간 (11, 13, 15, 17 중 하나).
        student_name (str): 대기자 이름.
        email (str): 알림 수신 이메일.
    Returns:
        dict: success(bool), waitlist_id(int|None), message(str).
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT slot_id FROM slots WHERE slot_date=? AND slot_hour=? LIMIT 1",
            (slot_date, slot_hour),
        ).fetchone()
        if row is None:
            return {"success": False, "waitlist_id": None,
                    "message": f"{slot_date} {slot_hour}시 슬롯이 존재하지 않습니다."}
        slot_id = row["slot_id"]
        existing = conn.execute(
            "SELECT waitlist_id FROM waitlist WHERE slot_id=? AND email=? AND status='waiting'",
            (slot_id, email),
        ).fetchone()
        if existing:
            return {"success": False, "waitlist_id": existing["waitlist_id"],
                    "message": f"이미 해당 슬롯 대기열에 등록되어 있습니다 (대기번호 {existing['waitlist_id']})."}
        cur = conn.execute(
            "INSERT INTO waitlist (slot_id, student_name, email) VALUES (?,?,?)",
            (slot_id, student_name, email),
        )
        wid = cur.lastrowid
        conn.execute(
            "INSERT INTO logs (event_type, entity_id, description) VALUES ('waitlist', ?, ?)",
            (wid, f"{student_name} -> {slot_date} {slot_hour}시 대기"),
        )
        conn.commit()
        return {"success": True, "waitlist_id": wid,
                "message": (f"대기 등록 완료! 대기번호 {wid}. "
                            f"취소 발생 시 자동으로 배정되며 이메일({email})로 알려드립니다.")}
    finally:
        conn.close()


@tool(permission=ToolPermission.READ_ONLY)
def get_active_waitlist() -> dict:
    """현재 'waiting' 상태인 모든 대기 항목을 조회합니다 (Monitor용).

    Returns:
        dict: entries(list of waitlist dicts), message(str).
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT w.waitlist_id, w.slot_id, s.slot_date, s.slot_hour,
                   s.machine_no, w.student_name, w.email, w.status, w.created_at
            FROM waitlist w JOIN slots s ON w.slot_id = s.slot_id
            WHERE w.status = 'waiting'
            ORDER BY w.created_at ASC
            """
        ).fetchall()
        entries = [dict(r) for r in rows]
        return {"entries": entries, "message": f"활성 대기 항목 {len(entries)}건"}
    finally:
        conn.close()


@tool(permission=ToolPermission.WRITE_ONLY)
def assign_waitlist_entry(waitlist_id: int, reservation_id: int) -> dict:
    """대기자를 'assigned' 상태로 업데이트합니다 (Monitor가 자동 배정 후 호출).

    Args:
        waitlist_id (int): 처리할 대기번호.
        reservation_id (int): 생성된 예약번호.
    Returns:
        dict: success(bool), waitlist_id(int), message(str).
    """
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE waitlist SET status='assigned', assigned_at=datetime('now','localtime') WHERE waitlist_id=?",
            (waitlist_id,),
        )
        conn.execute(
            "INSERT INTO logs (event_type, entity_id, description) VALUES ('assignment', ?, ?)",
            (waitlist_id, f"대기 {waitlist_id} -> 예약 {reservation_id} 자동 배정"),
        )
        conn.commit()
        return {"success": True, "waitlist_id": waitlist_id,
                "message": f"대기번호 {waitlist_id}가 예약번호 {reservation_id}로 자동 배정 완료."}
    finally:
        conn.close()
