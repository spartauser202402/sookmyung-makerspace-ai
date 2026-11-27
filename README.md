# 숙명 메이커스페이스 AI 코파일럿

> IBM watsonx Orchestrate 멀티에이전트 시스템으로 구현한 3D 프린팅 메이커스페이스 운영 지원 AI

---

## 개요

| 항목 | 내용 |
|---|---|
| 플랫폼 | IBM watsonx Orchestrate (ADK v1) |
| 에이전트 수 | 5개 (메인 1 + 서브 4) |
| Tool 수 | 19개 Python 함수 |
| 장비 | 신도리코 3DWOX1 단일 |
| 필라멘트 | PLA 단일 고정 |
| 예약 슬롯 | 11시 / 13시 / 15시 / 17시 |
| DB | SQLite (로컬 Adapter, 추후 학교 API로 교체 가능) |

---

## 아키텍처

```
사용자
  │
  ▼
makerspace_main_agent  ← 메인 오케스트레이터 (라우터)
  ├─ reservation_guide_agent   ← 예약·대기·자동배정
  ├─ print_prep_agent          ← .gcode 검증·슬라이싱·이메일 초안
  ├─ idea_to_model_agent       ← 아이디어 → CAD → 모델 검색
  └─ learning_support_agent    ← RAG 기반 교육·트러블슈팅
```

---

## 디렉터리 구조

```
makerspace/
├── db/
│   ├── schema.sql           # SQLite DDL
│   ├── seed.py              # 테스트 데이터 생성 (60슬롯, 5개 만석)
│   └── makerspace.db        # 생성된 DB (seed 실행 후)
├── tools/                   # WxO Python 도구 (19개)
│   ├── db_utils.py
│   ├── timetable_parser.py
│   ├── reservation_adapter.py
│   ├── waitlist_db.py
│   ├── scheduler.py
│   ├── email_sender.py
│   ├── gcode_validator.py
│   ├── slicer_advisor.py
│   ├── filename_builder.py
│   ├── email_draft.py
│   ├── idea_refiner.py
│   ├── tool_recommender.py
│   └── model_search.py
├── agents/                  # 에이전트 YAML
│   ├── makerspace_main_agent.yaml      # 오케스트레이터
│   ├── reservation_guide_agent.yaml
│   ├── print_prep_agent.yaml
│   ├── idea_to_model_agent.yaml
│   └── learning_support_agent.yaml
├── knowledge_base/          # RAG 소스 문서
│   ├── 이용수칙.md
│   ├── 3DWOX1_사용가이드.md
│   ├── PLA_파라미터.md
│   ├── 트러블슈팅_사례집.md
│   └── makerspace_kb.yaml   # KB 등록 스펙
├── tests/
│   ├── conftest.py
│   ├── mock_wxo.py
│   ├── test_reservation.py  # 4/4 PASS
│   └── test_print_prep.py   # 10/10 PASS
├── scripts/
│   ├── import-all.ps1       # 전체 등록
│   └── delete-all.ps1       # 전체 삭제
├── .env.example
└── README.md
```

---

## 시작하기

### 1. 환경 설정

```powershell
# 1-1. .env 파일 생성
cp makerspace\.env.example makerspace\.env
# .env 파일을 열어 SENDGRID_API_KEY, DEMO_EMAIL_* 값 입력

# 1-2. Python 패키지 설치 (필요 시)
pip install sendgrid python-dotenv
```

### 2. DB 초기화

```powershell
cd makerspace
python db\seed.py
# 출력: [OK] DB seed complete — 60 slots, 5 full slots
```

### 3. 로컬 테스트 실행

```powershell
# 프로젝트 루트에서
$env:PYTHONPATH = "makerspace"
python -m pytest makerspace\tests\ -v
# 기대 결과: 14개 테스트 모두 PASS
```

### 4. WxO 등록 (IBM watsonx Orchestrate 환경 필요)

```powershell
# orchestrate CLI 로그인
orchestrate environment activate <your-env>

# 전체 컴포넌트 등록
cd makerspace
.\scripts\import-all.ps1
```

---

## 데모 시나리오 5개

### 시나리오 1 — 시간표 → 예약 대기

```
사용자: "내 시간표야: 운영체제 월 09:00-11:50 목 09:00-11:50.
       다음 주 화요일 11시에 예약해줘. 이름은 강채린, 이메일 test@test.com"
```
> 공강 확인 → 11시 만석 → 대기 등록 → 대기 확인 메일 발송

### 시나리오 2 — 취소 감지 → 자동 배정

```
사용자: "취소된 자리 있으면 나한테 배정해줘."
```
> check_and_assign_waitlist → 취소 슬롯 발견 → 자동 배정 → 메일 알림

### 시나리오 3 — 비gcode 파일 거절

```
사용자: "model.stl 파일 출력하고 싶어요."
```
> validate_gcode_file → .stl 거절 → 3DWOX1 슬라이싱 가이드 안내

### 시나리오 4 — 파일명 자동 생성 + 이메일 초안

```
사용자: "test.gcode 파일 2026-11-30 13시에 출력 요청하는 이메일 초안 써줘. 이름은 강채린."
```
> build_gcode_filename → 20261130_13_강채린.gcode → draft_print_request_email → 초안 출력

### 시나리오 5 — RAG 트러블슈팅

```
사용자: "출력물 바닥에서 들떠요. 워핑이 생겼는데 어떻게 해결하나요?"
```
> learning_support_agent → KB 검색(트러블슈팅_사례집.md) → 원인 + 해결책 안내

---

## 이용수칙 (에이전트 공통 적용)

| 항목 | 규칙 |
|---|---|
| 예약 슬롯 | 11시 / 13시 / 15시 / 17시 고정 |
| 파일 형식 | .gcode 만 접수 |
| 필라멘트 | PLA 단일 고정 |
| 접수 이메일 | makerspace@sookmyung.ac.kr |
| 당일 취소 | 불가 |
| 미방문 제재 | 10분 이내 미방문 3회 누적 시 1개월 이용 정지 |
| 보안 | 학번·비밀번호 절대 요청·저장 금지 |

---

## 주요 환경변수 (.env)

| 변수명 | 설명 |
|---|---|
| `SENDGRID_API_KEY` | SendGrid API 키 |
| `DEMO_EMAIL_SENDER` | 발신 이메일 주소 |
| `DEMO_EMAIL_RECIPIENT` | 수신 이메일 주소 (테스트용) |
| `IBM_CLOUD_API_KEY` | WxO 인스턴스 접근 키 |
| `WXO_INSTANCE_URL` | WxO 인스턴스 URL |

---

## 확장 포인트

- **학교 API 연동**: `tools/reservation_adapter.py`의 `ReservationAdapter` 클래스를 교체하면 SQLite → 실제 학교 시스템 API로 전환 가능
- **이메일 실제 발송**: `email_sender.py`의 `SENDGRID_API_KEY` 설정 후 바로 동작
- **KB 확장**: `knowledge_base/` 폴더에 `.md` 파일 추가 후 `makerspace_kb.yaml` 업데이트
