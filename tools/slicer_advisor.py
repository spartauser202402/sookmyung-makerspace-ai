"""
slicer_advisor.py — PLA 기준 슬라이싱 파라미터 추천

필라멘트: PLA 단일 고정 (이용수칙).
출력 목적에 따라 최적 설정을 제안.
"""
from __future__ import annotations

from pydantic import BaseModel
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# PLA 고정 파라미터 사전 (KB에도 등록됨)
PLA_PROFILES: dict[str, dict] = {
    "prototype": {
        "layer_height_mm": 0.2,
        "infill_percent": 15,
        "print_speed_mm_s": 60,
        "support": False,
        "brim": False,
        "note": "빠른 프로토타입. 강도보다 속도 우선.",
    },
    "standard": {
        "layer_height_mm": 0.15,
        "infill_percent": 20,
        "print_speed_mm_s": 50,
        "support": False,
        "brim": False,
        "note": "일반적인 용도. 속도와 품질 균형.",
    },
    "detail": {
        "layer_height_mm": 0.1,
        "infill_percent": 30,
        "print_speed_mm_s": 40,
        "support": True,
        "brim": True,
        "note": "세밀한 형상이나 소품. 출력 시간이 길어짐.",
    },
    "strong": {
        "layer_height_mm": 0.2,
        "infill_percent": 50,
        "print_speed_mm_s": 45,
        "support": True,
        "brim": True,
        "note": "기능성 부품, 조립용. 강도가 중요한 경우.",
    },
    "miniature": {
        "layer_height_mm": 0.08,
        "infill_percent": 25,
        "print_speed_mm_s": 30,
        "support": True,
        "brim": False,
        "note": "피규어·소형 모형. 느리고 정밀.",
    },
}

PURPOSE_MAP = {
    "프로토타입": "prototype", "테스트": "prototype", "빠르게": "prototype",
    "일반": "standard", "표준": "standard", "기본": "standard",
    "세밀": "detail", "정밀": "detail", "소품": "detail", "디테일": "detail",
    "강도": "strong", "기능": "strong", "조립": "strong", "튼튼": "strong",
    "미니어처": "miniature", "피규어": "miniature", "소형": "miniature",
}


class SlicerRecommendation(BaseModel):
    filament: str
    profile_name: str
    layer_height_mm: float
    infill_percent: int
    print_speed_mm_s: int
    support: bool
    brim: bool
    note: str
    three_dwox1_tip: str
    message: str


@tool(permission=ToolPermission.READ_ONLY)
def recommend_slicer_settings(
    print_purpose: str = "standard",
    has_overhang: bool = False,
) -> SlicerRecommendation:
    """PLA 필라멘트 기준 3DWOX1 슬라이싱 파라미터를 추천합니다.

    Args:
        print_purpose (str): 출력 목적. '프로토타입', '일반', '세밀', '강도', '미니어처' 중 선택.
        has_overhang (bool): 돌출부(오버행) 형상이 있으면 True (서포트 필요 여부 판단용).
    Returns:
        SlicerRecommendation: 추천 슬라이싱 설정.
    """
    # 목적 키워드 매핑
    profile_key = "standard"
    for kw, pk in PURPOSE_MAP.items():
        if kw in print_purpose:
            profile_key = pk
            break

    p = PLA_PROFILES[profile_key].copy()

    # 오버행이 있으면 서포트 강제 추가
    if has_overhang:
        p["support"] = True

    tip = (
        "3DWOX1에서: 필라멘트 'PLA' 선택 → "
        f"레이어 높이 {p['layer_height_mm']}mm → "
        f"인필 {p['infill_percent']}% → "
        f"서포트 {'켜기' if p['support'] else '끄기'} → "
        f"브림 {'켜기' if p['brim'] else '끄기'} → 슬라이싱 → .gcode 저장"
    )

    return SlicerRecommendation(
        filament="PLA (고정)",
        profile_name=profile_key,
        layer_height_mm=p["layer_height_mm"],
        infill_percent=p["infill_percent"],
        print_speed_mm_s=p["print_speed_mm_s"],
        support=p["support"],
        brim=p["brim"],
        note=p["note"],
        three_dwox1_tip=tip,
        message=f"[{profile_key}] 프로필 추천 완료. 필라멘트는 PLA로 고정입니다.",
    )
