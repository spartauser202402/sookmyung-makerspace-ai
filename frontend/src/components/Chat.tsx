import { useEffect, useRef, useState } from "react";
import type { AgentId } from "./AgentSidebar";
import { detectAgent } from "./AgentSidebar";
import type { NoteEntry } from "./ActivityNote";

const env = import.meta.env;
const HOST = env.VITE_WXO_HOST_URL as string | undefined;
const ORCH = env.VITE_WXO_ORCHESTRATION_ID as string | undefined;
const AGENT = env.VITE_WXO_AGENT_ID as string | undefined;
const AGENT_ENV = env.VITE_WXO_AGENT_ENVIRONMENT_ID as string | undefined;
export const WXO_ENABLED = Boolean(HOST && ORCH && AGENT);

declare global {
  interface Window {
    wxOConfiguration?: unknown;
    wxoLoader?: { init: () => void };
  }
}

interface Message {
  id: number;
  role: "user" | "agent";
  text: string;
  ts: Date;
}

interface Props {
  onAgentChange: (id: AgentId) => void;
  onNote: (entry: NoteEntry) => void;
}

const DEMO_PROMPTS = [
  "내 시간표야: 운영체제 월 09:00-11:50 목 09:00-11:50. 다음 주 화요일 11시에 예약해줘.",
  "test.gcode 파일 2026-11-30 13시에 출력 요청하는 이메일 초안 써줘.",
  "출력물 바닥에서 들떠요. 워핑이 생겼는데 어떻게 해결하나요?",
  "취소된 자리 있으면 나한테 배정해줘.",
];

let _id = 0;
const nextId = () => ++_id;

export default function Chat({ onAgentChange, onNote }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: nextId(),
      role: "agent",
      text: "안녕하세요! 숙명 메이커스페이스 AI 에이전트입니다.\n\n예약, 출력 파일 준비, 슬라이싱 설정, 가이드 문의 등 무엇이든 물어보세요.",
      ts: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // WxO 임베드 로드
  useEffect(() => {
    if (!WXO_ENABLED || document.getElementById("wxo-loader")) return;
    window.wxOConfiguration = {
      orchestrationID: ORCH,
      hostURL: HOST,
      rootElementID: "wxo-chat-root",
      chatOptions: { agentId: AGENT, ...(AGENT_ENV ? { agentEnvironmentId: AGENT_ENV } : {}) },
    };
    const s = document.createElement("script");
    s.id = "wxo-loader";
    s.src = `${HOST}/wxochat/wxoLoader.js?embed=true`;
    s.addEventListener("load", () => window.wxoLoader?.init());
    document.head.appendChild(s);
  }, []);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    // 사용자 메시지 기반으로 활성 에이전트 추측
    const detectedAgent = detectAgent(trimmed);
    onAgentChange(detectedAgent);

    const userMsg: Message = { id: nextId(), role: "user", text: trimmed, ts: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      const replyText: string = data.reply ?? data.message ?? JSON.stringify(data);

      const agentMsg: Message = { id: nextId(), role: "agent", text: replyText, ts: new Date() };
      setMessages((prev) => [...prev, agentMsg]);

      // 응답 기반으로 에이전트 재감지 후 노트 추가
      const finalAgent = detectAgent(replyText) !== "makerspace_main_agent"
        ? detectAgent(replyText)
        : detectedAgent;
      onAgentChange(finalAgent);
      onNote({ id: nextId(), agentId: finalAgent, userText: trimmed, agentText: replyText, ts: new Date() });
    } catch {
      const errText = "⚠️ 에이전트에 연결할 수 없습니다. 백엔드 서버 또는 watsonx Orchestrate 연결을 확인하세요.";
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "agent", text: errText, ts: new Date() },
      ]);
      onNote({ id: nextId(), agentId: detectedAgent, userText: trimmed, agentText: errText, ts: new Date() });
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  // WxO 임베드 모드
  if (WXO_ENABLED) {
    return (
      <div className="chat-panel">
        <div className="chat-header">
          <span className="chat-title">makerspace_main_agent</span>
          <span className="badge badge-ok">연결됨</span>
        </div>
        <div id="wxo-chat-root" style={{ flex: 1 }} />
      </div>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title-group">
          <span className="chat-title">makerspace_main_agent</span>
          <span className="badge badge-warn">미연결</span>
        </div>
        <span className="chat-hint">watsonx Orchestrate 미연결 — /api/chat 경유</span>
      </div>

      <div className="chat-messages">
        {messages.map((m) => (
          <div key={m.id} className={`chat-bubble chat-bubble-${m.role}`}>
            <div className="chat-text">{m.text}</div>
            <div className="chat-ts">
              {m.ts.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-bubble chat-bubble-agent">
            <div className="chat-typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 1 && (
        <div className="chat-prompts">
          {DEMO_PROMPTS.map((p) => (
            <button key={p} className="chat-prompt-chip" onClick={() => sendMessage(p)}>
              {p}
            </button>
          ))}
        </div>
      )}

      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          rows={1}
          placeholder="메시지를 입력하세요… (Enter 전송 · Shift+Enter 줄바꿈)"
          value={input}
          onChange={handleInput}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button
          className="chat-send btn btn-primary"
          disabled={!input.trim() || loading}
          onClick={() => sendMessage(input)}
        >
          전송
        </button>
      </div>
    </div>
  );
}
