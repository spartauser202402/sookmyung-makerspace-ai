"""
idea_refiner.py — 아이디어 → 3D 모델 요구사항 구체화 Tool

사용자의 자유 서술을 크기·형태·기능·제약 항목으로 정리.
"""
from __future__ import annotations

from pydantic import BaseModel
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

# 3D 프린팅/모델링과 관련된 키워드가 하나 이상 포함돼야 처리
_3D_KEYWORDS = [
    "만들", "출력", "프린트", "모델", "stl", "gcode", "디자인", "형태", "크기",
    "모양", "조립", "부품", "케이스", "거치대", "스탠드", "홀더", "화분", "피규어",
    "소품", "장식", "조형", "cad", "tinkercad", "fusion", "blender", "freecad",
    "필라멘트", "pla", "3d", "print", "model", "design",
]


def _is_3d_related(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _3D_KEYWORDS)


class ModelRequirements(BaseModel):
    idea_summary: str
    estimated_size: str
    shape_description: str
    functional_requirement: str
    pla_feasibility: str
    recommended_next_step: str
    message: str


@tool(permission=ToolPermission.READ_ONLY)
def refine_idea_to_requirements(
    idea_description: str,
    estimated_size_cm: str = "미정",
    primary_function: str = "장식/소품",
) -> ModelRequirements:
    """자유 서술 아이디어를 3D 모델링 요구사항으로 정리합니다.

    Args:
        idea_description (str): 만들고 싶은 것에 대한 자유 서술. 예: '책상에 놓을 연필꽂이, 귀여운 동물 모양'
        estimated_size_cm (str): 예상 크기 (가로x세로x높이 cm). 예: '8x8x12'. 모르면 '미정'으로 입력.
        primary_function (str): 주요 용도. '장식/소품', '기능성 부품', '조립/결합', '피규어', '교육용' 중 선택.
    Returns:
        ModelRequirements: 정리된 요구사항과 다음 단계 추천.
    """
    # 3D 프린팅과 무관한 입력 차단
    if not _is_3d_related(idea_description):
        return ModelRequirements(
            idea_summary=idea_description[:100],
            estimated_size="N/A",
            shape_description="N/A",
            functional_requirement="N/A",
            pla_feasibility="N/A",
            recommended_next_step="N/A",
            message=(
                "이 도구는 3D 프린팅 모델 아이디어 구체화 전용입니다. "
                "만들고 싶은 물체나 3D 모델에 대한 아이디어를 설명해 주세요. "
                "예: '책상에 놓을 연필꽂이 만들고 싶어요'"
            ),
        )

    # PLA 적합성 판단
    pla_issues = []
    if "고온" in idea_description or "열" in idea_description:
        pla_issues.append("PLA는 60°C 이상 환경에서 변형될 수 있음")
    if "유연" in idea_description or "탄성" in idea_description:
        pla_issues.append("PLA는 단단한 소재 — 유연성이 필요하면 TPU 고려 (현재 숙명창작소 미제공)")
    if "투명" in idea_description:
        pla_issues.append("PLA는 불투명 — 투명 소재가 필요하면 resin 프린터 필요 (현재 미운영)")

    pla_ok = "PLA 출력 적합" if not pla_issues else "주의 필요: " + "; ".join(pla_issues)

    # 다음 단계 추천
    if "모델" in idea_description.lower() or "stl" in idea_description.lower():
        next_step = "기존 모델을 보유하고 있다면 3DWOX1에서 슬라이싱 후 .gcode로 변환하세요."
    elif primary_function in ("기능성 부품", "조립/결합"):
        next_step = "Fusion 360 또는 FreeCAD로 직접 모델링을 추천합니다 (정밀 치수 필요)."
    elif primary_function == "피규어":
        next_step = "Blender 또는 ZBrush로 모델링하거나, Thingiverse에서 유사 모델을 검색해 보세요."
    else:
        next_step = "Tinkercad(초보자 친화)로 모델링하거나, Thingiverse에서 유사 모델을 검색해 보세요."

    return ModelRequirements(
        idea_summary=idea_description[:100],
        estimated_size=estimated_size_cm,
        shape_description=f"자유 형태 — {idea_description[:60]}",
        functional_requirement=primary_function,
        pla_feasibility=pla_ok,
        recommended_next_step=next_step,
        message=f"요구사항 정리 완료. PLA 적합성: {pla_ok}",
    )
