export type AgentId =
  | "makerspace_main_agent"
  | "reservation_guide_agent"
  | "print_prep_agent"
  | "idea_to_model_agent"
  | "learning_support_agent";

export interface AgentInfo {
  id: AgentId;
  label: string;
  sub: string;
  icon: string;
  keywords: string[];
}

export const AGENTS: AgentInfo[] = [
  {
    id: "makerspace_main_agent",
    label: "Main",
    sub: "오케스트레이터",
    icon: "◎",
    keywords: [],
  },
  {
    id: "reservation_guide_agent",
    label: "예약",
    sub: "예약 · 대기 · 취소",
    icon: "📅",
    keywords: ["예약", "대기", "취소", "슬롯", "자리", "시간표", "배정"],
  },
  {
    id: "print_prep_agent",
    label: "출력 준비",
    sub: ".gcode · 슬라이싱 · 메일",
    icon: "🖨️",
    keywords: ["gcode", "stl", "obj", "3mf", "슬라이싱", "파일명", "이메일", "출력 접수", "변환"],
  },
  {
    id: "idea_to_model_agent",
    label: "아이디어 구상",
    sub: "요구사항 · CAD · 모델 검색",
    icon: "💡",
    keywords: ["만들고", "설계", "cad", "모델", "아이디어", "오픈소스", "thingiverse", "printables"],
  },
  {
    id: "learning_support_agent",
    label: "학습",
    sub: "가이드 · 트러블슈팅",
    icon: "📚",
    keywords: ["워핑", "스트링", "층분리", "노즐", "사용법", "처음", "pla", "파라미터", "오류"],
  },
];

/** 메시지 텍스트를 보고 어느 에이전트가 활성인지 추측 */
export function detectAgent(text: string): AgentId {
  const lower = text.toLowerCase();
  for (const agent of AGENTS.slice(1)) {
    if (agent.keywords.some((kw) => lower.includes(kw))) return agent.id;
  }
  return "makerspace_main_agent";
}

interface Props {
  activeAgent: AgentId;
}

export default function AgentSidebar({ activeAgent }: Props) {
  // Main 에이전트는 사이드바에서 제외 (전문 4개만 표시)
  const subAgents = AGENTS.slice(1);

  return (
    <aside className="agent-sidebar">
      <ul className="agent-list">
        {subAgents.map((a) => {
          const isActive = a.id === activeAgent;
          return (
            <li key={a.id} className={`agent-item${isActive ? " agent-item-active" : ""}`}>
              <span className="agent-status-icon">
                {isActive ? a.icon : "○"}
              </span>
              <span className="agent-label">{a.label}</span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
