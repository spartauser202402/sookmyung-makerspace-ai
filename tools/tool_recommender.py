"""
tool_recommender.py — 사용자 수준별 CAD 도구 추천
"""
from __future__ import annotations

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


CAD_TOOLS = {
    "beginner": [
        {
            "name": "Tinkercad",
            "url": "https://www.tinkercad.com",
            "description": "브라우저 기반, 무료. 블록 조합 방식으로 직관적. 초보자에게 최적.",
            "export": "STL -> 3DWOX1에서 .gcode 변환",
            "best_for": "소품, 케이스, 간단한 기구",
        },
    ],
    "intermediate": [
        {
            "name": "Fusion 360",
            "url": "https://www.autodesk.com/products/fusion-360",
            "description": "학생 무료 라이선스 제공. 파라메트릭 모델링, 치수 기반 설계.",
            "export": "STL -> 3DWOX1에서 .gcode 변환",
            "best_for": "기능성 부품, 조립품, 정밀 설계",
        },
        {
            "name": "FreeCAD",
            "url": "https://www.freecad.org",
            "description": "완전 무료 오픈소스. 파라메트릭 설계 가능.",
            "export": "STL -> 3DWOX1에서 .gcode 변환",
            "best_for": "기계 부품, 엔지니어링 설계",
        },
    ],
    "advanced": [
        {
            "name": "Blender",
            "url": "https://www.blender.org",
            "description": "무료 오픈소스. 유기적 형태, 피규어, 예술적 모델링에 강점.",
            "export": "STL -> 3DWOX1에서 .gcode 변환",
            "best_for": "피규어, 캐릭터, 복잡한 조형물",
        },
        {
            "name": "Rhino 3D",
            "url": "https://www.rhino3d.com",
            "description": "NURBS 기반. 학생 할인 있음.",
            "export": "STL -> 3DWOX1에서 .gcode 변환",
            "best_for": "제품 디자인, 건축 모형",
        },
    ],
}

LEVEL_MAP = {
    "초보": "beginner", "입문": "beginner", "처음": "beginner", "beginner": "beginner",
    "중급": "intermediate", "intermediate": "intermediate",
    "고급": "advanced", "expert": "advanced", "advanced": "advanced",
}


@tool(permission=ToolPermission.READ_ONLY)
def recommend_cad_tool(
    user_level: str = "초보",
    primary_use: str = "소품",
) -> dict:
    """사용자 수준에 맞는 3D 모델링 CAD 도구를 추천합니다.

    Args:
        user_level (str): 모델링 경험 수준. '초보', '중급', '고급' 중 선택.
        primary_use (str): 주요 사용 목적. 예: '소품', '기능성 부품', '피규어'.
    Returns:
        dict: level(str), tools(list), note(str), message(str).
    """
    level_key = "beginner"
    for kw, lk in LEVEL_MAP.items():
        if kw in user_level.lower():
            level_key = lk
            break

    tools = CAD_TOOLS.get(level_key, CAD_TOOLS["beginner"])
    note = (
        "모든 도구는 STL 형식으로 내보내기 후, "
        "3DWOX1 슬라이서에서 .gcode로 변환하여 숙명창작소에 제출하세요."
    )
    return {
        "level": level_key,
        "tools": tools,
        "note": note,
        "message": f"{level_key} 수준 추천 완료: {', '.join(t['name'] for t in tools)}",
    }
