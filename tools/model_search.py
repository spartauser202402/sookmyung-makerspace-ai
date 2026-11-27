"""
model_search.py — 오픈소스 3D 모델 검색 (Mock: 고정 샘플 5개 반환)
Phase 2에서 Thingiverse API / Printables GraphQL로 교체 예정.
"""
from __future__ import annotations

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

MOCK_MODELS = [
    {
        "title": "Pencil Holder — Animal Series",
        "source": "Thingiverse",
        "url": "https://www.thingiverse.com/thing:12345",
        "author": "maker_kim",
        "license": "CC BY",
        "pla_compatible": True,
        "description": "귀여운 동물 모양 연필꽂이. PLA 출력 최적화.",
    },
    {
        "title": "Phone Stand — Minimalist",
        "source": "Printables",
        "url": "https://www.printables.com/model/67890",
        "author": "designlab",
        "license": "CC BY-SA",
        "pla_compatible": True,
        "description": "미니멀 스마트폰 스탠드. 서포트 없이 출력 가능.",
    },
    {
        "title": "Cable Management Clip",
        "source": "Thingiverse",
        "url": "https://www.thingiverse.com/thing:11111",
        "author": "printeverything",
        "license": "CC0",
        "pla_compatible": True,
        "description": "케이블 정리 클립. 벽면 부착 가능.",
    },
    {
        "title": "Customizable Name Tag",
        "source": "Thingiverse",
        "url": "https://www.thingiverse.com/thing:22222",
        "author": "opendesign",
        "license": "CC BY",
        "pla_compatible": True,
        "description": "이름 태그 커스터마이즈 가능 (Tinkercad 편집 권장).",
    },
    {
        "title": "Planter — Small Succulent Pot",
        "source": "MyMiniFactory",
        "url": "https://www.myminifactory.com/object/33333",
        "author": "greenprints",
        "license": "CC BY-NC",
        "pla_compatible": True,
        "description": "소형 다육식물 화분. 브림 사용 권장.",
    },
]


@tool(permission=ToolPermission.READ_ONLY)
def search_open_models(query: str, max_results: int = 5) -> dict:
    """오픈소스 3D 모델 플랫폼에서 유사 모델을 검색합니다.

    Args:
        query (str): 검색 키워드. 예: '연필꽂이', '스탠드', '화분'.
        max_results (int): 반환할 최대 결과 수 (기본 5, 최대 5).
    Returns:
        dict: query(str), results(list), is_mock(bool), message(str).
    """
    limit = min(max_results, 5)
    results = MOCK_MODELS[:limit]
    return {
        "query": query,
        "results": results,
        "is_mock": True,
        "message": (
            f"'{query}' 검색 결과 {len(results)}개 (현재 샘플 데이터).\n"
            f"실제 모델은 Thingiverse(thingiverse.com), "
            f"Printables(printables.com)에서 직접 검색하세요.\n"
            f"다운로드한 STL 파일은 3DWOX1에서 .gcode로 변환 후 제출하세요."
        ),
    }
