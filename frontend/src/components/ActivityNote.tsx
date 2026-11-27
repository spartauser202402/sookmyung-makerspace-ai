import type { AgentId } from "./AgentSidebar";
import { AGENTS } from "./AgentSidebar";

export interface NoteEntry {
  id: number;
  agentId: AgentId;
  userText: string;
  agentText: string;
  ts: Date;
}

/** 에이전트 응답에서 핵심 요약 한 줄 추출 */
export function summarize(text: string): string {
  // 오류/경고
  if (text.includes("⚠️")) return "⚠️ 에이전트 연결 오류";

  // 첫 번째 의미 있는 문장 추출 (최대 60자)
  const sentences = text
    .replace(/\n+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 8);

  const first = sentences[0] ?? text.trim();
  return first.length > 60 ? first.slice(0, 58) + "…" : first;
}

interface Props {
  notes: NoteEntry[];
}

export default function ActivityNote({ notes }: Props) {
  if (notes.length === 0) {
    return (
      <section className="note-panel note-panel-empty">
        <div className="note-panel-title">활동 노트</div>
        <p className="note-empty-msg">대화가 시작되면<br />핵심 내용이 여기에 정리됩니다.</p>
      </section>
    );
  }

  return (
    <section className="note-panel">
      <div className="note-panel-title">활동 노트</div>
      <ul className="note-list">
        {notes.map((n) => {
          const agent = AGENTS.find((a) => a.id === n.agentId);
          const summary = summarize(n.agentText);
          return (
            <li key={n.id} className="note-item">
              <div className="note-item-header">
                <span className="note-agent-icon">{agent?.icon}</span>
                <span className="note-agent-label">{agent?.label}</span>
                <span className="note-ts">
                  {n.ts.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
              <div className="note-user-text">
                <span className="note-label-you">You</span>
                {n.userText.length > 50 ? n.userText.slice(0, 48) + "…" : n.userText}
              </div>
              <div className="note-summary">{summary}</div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
