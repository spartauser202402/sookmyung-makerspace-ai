import type { ReactNode } from "react";

/** KB 문서용 경량 마크다운 렌더러 (헤딩·목록·표·인용·굵게·코드). innerHTML을 쓰지 않습니다. */
export default function Markdown({ source }: { source: string }) {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const out: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];
    const t = line.trim();

    if (!t) { i++; continue; }
    if (/^-{3,}$/.test(t)) { out.push(<hr key={key++} />); i++; continue; }

    const h = /^(#{1,4})\s+(.*)$/.exec(t);
    if (h) {
      const level = h[1].length;
      const Tag = (`h${Math.min(level + 1, 5)}`) as "h2";
      out.push(<Tag key={key++}>{inline(h[2])}</Tag>);
      i++;
      continue;
    }

    if (t.startsWith(">")) {
      const buf: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) buf.push(lines[i++].trim().replace(/^>\s?/, ""));
      out.push(<blockquote key={key++}>{inline(buf.join(" "))}</blockquote>);
      continue;
    }

    if (t.startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) buf.push(lines[i++]);
      i++;
      out.push(<pre key={key++} className="pre">{buf.join("\n")}</pre>);
      continue;
    }

    if (t.startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const cells = lines[i].trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        if (!cells.every((c) => /^:?-+:?$/.test(c))) rows.push(cells);
        i++;
      }
      const [head, ...body] = rows;
      out.push(
        <div key={key++} className="table-wrap">
          <table>
            <thead><tr>{head.map((c, j) => <th key={j}>{inline(c)}</th>)}</tr></thead>
            <tbody>{body.map((r, ri) => <tr key={ri}>{r.map((c, j) => <td key={j}>{inline(c)}</td>)}</tr>)}</tbody>
          </table>
        </div>,
      );
      continue;
    }

    if (/^([-*]|\d+\.)\s/.test(t)) {
      const ordered = /^\d+\./.test(t);
      const items: string[] = [];
      while (i < lines.length && /^\s*([-*]|\d+\.)\s/.test(lines[i])) {
        items.push(lines[i].trim().replace(/^([-*]|\d+\.)\s+/, ""));
        i++;
      }
      const List = ordered ? "ol" : "ul";
      out.push(<List key={key++}>{items.map((it, j) => <li key={j}>{inline(it)}</li>)}</List>);
      continue;
    }

    const buf: string[] = [];
    while (i < lines.length && lines[i].trim() && !/^(#|>|\||```|-{3,}$|[-*]\s|\d+\.\s)/.test(lines[i].trim())) {
      buf.push(lines[i++].trim());
    }
    if (!buf.length) { buf.push(t); i++; }
    out.push(<p key={key++}>{inline(buf.join(" "))}</p>);
  }

  return <div className="md">{out}</div>;
}

function inline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) parts.push(<strong key={k++}>{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("`")) parts.push(<code key={k++}>{tok.slice(1, -1)}</code>);
    else {
      const lm = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(tok)!;
      const safe = /^https?:\/\//.test(lm[2]) ? lm[2] : undefined;
      parts.push(<a key={k++} href={safe} target="_blank" rel="noreferrer">{lm[1]}</a>);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}
