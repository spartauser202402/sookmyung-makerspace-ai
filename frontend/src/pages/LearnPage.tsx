import { useEffect, useState } from "react";
import { api } from "../api";
import Markdown from "../components/Markdown";
import { Card, ErrorNote, Notice, useAction } from "../components/ui";

const QUICK = ["워핑", "스트링", "첫 레이어", "서포트", "노즐 막힘", "온도", "운영시간", "미방문"];

export default function LearnPage() {
  const list = useAction(api.kbList);
  const doc = useAction(api.kbDoc);
  const search = useAction(api.kbSearch);
  const [q, setQ] = useState("");
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    list.run().then((r) => {
      const first = r?.documents.find((d) => d.includes("이용수칙")) ?? r?.documents[0];
      if (first) open(first);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const open = (name: string) => {
    setActive(name);
    doc.run(name);
  };
  const doSearch = (term: string) => {
    setQ(term);
    if (term.trim()) search.run(term.trim());
  };

  return (
    <div className="learn">
      <aside className="stack">
        <Card title="문제 해결 검색" subtitle="증상을 입력하면 지식베이스에서 관련 내용을 찾아드립니다.">
          <div className="row">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="예: 바닥이 들떠요"
              onKeyDown={(e) => e.key === "Enter" && doSearch(q)} />
            <button className="btn" onClick={() => doSearch(q)} disabled={!q.trim()}>검색</button>
          </div>
          <div className="chips">
            {QUICK.map((t) => <button key={t} className="chip" onClick={() => doSearch(t)}>{t}</button>)}
          </div>
          <ErrorNote error={search.error} />
          {search.data && (search.data.results.length ? (
            <ul className="hits">
              {search.data.results.map((h, i) => (
                <li key={i}>
                  <details className="hit" open={i === 0}>
                    <summary>
                      <span className="muted small">{h.document.replace(/_/g, " ")}</span>
                      <strong>{h.section}</strong>
                    </summary>
                    <Markdown source={h.snippet.split("\n").slice(1).join("\n")} />
                    <button className="btn btn-ghost btn-sm" onClick={() => open(h.document)}>전체 문서 보기 →</button>
                  </details>
                </li>
              ))}
            </ul>
          ) : <Notice tone="warn">검색 결과가 없습니다. 다른 표현으로 시도하거나 AI 코파일럿에게 물어보세요.</Notice>)}
        </Card>

        <Card title="지식베이스 문서">
          <ErrorNote error={list.error} />
          <ul className="doc-list">
            {list.data?.documents.map((d) => (
              <li key={d}>
                <button className={active === d ? "active" : ""} onClick={() => open(d)}>{d.replace(/_/g, " ")}</button>
              </li>
            ))}
          </ul>
        </Card>
      </aside>

      <Card title={active ? active.replace(/_/g, " ") : "문서"}>
        <ErrorNote error={doc.error} />
        {doc.loading && <p className="muted">불러오는 중…</p>}
        {doc.data && <Markdown source={doc.data.content} />}
      </Card>
    </div>
  );
}
