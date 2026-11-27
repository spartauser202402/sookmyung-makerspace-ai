"""
gcode_validator.py — .gcode 형식 + 3DWOX1 슬라이싱 여부 검사

이용수칙: .gcode만 접수. 다른 형식은 거절 + 3DWOX1 안내.
"""
from __future__ import annotations

from pydantic import BaseModel
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

ACCEPTED_EXT = ".gcode"
REJECTED_EXTS = {
    ".stl": "STL 파일은 3DWOX1 슬라이서에서 .gcode로 변환 후 제출해야 합니다.",
    ".obj": "OBJ 파일은 3DWOX1 슬라이서에서 .gcode로 변환 후 제출해야 합니다.",
    ".3mf": "3MF 파일은 3DWOX1 슬라이서에서 .gcode로 변환 후 제출해야 합니다.",
    ".amf": "AMF 파일은 3DWOX1 슬라이서에서 .gcode로 변환 후 제출해야 합니다.",
    ".step": "STEP 파일은 먼저 STL로 변환 후, 3DWOX1에서 .gcode로 슬라이싱하세요.",
    ".stp":  "STP 파일은 먼저 STL로 변환 후, 3DWOX1에서 .gcode로 슬라이싱하세요.",
}

CONVERSION_GUIDE = """
[3DWOX1 슬라이싱 방법]
1. 신도리코 3DWOX1 프로그램을 PC에 설치합니다.
   다운로드: https://www.sindoh.com/product/productMajorSoftware.do
2. 프로그램을 실행하고 STL 파일을 불러옵니다 (파일 > 열기).
3. 왼쪽 설정 패널에서 필라멘트를 'PLA'로 선택합니다.
4. '슬라이싱' 버튼을 클릭합니다.
5. '저장' 버튼으로 .gcode 파일을 저장합니다.
6. 파일명을 '출력날짜_시간_이름.gcode' 형식으로 변경합니다.
   예: 20261130_13_강채린.gcode
7. makerspace@sookmyung.ac.kr 로 전송합니다.
"""


class GcodeValidationResult(BaseModel):
    is_valid: bool
    filename: str
    detected_extension: str
    message: str
    conversion_guide: str


@tool(permission=ToolPermission.READ_ONLY)
def validate_gcode_file(filename: str) -> GcodeValidationResult:
    """.gcode 파일 형식 및 명명 규칙을 검사합니다.

    Args:
        filename (str): 검사할 파일명 (예: test.gcode, model.stl).
    Returns:
        GcodeValidationResult: 유효성 검사 결과와 안내 메시지.
    """
    lower = filename.strip().lower()
    # 확장자 추출
    if "." in lower:
        ext = "." + lower.rsplit(".", 1)[-1]
    else:
        ext = ""

    if ext == ACCEPTED_EXT:
        return GcodeValidationResult(
            is_valid=True,
            filename=filename,
            detected_extension=ext,
            message=f"'{filename}'은 올바른 .gcode 형식입니다. 출력 접수가 가능합니다.",
            conversion_guide="",
        )

    if ext in REJECTED_EXTS:
        reason = REJECTED_EXTS[ext]
        return GcodeValidationResult(
            is_valid=False,
            filename=filename,
            detected_extension=ext,
            message=(
                f"'{filename}'은 접수 불가 형식({ext})입니다.\n"
                f"{reason}\n"
                f"3DWOX1에서 .gcode로 변환 후 다시 제출해 주세요."
            ),
            conversion_guide=CONVERSION_GUIDE,
        )

    return GcodeValidationResult(
        is_valid=False,
        filename=filename,
        detected_extension=ext or "(없음)",
        message=(
            f"'{filename}'의 형식을 확인할 수 없습니다.\n"
            f"메이커스페이스는 .gcode 파일만 접수합니다.\n"
            f"3DWOX1 슬라이서로 변환 후 다시 제출해 주세요."
        ),
        conversion_guide=CONVERSION_GUIDE,
    )
