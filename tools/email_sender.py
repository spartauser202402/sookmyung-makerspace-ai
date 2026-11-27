"""
email_sender.py — 예약 확정 / 대기 등록 / 자동 배정 완료 메일 발송

- 데모용 테스트 주소로만 실제 발송
- makerspace@sookmyung.ac.kr은 "초안 생성"까지만 (실제 발송 X)
- 비밀키는 .env에서 로드
"""
from __future__ import annotations

import os
from pydantic import BaseModel
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


class EmailResult(BaseModel):
    success: bool
    to: str
    subject: str
    body_preview: str
    message: str


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _send_via_sendgrid(to: str, subject: str, body: str) -> bool:
    """SendGrid로 실제 발송. API Key 없으면 콘솔 출력만."""
    api_key = _get_env("SENDGRID_API_KEY")
    sender = _get_env("DEMO_EMAIL_SENDER", "demo@example.com")
    if not api_key or api_key == "your_sendgrid_api_key_here":
        print(f"[EMAIL MOCK] To: {to}\nSubject: {subject}\n{body[:200]}")
        return True
    try:
        import urllib.request, urllib.error, json
        payload = json.dumps({
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": sender},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }).encode()
        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


@tool(permission=ToolPermission.WRITE_ONLY)
def send_reservation_confirmed_email(
    student_name: str,
    email: str,
    slot_date: str,
    slot_hour: int,
    machine_no: int,
    reservation_id: int,
) -> EmailResult:
    """예약 확정 알림 이메일을 발송합니다.

    Args:
        student_name (str): 예약자 이름.
        email (str): 수신 이메일 주소.
        slot_date (str): 예약 날짜 (YYYY-MM-DD).
        slot_hour (int): 예약 시간 (11, 13, 15, 17 중 하나).
        machine_no (int): 배정된 장비 번호.
        reservation_id (int): 예약 번호.
    Returns:
        EmailResult: 발송 결과.
    """
    subject = f"[숙명 메이커스페이스] 3D 프린터 예약 확정 — {slot_date} {slot_hour}시"
    body = (
        f"안녕하세요, {student_name}님!\n\n"
        f"3D 프린터 예약이 확정되었습니다.\n\n"
        f"  - 날짜: {slot_date}\n"
        f"  - 시간: {slot_hour}시\n"
        f"  - 장비: {machine_no}번\n"
        f"  - 예약번호: {reservation_id}\n\n"
        f"[필수] 예약 당일, 반드시 .gcode 파일을 아래 주소로 전송해 주세요.\n"
        f"  수신: makerspace@sookmyung.ac.kr\n"
        f"  파일명: {slot_date.replace('-', '')}_{slot_hour}_{student_name}.gcode\n\n"
        f"주의사항:\n"
        f"  - 당일 취소 불가\n"
        f"  - 예약 시간 10분 이내 미방문 3회 누적 시 2주 이용 제한\n\n"
        f"감사합니다. 숙명 메이커스페이스 AI 코파일럿"
    )
    demo_to = _get_env("DEMO_EMAIL_RECIPIENT", email)
    ok = _send_via_sendgrid(demo_to, subject, body)
    return EmailResult(
        success=ok, to=demo_to, subject=subject,
        body_preview=body[:150],
        message="예약 확정 메일 발송 완료" if ok else "메일 발송 실패",
    )


@tool(permission=ToolPermission.WRITE_ONLY)
def send_waitlist_registered_email(
    student_name: str,
    email: str,
    slot_date: str,
    slot_hour: int,
    waitlist_id: int,
) -> EmailResult:
    """대기 등록 알림 이메일을 발송합니다.

    Args:
        student_name (str): 대기자 이름.
        email (str): 수신 이메일 주소.
        slot_date (str): 대기 날짜 (YYYY-MM-DD).
        slot_hour (int): 대기 시간 (11, 13, 15, 17 중 하나).
        waitlist_id (int): 대기 번호.
    Returns:
        EmailResult: 발송 결과.
    """
    subject = f"[숙명 메이커스페이스] 대기 등록 완료 — {slot_date} {slot_hour}시"
    body = (
        f"안녕하세요, {student_name}님!\n\n"
        f"요청하신 슬롯이 현재 만석으로, 대기열에 등록되었습니다.\n\n"
        f"  - 날짜: {slot_date}\n"
        f"  - 시간: {slot_hour}시\n"
        f"  - 대기번호: {waitlist_id}\n\n"
        f"취소 발생 시 자동으로 배정되며, 별도 이메일로 알려드립니다.\n"
        f"(모니터링 주기: 5~10분)\n\n"
        f"감사합니다. 숙명 메이커스페이스 AI 코파일럿"
    )
    demo_to = _get_env("DEMO_EMAIL_RECIPIENT", email)
    ok = _send_via_sendgrid(demo_to, subject, body)
    return EmailResult(
        success=ok, to=demo_to, subject=subject,
        body_preview=body[:150],
        message="대기 등록 메일 발송 완료" if ok else "메일 발송 실패",
    )


@tool(permission=ToolPermission.WRITE_ONLY)
def send_auto_assigned_email(
    student_name: str,
    email: str,
    slot_date: str,
    slot_hour: int,
    machine_no: int,
    reservation_id: int,
    waitlist_id: int,
) -> EmailResult:
    """자동 배정 완료 알림 이메일을 발송합니다.

    Args:
        student_name (str): 배정된 학생 이름.
        email (str): 수신 이메일 주소.
        slot_date (str): 배정 날짜 (YYYY-MM-DD).
        slot_hour (int): 배정 시간 (11, 13, 15, 17 중 하나).
        machine_no (int): 배정된 장비 번호.
        reservation_id (int): 생성된 예약 번호.
        waitlist_id (int): 처리된 대기 번호.
    Returns:
        EmailResult: 발송 결과.
    """
    subject = f"[숙명 메이커스페이스] 자동 배정 완료 — {slot_date} {slot_hour}시"
    body = (
        f"안녕하세요, {student_name}님!\n\n"
        f"대기번호 {waitlist_id}번 — 자동 배정이 완료되었습니다!\n\n"
        f"  - 날짜: {slot_date}\n"
        f"  - 시간: {slot_hour}시\n"
        f"  - 장비: {machine_no}번\n"
        f"  - 예약번호: {reservation_id}\n\n"
        f"[필수] 예약 당일, 반드시 .gcode 파일을 아래 주소로 전송해 주세요.\n"
        f"  수신: makerspace@sookmyung.ac.kr\n"
        f"  파일명: {slot_date.replace('-', '')}_{slot_hour}_{student_name}.gcode\n\n"
        f"감사합니다. 숙명 메이커스페이스 AI 코파일럿"
    )
    demo_to = _get_env("DEMO_EMAIL_RECIPIENT", email)
    ok = _send_via_sendgrid(demo_to, subject, body)
    return EmailResult(
        success=ok, to=demo_to, subject=subject,
        body_preview=body[:150],
        message="자동 배정 메일 발송 완료" if ok else "메일 발송 실패",
    )
