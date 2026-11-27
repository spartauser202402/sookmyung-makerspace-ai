"""
heyoung_timetable_sample.py — 헤이영 앱 시간표 샘플 데이터 제공 및 예약 대기 시스템 안내

헤이영 앱 시간표 형식 샘플을 제공하고, 공강 슬롯 분석 및
숙명창작소 3D 프린터 예약/대기 등록 흐름을 안내합니다.
"""
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


# 헤이영 앱 시간표 형식 샘플 데이터
HEYOUNG_TIMETABLE_SAMPLES = {
    "sample_1": {
        "description": "이공계 3학년 샘플 (월수금 집중)",
        "raw_text": (
            "알고리즘 월 09:00-10:50 수 09:00-10:50\n"
            "데이터베이스 월 13:00-14:50 목 13:00-14:50\n"
            "소프트웨어공학 화 11:00-12:50\n"
            "운영체제 수 11:00-12:50 금 11:00-12:50\n"
            "전공선택실험 목 15:00-17:50"
        ),
        "free_slots_hint": "화 15시·17시, 금 13시·15시·17시 등 공강 예상",
    },
    "sample_2": {
        "description": "인문계 2학년 샘플 (화목 집중)",
        "raw_text": (
            "영어회화 화 09:00-10:50 목 09:00-10:50\n"
            "경제학원론 화 13:00-14:50\n"
            "문화인류학 목 11:00-12:50\n"
            "글쓰기와표현 수 09:00-10:50\n"
            "심리학개론 금 13:00-14:50"
        ),
        "free_slots_hint": "월 전체, 수 11시·13시·15시·17시 공강 예상",
    },
    "sample_3": {
        "description": "경영학과 4학년 샘플 (가벼운 학기)",
        "raw_text": (
            "마케팅전략 월 11:00-12:50\n"
            "재무관리 수 13:00-14:50\n"
            "인턴십세미나 금 15:00-16:50"
        ),
        "free_slots_hint": "월 13시·15시·17시, 화 전체, 목 전체 공강 예상",
    },
}


@tool(permission=ToolPermission.READ_ONLY)
def get_heyoung_timetable_sample(
    sample_name: str = "sample_1",
) -> dict:
    """헤이영 앱 시간표 샘플 데이터를 반환합니다. 숙명창작소 예약에 활용하세요.

    Args:
        sample_name (str): 샘플 이름. 'sample_1'(이공계 3학년), 'sample_2'(인문계 2학년),
                           'sample_3'(경영 4학년) 중 선택. 기본값: 'sample_1'.
    Returns:
        dict: sample_name, description, raw_timetable_text, free_slots_hint,
              usage_guide, reservation_guide.
    """
    if sample_name not in HEYOUNG_TIMETABLE_SAMPLES:
        sample_name = "sample_1"

    s = HEYOUNG_TIMETABLE_SAMPLES[sample_name]

    usage_guide = (
        "📱 헤이영 앱에서 시간표를 복사하는 방법:\n"
        "1. 헤이영 앱 실행 → 하단 메뉴 '시간표' 탭\n"
        "2. 현재 학기 시간표 화면에서 '공유' 또는 '텍스트 복사' 선택\n"
        "3. 복사된 텍스트를 그대로 여기에 붙여넣기\n\n"
        "📋 지원 형식 예시:\n"
        "  '과목명 요일 HH:MM-HH:MM' 형식\n"
        "  예: '운영체제 월 09:00-11:50 목 09:00-11:50'"
    )

    reservation_guide = (
        "🏭 숙명창작소 3D 프린터 예약 순서:\n"
        "1. 이 샘플 시간표(또는 본인 시간표)를 parse_timetable_and_find_free_slots에 전달\n"
        "2. 공강 슬롯 확인 후 원하는 날짜·시간 선택 (11시/13시/15시/17시)\n"
        "3. check_available_slots로 예약 가능 여부 확인\n"
        "   ✅ 가능 → make_reservation으로 예약\n"
        "   ❌ 만석 → add_to_waitlist로 대기 등록 (자동 배정 시스템 작동)\n"
        "4. 예약/대기 완료 후 이메일 알림 자동 발송\n\n"
        "⏰ 예약 슬롯: 11시 / 13시 / 15시 / 17시 (각 2시간)\n"
        "🔧 필라멘트: PLA 단일\n"
        "📧 출력 파일: makerspace@sookmyung.ac.kr로 .gcode 파일 전송 필수"
    )

    return {
        "sample_name": sample_name,
        "description": s["description"],
        "raw_timetable_text": s["raw_text"],
        "free_slots_hint": s["free_slots_hint"],
        "usage_guide": usage_guide,
        "reservation_guide": reservation_guide,
    }


@tool(permission=ToolPermission.READ_ONLY)
def get_waitlist_system_guide() -> dict:
    """숙명창작소 3D 프린터 예약 대기 시스템 사용 방법을 안내합니다.

    Returns:
        dict: system_description, how_it_works(list), tools_to_use(list), example_scenario.
    """
    how_it_works = [
        "1️⃣  원하는 날짜·시간 슬롯이 만석인 경우, add_to_waitlist로 대기열에 등록합니다.",
        "2️⃣  대기 등록 시 이메일로 대기번호와 안내가 발송됩니다.",
        "3️⃣  기존 예약자가 취소하면 check_and_assign_waitlist가 자동으로 대기열을 순회합니다.",
        "4️⃣  빈 슬롯이 생기면 대기 등록 순서(선착순)대로 자동 예약이 배정됩니다.",
        "5️⃣  자동 배정 완료 시 등록한 이메일로 즉시 알림이 발송됩니다.",
        "6️⃣  모니터링 주기: 약 5~10분 간격으로 대기열 확인 및 자동 배정 실행.",
    ]

    tools_to_use = [
        "add_to_waitlist — 만석 슬롯 대기열 등록 (slot_date, slot_hour, student_name, email 필요)",
        "get_active_waitlist — 현재 대기 중인 전체 목록 조회 (모니터링용)",
        "check_and_assign_waitlist — 취소 발생 시 대기자 자동 배정 실행",
        "assign_waitlist_entry — 특정 대기자를 수동으로 배정 처리",
        "send_waitlist_registered_email — 대기 등록 완료 이메일 발송",
        "send_auto_assigned_email — 자동 배정 완료 이메일 발송",
    ]

    example_scenario = (
        "📌 예시 시나리오:\n\n"
        "학생 A: '2026-12-01 13시 예약하고 싶어'\n"
        "  → check_available_slots(2026-12-01, 13) → 만석!\n"
        "  → add_to_waitlist(2026-12-01, 13, '학생A', 'a@sookmyung.ac.kr')\n"
        "  → 대기번호 3번 등록 완료. 이메일 발송.\n\n"
        "5분 후, 기존 예약자 B가 cancel_reservation으로 예약 취소\n"
        "  → check_and_assign_waitlist() 자동 실행\n"
        "  → 대기번호 3번(학생 A)에게 자동 예약 배정\n"
        "  → send_auto_assigned_email로 학생 A에게 즉시 알림!\n\n"
        "🎉 학생 A는 아무것도 안 해도 자동으로 예약이 완료됩니다."
    )

    return {
        "system_description": (
            "숙명창작소 3D 프린터 예약 대기 시스템: 이미 예약이 꽉 찬 슬롯에 대기를 걸어두면, "
            "취소가 발생했을 때 자동으로 대기 순서대로 예약을 배정해주는 시스템입니다. "
            "학생이 계속 확인하지 않아도 취소 발생 시 자동으로 이메일로 통보됩니다."
        ),
        "how_it_works": how_it_works,
        "tools_to_use": tools_to_use,
        "example_scenario": example_scenario,
    }
