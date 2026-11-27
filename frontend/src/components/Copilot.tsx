import { useEffect, useState } from "react";

/**
 * watsonx Orchestrate 웹챗 임베드.
 * frontend/.env 에 VITE_WXO_* 값을 넣으면 makerspace_main_agent 채팅이 우측 하단에 뜹니다.
 * 값은 `orchestrate channels webchat embed --agent-name=makerspace_main_agent` 출력에서 얻을 수 있습니다.
 */
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

const DEMO_PROMPTS = [
  "내 시간표야: 운영체제 월 09:00-11:50 목 09:00-11:50. 다음 주 화요일 11시에 예약해줘.",
  "취소된 자리 있으면 나한테 배정해줘.",
  "model.stl 파일 출력하고 싶어요.",
  "test.gcode 파일 2026-11-30 13시에 출력 요청하는 이메일 초안 써줘.",
  "출력물 바닥에서 들떠요. 워핑이 생겼는데 어떻게 해결하나요?",
];

export default function Copilot() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!WXO_ENABLED || document.getElementById("wxo-loader")) return;
    window.wxOConfiguration = {
      orchestrationID: ORCH,
      hostURL: HOST,
      rootElementID: "wxo-root",
      chatOptions: { agentId: AGENT, ...(AGENT_ENV ? { agentEnvironmentId: AGENT_ENV } : {}) },
    };
    const s = document.createElement("script");
    s.id = "wxo-loader";
    s.src = `${HOST}/wxochat/wxoLoader.js?embed=true`;
    s.addEventListener("load", () => window.wxoLoader?.init());
    document.head.appendChild(s);
  }, []);

  if (WXO_ENABLED) return <div id="wxo-root" />;

  return (
    <>
      <button className="fab" onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-label="AI 코파일럿">
        {open ? "✕" : "AI"}
      </button>
      {open && (
        <div className="copilot" role="dialog" aria-label="AI 코파일럿">
          <header>
            <strong>AI 코파일럿</strong>
            <span className="badge badge-warn">미연결</span>
          </header>
          <p className="small">
            대화형 코파일럿은 watsonx Orchestrate의 <code>makerspace_main_agent</code>로 동작합니다.
            연결하려면 <code>frontend/.env</code>에 <code>VITE_WXO_*</code> 값을 설정하고 dev 서버를 재시작하세요.
          </p>
          <p className="small muted">연결 후 이런 질문을 해 볼 수 있어요:</p>
          <ul className="prompts">
            {DEMO_PROMPTS.map((p) => (
              <li key={p}>
                <button onClick={() => navigator.clipboard.writeText(p)} title="클릭해서 복사">{p}</button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
