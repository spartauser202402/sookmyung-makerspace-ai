import { useRef, useState } from "react";
import { api } from "../api";
import type { GcodeValidation } from "../api";

type State = "idle" | "loading" | "ok" | "error";

export default function GcodePanel() {
  const [filename, setFilename] = useState("");
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<GcodeValidation | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = async (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    setState("loading");
    setResult(null);
    setErr(null);
    try {
      const data = await api.validateGcode(trimmed);
      setResult(data);
      setState(data.is_valid ? "ok" : "error");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "알 수 없는 오류");
      setState("error");
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]?.name ?? "";
    setFilename(f);
    if (f) validate(f);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0]?.name ?? "";
    setFilename(f);
    if (f) validate(f);
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => e.preventDefault();

  const reset = () => {
    setFilename("");
    setState("idle");
    setResult(null);
    setErr(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <aside className="gcode-panel">
      <div className="gcode-panel-header">
        <strong className="gcode-panel-title">.gcode 파일 검사</strong>
        <span className="gcode-panel-sub">에이전트에 파일 형식을 확인시킵니다</span>
      </div>

      <div
        className={`gcode-drop${state === "loading" ? " gcode-drop-loading" : ""}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        aria-label="파일을 드래그하거나 클릭해서 선택"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".gcode,.stl,.obj,.3mf,.step,.stp"
          style={{ display: "none" }}
          onChange={onFileChange}
        />
        {state === "idle" && (
          <>
            <div className="gcode-drop-icon">📂</div>
            <div className="gcode-drop-text">파일을 드래그하거나<br />클릭해서 선택</div>
            <div className="gcode-drop-hint">.gcode · .stl · .obj · .3mf 등</div>
          </>
        )}
        {state === "loading" && (
          <>
            <div className="gcode-drop-icon gcode-spin">⟳</div>
            <div className="gcode-drop-text">검사 중…</div>
          </>
        )}
        {(state === "ok" || state === "error") && filename && (
          <>
            <div className={`gcode-drop-icon ${state === "ok" ? "gcode-icon-ok" : "gcode-icon-err"}`}>
              {state === "ok" ? "✓" : "✕"}
            </div>
            <div className="gcode-drop-filename">{filename}</div>
          </>
        )}
      </div>

      {filename && state !== "idle" && state !== "loading" && (
        <button className="btn btn-sm gcode-reset" onClick={reset}>
          다시 선택
        </button>
      )}

      {/* 에러 */}
      {err && (
        <div className="gcode-result gcode-result-error">
          <div className="gcode-result-label">오류</div>
          <div className="gcode-result-msg">{err}</div>
        </div>
      )}

      {/* 검사 결과 */}
      {result && (
        <div className={`gcode-result ${result.is_valid ? "gcode-result-ok" : "gcode-result-error"}`}>
          <div className="gcode-result-label">
            {result.is_valid ? "✓ 유효한 파일" : "✕ 형식 오류"}
          </div>
          <div className="gcode-result-name">
            <code>{result.filename}</code>
            {result.detected_extension && result.detected_extension !== ".gcode" && (
              <span className="badge" style={{ marginLeft: 6 }}>{result.detected_extension}</span>
            )}
          </div>
          <div className="gcode-result-msg">{result.message}</div>
          {result.conversion_guide && (
            <pre className="gcode-guide">{result.conversion_guide.trim()}</pre>
          )}
        </div>
      )}

      {/* 사용 안내 */}
      {state === "idle" && (
        <div className="gcode-info">
          <div className="gcode-info-row">
            <span className="badge badge-ok">허용</span>
            <span>3DWOX1에서 슬라이싱한 <code>.gcode</code></span>
          </div>
          <div className="gcode-info-row">
            <span className="badge" style={{ background: "var(--danger-soft)", color: "var(--danger)" }}>거부</span>
            <span><code>.stl</code> · <code>.obj</code> · <code>.3mf</code> 등 직접 접수 불가</span>
          </div>
          <p className="gcode-info-note">
            파일은 서버에 업로드되지 않으며 파일명만 검사합니다.
          </p>
        </div>
      )}
    </aside>
  );
}
