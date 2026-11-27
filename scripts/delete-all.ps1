# ============================================================
# delete-all.ps1 — 메이커스페이스 에이전트 전체 삭제 스크립트
# 사용법: cd makerspace; .\scripts\delete-all.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$ROOT = Split-Path -Parent $PSScriptRoot

Write-Host "=== Makerspace AI Copilot — Delete All ===" -ForegroundColor Red
Write-Host "주의: 모든 에이전트·툴·KB가 삭제됩니다." -ForegroundColor Yellow
$confirm = Read-Host "계속하시겠습니까? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "취소됨." -ForegroundColor Green
    exit 0
}
Write-Host ""

# ── 1. 메인 에이전트 삭제 ──────────────────────────────────
Write-Host "[1/4] Main agent 삭제..." -ForegroundColor Yellow
orchestrate agents remove -n makerspace_main_agent --kind native 2>$null
Write-Host "  [OK]" -ForegroundColor Green

# ── 2. 서브 에이전트 삭제 ─────────────────────────────────
Write-Host "[2/4] Sub-agents 삭제..." -ForegroundColor Yellow
$agents = @("reservation_guide_agent", "print_prep_agent", "idea_to_model_agent", "learning_support_agent")
foreach ($a in $agents) {
    Write-Host "  removing $a ..." -NoNewline
    orchestrate agents remove -n $a --kind native 2>$null
    Write-Host " [OK]" -ForegroundColor Green
}

# ── 3. Knowledge Base 삭제 ────────────────────────────────
Write-Host "[3/4] Knowledge Base 삭제..." -ForegroundColor Yellow
orchestrate knowledge-bases remove -n makerspace_kb 2>$null
Write-Host "  [OK]" -ForegroundColor Green

# ── 4. Tools 삭제 ─────────────────────────────────────────
Write-Host "[4/4] Tools 삭제..." -ForegroundColor Yellow
$tools = @(
    "parse_timetable_and_find_free_slots",
    "check_available_slots",
    "make_reservation",
    "cancel_reservation",
    "add_to_waitlist",
    "get_active_waitlist",
    "assign_waitlist_entry",
    "check_and_assign_waitlist",
    "send_reservation_confirmed_email",
    "send_waitlist_registered_email",
    "send_auto_assigned_email",
    "validate_gcode_file",
    "recommend_slicer_settings",
    "build_gcode_filename",
    "check_filename_format",
    "draft_print_request_email",
    "refine_idea_to_requirements",
    "recommend_cad_tool",
    "search_open_models"
)
foreach ($t in $tools) {
    Write-Host "  removing $t ..." -NoNewline
    orchestrate tools remove -n $t 2>$null
    Write-Host " [OK]" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 삭제 완료 ===" -ForegroundColor Red
