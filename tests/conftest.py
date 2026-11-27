# tests/conftest.py — pytest 전역 픽스처: WxO mock 주입
import sys
from pathlib import Path

# mock_wxo를 가장 먼저 import해서 ibm_watsonx_orchestrate stub을 등록
sys.path.insert(0, str(Path(__file__).parent))
import mock_wxo  # noqa: F401 — side-effect only

# tools 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
