"""
tests/test_print_prep.py — B 출력 준비 Tool 단위 테스트

시나리오:
  1. .gcode 파일 → 통과
  2. .stl 파일 → 거절 + 3DWOX1 안내
  3. 파일명 자동 생성
  4. 파일명 형식 검사 (올바름 / 잘못됨)
  5. 메일 초안 생성

실행: cd makerspace && python -m pytest tests/test_print_prep.py -v
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def test_gcode_accepted():
    from gcode_validator import validate_gcode_file
    result = validate_gcode_file("test.gcode")
    assert result.is_valid, f"gcode가 거절됨: {result.message}"
    print(f"[PASS] gcode 통과: {result.message}")


def test_stl_rejected_with_guide():
    from gcode_validator import validate_gcode_file
    result = validate_gcode_file("model.stl")
    assert not result.is_valid, "stl이 통과되면 안 됨"
    assert "3DWOX1" in result.message or "3DWOX1" in result.conversion_guide
    assert result.conversion_guide != ""
    print(f"[PASS] stl 거절 + 가이드 제공: {result.message[:60]}...")


def test_obj_rejected():
    from gcode_validator import validate_gcode_file
    result = validate_gcode_file("shape.obj")
    assert not result.is_valid
    print(f"[PASS] obj 거절: {result.message[:60]}...")


def test_filename_builder_valid():
    from filename_builder import build_gcode_filename
    result = build_gcode_filename(
        print_date="2026-11-30",
        print_hour=13,
        student_name="강채린",
    )
    assert result.is_valid, f"파일명 생성 실패: {result.message}"
    assert result.filename == "20261130_13_강채린.gcode"
    print(f"[PASS] 파일명 생성: {result.filename}")


def test_filename_builder_invalid_hour():
    from filename_builder import build_gcode_filename
    result = build_gcode_filename(
        print_date="2026-11-30",
        print_hour=14,  # 유효하지 않은 시간
        student_name="홍길동",
    )
    assert not result.is_valid
    print(f"[PASS] 잘못된 시간 거절: {result.message}")


def test_filename_format_check_valid():
    from filename_builder import check_filename_format
    result = check_filename_format("20261130_13_강채린.gcode")
    assert result.is_valid, f"유효한 파일명이 거절됨: {result.message}"
    print(f"[PASS] 파일명 형식 검사 통과: {result.message}")


def test_filename_format_check_invalid():
    from filename_builder import check_filename_format
    result = check_filename_format("my_model.gcode")
    assert not result.is_valid
    print(f"[PASS] 잘못된 파일명 거절: {result.message}")


def test_email_draft_generation():
    from email_draft import draft_print_request_email
    result = draft_print_request_email(
        student_name="강채린",
        print_date="2026-11-30",
        print_hour=13,
        gcode_filename="20261130_13_강채린.gcode",
        reservation_id=42,
    )
    assert result.to == "makerspace@sookmyung.ac.kr"
    assert "강채린" in result.body
    assert "20261130_13_강채린.gcode" in result.body
    assert "PLA" in result.body
    print(f"[PASS] 메일 초안 생성: To={result.to}")
    print(f"       Subject: {result.subject}")


def test_slicer_advisor_standard():
    from slicer_advisor import recommend_slicer_settings
    result = recommend_slicer_settings(print_purpose="일반", has_overhang=False)
    assert result.filament == "PLA (고정)"
    assert result.layer_height_mm > 0
    assert result.infill_percent > 0
    print(f"[PASS] 슬라이서 추천 (일반): 레이어 {result.layer_height_mm}mm, 인필 {result.infill_percent}%")


def test_slicer_advisor_overhang_forces_support():
    from slicer_advisor import recommend_slicer_settings
    result = recommend_slicer_settings(print_purpose="프로토타입", has_overhang=True)
    assert result.support is True, "오버행이 있으면 서포트 강제 활성화"
    print(f"[PASS] 오버행 → 서포트 강제 활성: {result.three_dwox1_tip}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
