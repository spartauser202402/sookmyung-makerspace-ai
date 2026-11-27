"""
filename_builder.py — 파일명 규칙 자동 생성

이용수칙 규칙: 출력날짜_시간_이름.gcode
예: 20261130_13_강채린.gcode
"""
from __future__ import annotations

import re
from pydantic import BaseModel
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

VALID_HOURS = [11, 13, 15, 17]


class FilenameResult(BaseModel):
    filename: str
    is_valid: bool
    message: str


@tool(permission=ToolPermission.READ_ONLY)
def build_gcode_filename(
    print_date: str,
    print_hour: int,
    student_name: str,
) -> FilenameResult:
    """이용수칙에 맞는 .gcode 파일명을 자동 생성합니다.

    Args:
        print_date (str): 출력 날짜 (YYYY-MM-DD 형식, 예: 2026-11-30).
        print_hour (int): 출력 시간 (11, 13, 15, 17 중 하나).
        student_name (str): 예약자 이름 (예: 강채린).
    Returns:
        FilenameResult: 생성된 파일명과 유효성 메시지.
    """
    if print_hour not in VALID_HOURS:
        return FilenameResult(
            filename="",
            is_valid=False,
            message=f"유효하지 않은 시간입니다. 11/13/15/17시 중 선택하세요.",
        )

    # YYYY-MM-DD → YYYYMMDD
    date_compact = print_date.replace("-", "")
    if len(date_compact) != 8 or not date_compact.isdigit():
        return FilenameResult(
            filename="",
            is_valid=False,
            message=f"날짜 형식이 올바르지 않습니다. YYYY-MM-DD로 입력하세요.",
        )

    # 이름에서 특수문자 제거 (공백, 특수문자 → 빈 문자열)
    safe_name = re.sub(r"[^\w가-힣]", "", student_name)
    if not safe_name:
        return FilenameResult(
            filename="",
            is_valid=False,
            message="이름에 사용할 수 없는 문자만 있습니다.",
        )

    filename = f"{date_compact}_{print_hour}_{safe_name}.gcode"
    return FilenameResult(
        filename=filename,
        is_valid=True,
        message=(
            f"파일명 생성 완료: {filename}\n"
            f"makerspace@sookmyung.ac.kr 로 이 파일명으로 전송해 주세요."
        ),
    )


@tool(permission=ToolPermission.READ_ONLY)
def check_filename_format(filename: str) -> FilenameResult:
    """기존 .gcode 파일명이 이용수칙 형식(출력날짜_시간_이름.gcode)에 맞는지 확인합니다.

    Args:
        filename (str): 검사할 파일명 (예: 20261130_13_강채린.gcode).
    Returns:
        FilenameResult: 형식 검사 결과.
    """
    pattern = re.compile(r"^(\d{8})_(11|13|15|17)_(.+)\.gcode$", re.IGNORECASE)
    m = pattern.match(filename.strip())
    if m:
        date_part, hour_part, name_part = m.group(1), m.group(2), m.group(3)
        return FilenameResult(
            filename=filename,
            is_valid=True,
            message=(
                f"파일명 형식이 올바릅니다.\n"
                f"  날짜: {date_part[:4]}-{date_part[4:6]}-{date_part[6:]}\n"
                f"  시간: {hour_part}시\n"
                f"  이름: {name_part}"
            ),
        )
    return FilenameResult(
        filename=filename,
        is_valid=False,
        message=(
            f"파일명 형식이 올바르지 않습니다.\n"
            f"올바른 형식: 출력날짜_시간_이름.gcode\n"
            f"예시: 20261130_13_강채린.gcode"
        ),
    )
