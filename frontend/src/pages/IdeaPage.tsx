import { useState } from "react";
import { api } from "../api";
import { Card, ErrorNote, Field, Notice, useAction } from "../components/ui";

const FUNCTIONS = ["장식/소품", "기능성 부품", "조립/결합", "피규어", "교육용"];
const LEVELS = ["초보", "중급", "고급"];

export default function IdeaPage() {
  const [idea, setIdea] = useState("");
  const [size, setSize] = useState("");
  const [fn, setFn] = useState(FUNCTIONS[0]);
  const [level, setLevel] = useState("초보");
  const [query, setQuery] = useState("");

  const refine = useAction(api.refineIdea);
  const cad = useAction(api.cad);
  const models = useAction(api.models);

  const analyze = async () => {
    await Promise.all([
      refine.run({ idea_description: idea, estimated_size_cm: size || "미정", primary_function: fn }),
      cad.run(level, fn),
    ]);
    if (!query) setQuery(idea.split(/[,\s]+/).find((w) => w.length > 1) ?? idea);
  };

  const r = refine.data;
  const plaWarn = r && !r.pla_feasibility.startsWith("PLA 출력 적합");

  return (
    <div className="grid-2">
      <div className="stack">
        <Card title="아이디어 구체화" subtitle="만들고 싶은 것을 자유롭게 적어 주세요. 3D 모델 요구사항으로 정리해 드립니다.">
          <Field label="아이디어">
            <textarea rows={4} value={idea} onChange={(e) => setIdea(e.target.value)}
              placeholder="예: 책상에 놓을 연필꽂이, 귀여운 고양이 모양" />
          </Field>
          <div className="row-3">
            <Field label="예상 크기 (cm)" hint="가로x세로x높이"><input value={size} onChange={(e) => setSize(e.target.value)} placeholder="8x8x12" /></Field>
            <Field label="주요 용도">
              <select value={fn} onChange={(e) => setFn(e.target.value)}>{FUNCTIONS.map((f) => <option key={f}>{f}</option>)}</select>
            </Field>
            <Field label="모델링 경험">
              <select value={level} onChange={(e) => setLevel(e.target.value)}>{LEVELS.map((l) => <option key={l}>{l}</option>)}</select>
            </Field>
          </div>
          <button className="btn btn-primary" disabled={!idea.trim() || refine.loading} onClick={analyze}>정리하기</button>
          <ErrorNote error={refine.error || cad.error} />
        </Card>

        {r && (
          <Card title="모델 요구사항">
            <dl className="dl">
              <dt>요약</dt><dd>{r.idea_summary}</dd>
              <dt>크기</dt><dd>{r.estimated_size}</dd>
              <dt>형태</dt><dd>{r.shape_description}</dd>
              <dt>용도</dt><dd>{r.functional_requirement}</dd>
            </dl>
            <Notice tone={plaWarn ? "warn" : "ok"}>{r.pla_feasibility}</Notice>
            <Notice tone="info"><b>다음 단계</b> · {r.recommended_next_step}</Notice>
          </Card>
        )}
      </div>

      <div className="stack">
        <Card title="추천 CAD 도구" subtitle="모든 도구는 STL로 내보낸 뒤 3DWOX1에서 .gcode로 변환하세요.">
          {!cad.data && <p className="muted">아이디어를 정리하면 경험 수준에 맞는 도구를 추천합니다.</p>}
          {cad.data && (
            <ul className="tool-list">
              {cad.data.tools.map((t) => (
                <li key={t.name}>
                  <div className="row-between">
                    <strong>{t.name}</strong>
                    <a href={t.url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">열기 ↗</a>
                  </div>
                  <p>{t.description}</p>
                  <p className="muted small">적합: {t.best_for}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="오픈소스 모델 찾기" subtitle="직접 모델링 전에 비슷한 모델이 있는지 확인해 보세요.">
          <div className="row">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="연필꽂이, 스탠드, 화분…"
              onKeyDown={(e) => e.key === "Enter" && query.trim() && models.run(query)} />
            <button className="btn" disabled={!query.trim() || models.loading} onClick={() => models.run(query)}>검색</button>
          </div>
          <ErrorNote error={models.error} />
          {models.data?.is_mock && <Notice tone="warn">현재 샘플 데이터입니다. 실제 검색은 Thingiverse · Printables에서 직접 해 주세요.</Notice>}
          {models.data && (
            <ul className="tool-list">
              {models.data.results.map((m) => (
                <li key={m.url}>
                  <div className="row-between">
                    <strong>{m.title}</strong>
                    <span className="badge">{m.license}</span>
                  </div>
                  <p>{m.description}</p>
                  <p className="muted small">{m.source} · {m.author} · <a href={m.url} target="_blank" rel="noreferrer">보기 ↗</a></p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
