import { useCallback, useState, type ReactNode } from "react";

/** 비동기 호출 상태(loading/error/data)를 한 번에 관리 */
export function useAction<A extends unknown[], T>(fn: (...args: A) => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const run = useCallback(
    async (...args: A) => {
      setLoading(true);
      setError(null);
      try {
        const r = await fn(...args);
        setData(r);
        return r;
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [fn],
  );
  return { data, error, loading, run, setData };
}

export function Card({ title, subtitle, children, actions }: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <section className="card">
      <header className="card-head">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        {actions}
      </header>
      {children}
    </section>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "ok" | "warn" | "error"; children: ReactNode }) {
  return <div className={`notice notice-${tone}`}>{children}</div>;
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <Notice tone="error">
      {error.includes("DB not found") || error.includes("Failed to fetch") || error.startsWith("5")
        ? "백엔드에 연결할 수 없습니다. `python db/seed.py` 후 `uvicorn api.server:app --port 8000` 를 실행했는지 확인하세요."
        : error}
    </Notice>
  );
}

export function Pre({ children }: { children: ReactNode }) {
  return <pre className="pre">{children}</pre>;
}

export function CopyButton({ text, label = "복사" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      className="btn btn-ghost btn-sm"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setDone(true);
        setTimeout(() => setDone(false), 1500);
      }}
    >
      {done ? "복사됨 ✓" : label}
    </button>
  );
}
