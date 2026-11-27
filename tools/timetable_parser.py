"""
timetable_parser.py — 시간표 텍스트 -> 공강 슬롯 JSON
"""
from __future__ import annotations

import re
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

VALID_HOURS = [11, 13, 15, 17]

DAY_MAP = {
    "월": "MON", "화": "TUE", "수": "WED", "목": "THU", "금": "FRI",
    "MON": "MON", "TUE": "TUE", "WED": "WED", "THU": "THU", "FRI": "FRI",
    "MONDAY": "MON", "TUESDAY": "TUE", "WEDNESDAY": "WED",
    "THURSDAY": "THU", "FRIDAY": "FRI",
}

SLOT_RANGES = {
    11: (11, 0, 12, 50),
    13: (13, 0, 14, 50),
    15: (15, 0, 16, 50),
    17: (17, 0, 18, 50),
}


def _time_to_min(h: int, m: int) -> int:
    return h * 60 + m


def _overlaps(slot_hour: int, sh: int, sm: int, eh: int, em: int) -> bool:
    s_start, s_end = SLOT_RANGES[slot_hour][:2], SLOT_RANGES[slot_hour][2:]
    slot_s = _time_to_min(*s_start)
    slot_e = _time_to_min(*s_end)
    cls_s = _time_to_min(sh, sm)
    cls_e = _time_to_min(eh, em)
    return not (slot_e <= cls_s or slot_s >= cls_e)


def _parse_classes(timetable_text: str) -> dict:
    result: dict = {}
    pattern = re.compile(
        r"([월화수목금]|MON|TUE|WED|THU|FRI)\s*"
        r"(\d{1,2}):(\d{2})\s*[-~]\s*(\d{1,2}):(\d{2})",
        re.IGNORECASE,
    )
    for m in pattern.finditer(timetable_text.upper().replace("월", "MON")
                               .replace("화", "TUE").replace("수", "WED")
                               .replace("목", "THU").replace("금", "FRI")):
        raw_day = m.group(1).upper()
        day = DAY_MAP.get(raw_day)
        if day is None:
            continue
        sh, sm, eh, em = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        result.setdefault(day, []).append((sh, sm, eh, em))
    return result


@tool(permission=ToolPermission.READ_ONLY)
def parse_timetable_and_find_free_slots(
    timetable_text: str,
    target_days: str = "MON,TUE,WED,THU,FRI",
) -> dict:
    """시간표 텍스트를 파싱하여 메이커스페이스 예약 가능 공강 슬롯을 반환합니다.

    Args:
        timetable_text (str): 에타(everytime) 등에서 복사한 시간표 텍스트. 예: '운영체제 월 09:00-11:50 목 09:00-11:50'
        target_days (str): 확인할 요일 목록 (쉼표 구분). 기본값: 'MON,TUE,WED,THU,FRI'
    Returns:
        dict: free_slots(list of {day, hour}), busy_days(list), message(str).
    """
    classes = _parse_classes(timetable_text)
    days = [d.strip().upper() for d in target_days.split(",")]

    free_slots = []
    busy_days = []

    for day in days:
        day_classes = classes.get(day, [])
        if day_classes:
            busy_days.append(day)
        for slot_hour in VALID_HOURS:
            is_busy = any(
                _overlaps(slot_hour, sh, sm, eh, em) for sh, sm, eh, em in day_classes
            )
            if not is_busy:
                free_slots.append({"day": day, "hour": slot_hour})

    if not free_slots:
        msg = "모든 요청 요일에 수업이 있어 예약 가능한 공강 슬롯이 없습니다."
    else:
        slots_str = ", ".join(f"{s['day']} {s['hour']}시" for s in free_slots[:5])
        more = f" 외 {len(free_slots)-5}개" if len(free_slots) > 5 else ""
        msg = f"공강 슬롯 {len(free_slots)}개를 찾았습니다: {slots_str}{more}"

    return {"free_slots": free_slots, "busy_days": busy_days, "message": msg}
