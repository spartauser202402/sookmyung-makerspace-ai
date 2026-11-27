# ============================================================
# import-all.ps1 — 메이커스페이스 에이전트 전체 등록 스크립트
# 사용법: cd makerspace; .\scripts\import-all.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$ORC = "C:\Users\user\Documents\bob3\venv\Scripts\orchestrate.exe"

Write-Host "=== Makerspace AI Copilot — Import All ===" -ForegroundColor Cyan
Write-Host ""

# ── 1. DB 초기화 ───────────────────────────────────────────
Write-Host "[1/5] DB seed 실행..." -ForegroundColor Yellow
python "$ROOT\db\seed.py"
Write-Host "  [OK] DB seed 완료" -ForegroundColor Green
Write-Host ""

# ── 2. Tools 등록 (python) ─────────────────────────────────
Write-Host "[2/5] Tools 등록..." -ForegroundColor Yellow

$tools = @(
    "tools\timetable_parser.py",
    "tools\reservation_adapter.py",
    "tools\waitlist_db.py",
    "tools\scheduler.py",
    "tools\email_sender.py",
    "tools\gcode_validator.py",
    "tools\slicer_advisor.py",
    "tools\filename_builder.py",
    "tools\email_draft.py",
    "tools\idea_refiner.py",
    "tools\tool_recommender.py",
    "tools\model_search.py"
)

foreach ($tool in $tools) {
    $path = Join-Path $ROOT $tool
    $name = [System.IO.Path]::GetFileNameWithoutExtension($tool)
    Write-Host "  importing $name ..." -NoNewline
    & $ORC tools import -k python -f $path --package-root "$ROOT\tools"
    Write-Host " [OK]" -ForegroundColor Green
}
Write-Host ""

# ── 3. Knowledge Base 등록 ─────────────────────────────────
Write-Host "[3/5] Knowledge Base 등록..." -ForegroundColor Yellow
& $ORC knowledge-bases import -f "$ROOT\knowledge_base\makerspace_kb.yaml"
Write-Host "  [OK] makerspace_kb 등록 완료" -ForegroundColor Green
Write-Host ""

# ── 4. 서브 에이전트 등록 ──────────────────────────────────
Write-Host "[4/5] Sub-agents 등록..." -ForegroundColor Yellow

$subAgents = @(
    "agents\reservation_guide_agent.yaml",
    "agents\print_prep_agent.yaml",
    "agents\idea_to_model_agent.yaml",
    "agents\learning_support_agent.yaml"
)

foreach ($agent in $subAgents) {
    $path = Join-Path $ROOT $agent
    $name = [System.IO.Path]::GetFileNameWithoutExtension($agent)
    Write-Host "  importing $name ..." -NoNewline
    & $ORC agents import -f $path
    Write-Host " [OK]" -ForegroundColor Green
}
Write-Host ""

# ── 5. 메인 오케스트레이터 등록 ───────────────────────────
Write-Host "[5/5] Main orchestrator 등록..." -ForegroundColor Yellow
& $ORC agents import -f "$ROOT\agents\makerspace_main_agent.yaml"
Write-Host "  [OK] makerspace_main_agent 등록 완료" -ForegroundColor Green
Write-Host ""

Write-Host "=== Done! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. orchestrate agents list"
Write-Host "  2. orchestrate chat ask -n makerspace_main_agent"
