"""
api/server.py — 프론트엔드용 REST API (FastAPI)

WxO에 등록하는 tools/*.py 함수를 그대로 재사용해 HTTP로 노출합니다.
ibm_watsonx_orchestrate ADK가 설치돼 있지 않으면 tests/mock_wxo의 stub을 사용합니다.

실행 (프로젝트 루트에서):
    pip install -r api/requirements.txt
    python db/seed.py
    uvicorn api.server:app --reload --port 8000
"""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

try:  # 실제 ADK가 있으면 그대로 사용
    import ibm_watsonx_orchestrate.agent_builder.tools  # noqa: F401
except ImportError:  # 없으면 로컬 stub
    sys.path.insert(0, str(ROOT / "tests"))
    import mock_wxo  # noqa: F401

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import reservation_adapter as ra
import waitlist_db as wl
import scheduler
import timetable_parser as tp
import gcode_validator as gv
import filename_builder as fb
import slicer_advisor as sa
import email_draft as ed
import idea_refiner as ir
import tool_recommender as tr
import model_search as ms
from db_utils import get_connection

KB_DIR = ROOT / "knowledge_base"

app = FastAPI(title="Sookmyung Makerspace AI Copilot API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _dump(result):
    """pydantic 모델이면 dict로, 아니면 그대로."""
    return result.model_dump() if hasattr(result, "model_dump") else result


def _db_guard(fn, *args, **kwargs):
    try:
        return _dump(fn(*args, **kwargs))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ───────────────────────── 예약 ─────────────────────────
class ReservationIn(BaseModel):
    target_date: str
    target_hour: int
    student_name: str = Field(min_length=1)
    email: str = Field(min_length=3)


class WaitlistIn(BaseModel):
    slot_date: str
    slot_hour: int
    student_name: str = Field(min_length=1)
    email: str = Field(min_length=3)


class TimetableIn(BaseModel):
    timetable_text: str
    target_days: str = "MON,TUE,WED,THU,FRI"


@app.get("/api/health")
def health():
    return {"ok": True, "db": (ROOT / "db" / "makerspace.db").exists()}


@app.get("/api/slots/overview")
def slots_overview(days: int = 7):
    """오늘~N일 슬롯 현황 (날짜 × 시간 그리드용)."""
    start = date.today()
    end = start + timedelta(days=days)
    try:
        conn = get_connection()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        rows = conn.execute(
            """
            SELECT s.slot_date, s.slot_hour,
                   COUNT(DISTINCT s.slot_id) AS machines,
                   SUM(CASE WHEN rc.cnt >= s.capacity THEN 1 ELSE 0 END) AS full_machines,
                   (SELECT COUNT(*) FROM waitlist w JOIN slots s2 ON w.slot_id = s2.slot_id
                     WHERE s2.slot_date = s.slot_date AND s2.slot_hour = s.slot_hour
                       AND w.status = 'waiting') AS waiting
            FROM slots s
            LEFT JOIN (SELECT slot_id, COUNT(*) AS cnt FROM reservations
                       WHERE status='confirmed' GROUP BY slot_id) rc
                   ON rc.slot_id = s.slot_id
            WHERE s.is_active = 1 AND s.slot_date >= ? AND s.slot_date <= ?
            GROUP BY s.slot_date, s.slot_hour
            ORDER BY s.slot_date, s.slot_hour
            """,
            (str(start), str(end)),
        ).fetchall()
        cells = [
            {
                "slot_date": r["slot_date"],
                "slot_hour": r["slot_hour"],
                "machines": r["machines"],
                "available": r["machines"] - (r["full_machines"] or 0),
                "waiting": r["waiting"],
            }
            for r in rows
        ]
        return {"hours": ra.VALID_HOURS, "cells": cells}
    finally:
        conn.close()


@app.get("/api/slots")
def check_slots(target_date: str, target_hour: int):
    return _db_guard(ra.check_available_slots, target_date, target_hour)


@app.post("/api/reservations")
def make_reservation(body: ReservationIn):
    return _db_guard(ra.make_reservation, body.target_date, body.target_hour,
                     body.student_name, body.email)


@app.delete("/api/reservations/{reservation_id}")
def cancel_reservation(reservation_id: int):
    return _db_guard(ra.cancel_reservation, reservation_id)


@app.get("/api/reservations")
def list_reservations(email: str):
    """이메일로 본인 예약 조회 (학번은 사용하지 않음)."""
    try:
        conn = get_connection()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        res = conn.execute(
            """
            SELECT r.reservation_id, r.status, r.student_name, r.created_at,
                   s.slot_date, s.slot_hour, s.machine_no
            FROM reservations r JOIN slots s ON r.slot_id = s.slot_id
            WHERE r.email = ? ORDER BY s.slot_date, s.slot_hour
            """,
            (email,),
        ).fetchall()
        wait = conn.execute(
            """
            SELECT w.waitlist_id, w.status, w.created_at, s.slot_date, s.slot_hour
            FROM waitlist w JOIN slots s ON w.slot_id = s.slot_id
            WHERE w.email = ? ORDER BY s.slot_date, s.slot_hour
            """,
            (email,),
        ).fetchall()
        return {"reservations": [dict(r) for r in res], "waitlist": [dict(w) for w in wait]}
    finally:
        conn.close()


@app.post("/api/waitlist")
def add_waitlist(body: WaitlistIn):
    return _db_guard(wl.add_to_waitlist, body.slot_date, body.slot_hour,
                     body.student_name, body.email)


@app.get("/api/waitlist")
def active_waitlist():
    return _db_guard(wl.get_active_waitlist)


@app.post("/api/waitlist/assign")
def run_assignment():
    return _db_guard(scheduler.check_and_assign_waitlist)


@app.post("/api/timetable/free-slots")
def free_slots(body: TimetableIn):
    return _dump(tp.parse_timetable_and_find_free_slots(body.timetable_text, body.target_days))


# ───────────────────────── 출력 준비 ─────────────────────────
class FilenameIn(BaseModel):
    print_date: str
    print_hour: int
    student_name: str


class SlicerIn(BaseModel):
    print_purpose: str = "일반"
    has_overhang: bool = False


class EmailDraftIn(BaseModel):
    student_name: str
    print_date: str
    print_hour: int
    gcode_filename: str
    reservation_id: int = 0
    special_requests: str = ""


@app.get("/api/gcode/validate")
def validate_gcode(filename: str):
    return _dump(gv.validate_gcode_file(filename))


@app.get("/api/filename/check")
def check_filename(filename: str):
    return _dump(fb.check_filename_format(filename))


@app.post("/api/filename/build")
def build_filename(body: FilenameIn):
    return _dump(fb.build_gcode_filename(body.print_date, body.print_hour, body.student_name))


@app.post("/api/slicer/recommend")
def slicer(body: SlicerIn):
    return _dump(sa.recommend_slicer_settings(body.print_purpose, body.has_overhang))


@app.post("/api/email/draft")
def email_draft(body: EmailDraftIn):
    return _dump(ed.draft_print_request_email(
        body.student_name, body.print_date, body.print_hour, body.gcode_filename,
        body.reservation_id, body.special_requests,
    ))


# ───────────────────────── 아이디어 → 모델 ─────────────────────────
class IdeaIn(BaseModel):
    idea_description: str
    estimated_size_cm: str = "미정"
    primary_function: str = "장식/소품"


@app.post("/api/idea/refine")
def refine_idea(body: IdeaIn):
    return _dump(ir.refine_idea_to_requirements(
        body.idea_description, body.estimated_size_cm, body.primary_function))


@app.get("/api/cad/recommend")
def cad(user_level: str = "초보", primary_use: str = "소품"):
    return _dump(tr.recommend_cad_tool(user_level, primary_use))


@app.get("/api/models/search")
def models(query: str, max_results: int = 5):
    return _dump(ms.search_open_models(query, max_results))


# ───────────────────────── 지식베이스 ─────────────────────────
@app.get("/api/kb")
def kb_list():
    docs = sorted(p.stem for p in KB_DIR.glob("*.md"))
    return {"documents": docs}


@app.get("/api/kb/{name}")
def kb_doc(name: str):
    path = (KB_DIR / f"{name}.md").resolve()
    if path.parent != KB_DIR.resolve() or not path.exists():
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    return {"name": name, "content": path.read_text(encoding="utf-8")}


@app.get("/api/kb-search")
def kb_search(q: str, limit: Optional[int] = 8):
    """간단한 키워드 검색 (WxO RAG 없이 로컬에서 쓰는 폴백)."""
    terms = [t for t in q.lower().split() if t]
    hits = []
    for p in sorted(KB_DIR.glob("*.md")):
        # '## ' 헤딩 단위로 섹션 분할
        sections = re.split(r"\n(?=##\s)", p.read_text(encoding="utf-8"))
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            text = sec.lower()
            score = sum(text.count(t) for t in terms)
            if score:
                title = sec.splitlines()[0].lstrip("# ").strip()
                hits.append({"document": p.stem, "section": title,
                             "snippet": sec[:800], "score": score})
    hits.sort(key=lambda h: -h["score"])
    return {"query": q, "results": hits[:limit]}
