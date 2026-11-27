import { useEffect, useState } from "react";
import { api } from "./api";
import Chat from "./components/Chat";
import AgentSidebar from "./components/AgentSidebar";
import ActivityNote from "./components/ActivityNote";
import type { AgentId } from "./components/AgentSidebar";
import type { NoteEntry } from "./components/ActivityNote";

export default function App() {
  const [backend, setBackend] = useState<"ok" | "nodb" | "down" | "checking">("checking");
  const [activeAgent, setActiveAgent] = useState<AgentId>("makerspace_main_agent");
  const [notes, setNotes] = useState<NoteEntry[]>([]);

  useEffect(() => {
    api.health()
      .then((h) => setBackend(h.db ? "ok" : "nodb"))
      .catch(() => setBackend("down"));
  }, []);

  const handleNote = (entry: NoteEntry) => {
    setNotes((prev) => [...prev, entry]);
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>▲</span>
          <div>
            <strong>숙명창작소</strong>
            <span>AI 에이전트 · 3DWOX1 / PLA</span>
          </div>
        </div>
        <span className={`status status-${backend}`} title="백엔드 상태">
          {backend === "ok"
            ? "서버 연결됨"
            : backend === "nodb"
            ? "DB 없음"
            : backend === "down"
            ? "서버 꺼짐"
            : "확인 중"}
        </span>
      </header>

      {backend === "down" && (
        <div className="topbar-notice notice-error">
          백엔드(:8001)에 연결할 수 없습니다.&nbsp;
          <code>uvicorn api.server:app --port 8001</code>을 실행하세요.
        </div>
      )}
      {backend === "nodb" && (
        <div className="topbar-notice notice-warn">
          DB가 없습니다. <code>python db/seed.py</code>를 먼저 실행하세요.
        </div>
      )}

      <main className="workspace">
        <AgentSidebar activeAgent={activeAgent} />
        <Chat onAgentChange={setActiveAgent} onNote={handleNote} />
        <ActivityNote notes={notes} />
      </main>

      <footer className="foot muted small">
        접수: makerspace@sookmyung.ac.kr · 학번·비밀번호는 수집하지 않습니다.
      </footer>
    </div>
  );
}
