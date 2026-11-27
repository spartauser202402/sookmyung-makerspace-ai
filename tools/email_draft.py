"""
email_draft.py — 출력 요청 메일 초안 생성

makerspace@sookmyung.ac.kr 수신용 초안만 생성 (실제 발송 X).
"""
from __future__ import annotations

from pydantic import BaseModel
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

MAKERSPACE_EMAIL = "makerspace@sookmyung.ac.kr"


class EmailDraftResult(BaseModel):
    to: str
    subject: str
    body: str
    filename_reminder: str
    message: str


@tool(permission=ToolPermission.READ_ONLY)
def draft_print_request_email(
    student_name: str,
    print_date: str,
    print_hour: int,
    gcode_filename: str,
    reservation_id: int = 0,
    special_requests: str = "",
) -> EmailDraftResult:
    """출력 요청 이메일 초안을 생성합니다. 실제 발송은 사용자가 직접 합니다.

    Args:
        student_name (str): 예약자 이름.
        print_date (str): 출력 날짜 (YYYY-MM-DD).
        print_hour (int): 출력 시간 (11, 13, 15, 17 중 하나).
        gcode_filename (str): 첨부할 .gcode 파일명 (출력날짜_시간_이름.gcode 형식).
        reservation_id (int): 예약 번호 (없으면 0).
        special_requests (str): 특이사항 (없으면 빈 문자열).
    Returns:
        EmailDraftResult: 완성된 이메일 초안.
    """
    subject = f"[3D 프린터 출력 요청] {print_date} {print_hour}시 — {student_name}"

    reservation_line = (
        f"예약번호: {reservation_id}\n" if reservation_id else ""
    )
    special_line = (
        f"\n특이사항: {special_requests}" if special_requests else ""
    )

    body = (
        f"안녕하세요, 숙명 메이커스페이스 담당자님.\n\n"
        f"3D 프린터 출력을 요청드립니다.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"신청자: {student_name}\n"
        f"출력 일시: {print_date} {print_hour}시\n"
        f"{reservation_line}"
        f"파일명: {gcode_filename}\n"
        f"필라멘트: PLA (고정){special_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"위 파일을 첨부하여 발송합니다.\n"
        f"감사합니다.\n{student_name} 드림"
    )

    return EmailDraftResult(
        to=MAKERSPACE_EMAIL,
        subject=subject,
        body=body,
        filename_reminder=(
            f"첨부 파일명 확인: '{gcode_filename}'\n"
            f"형식: 출력날짜_시간_이름.gcode (예: {print_date.replace('-','')}_{print_hour}_{student_name}.gcode)"
        ),
        message=(
            f"이메일 초안이 완성되었습니다.\n"
            f"수신: {MAKERSPACE_EMAIL}\n"
            f"제목: {subject}\n"
            f"본문과 .gcode 파일을 첨부하여 직접 발송해 주세요."
        ),
    )
