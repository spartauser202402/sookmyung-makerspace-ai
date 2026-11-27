import { useState } from "react";
import { api, HOURS, localISO, MAKERSPACE_EMAIL } from "../api";
import { Card, CopyButton, ErrorNote, Field, Notice, Pre, useAction } from "../components/ui";
import type { Profile } from "../profile";

const PURPOSES = [
  { value: "프로토타입", label: "프로토타입 · 빠르게" },
  { value: "일반", label: "일반 · 균형" },
  { value: "세밀", label: "세밀 · 소품" },
  { value: "강도", label: "강도 · 기능/조립 부품" },
  { value: "미니어처", label: "미니어처 · 피규어" },
];

export default function PrintPrepPage({ profile }: { profile: Profile }) {
  // 1. 파일 검사
  const [file, setFile] = useState("");
  const validate = useAction(api.validateGcode);
  const fmt = useAction(api.checkFilename);

  // 2. 파일명
  const [date, setDate] = useState(localISO(1));
  const [hour, setHour] = useState<number>(13);
  const [name, setName] = useState(profile.name);
  const build = useAction(api.buildFilename);

  // 3. 슬라이싱
  const [purpose, setPurpose] = useState("일반");
  const [overhang, setOverhang] = useState(false);
  const slicer = useAction(api.slicer);

  // 4. 이메일
  const [resId, setResId] = useState("");
  const [special, setSpecial] = useState("");
  const draft = useAction(api.emailDraft);

  const checkFile = async (f: string) => {
    setFile(f);
    if (!f.trim()) return;
    const v = await validate.run(f.trim());
    if (v?.is_valid) fmt.run(f.trim());
    else fmt.setData(null);
  };

  const generatedName = build.data?.is_valid ? build.data.filename : "";

  return (
    <div className="stack">
      <div className="steps">
        <span>① 파일 검사</span><span>② 파일명 규칙</span><span>③ 슬라이싱 설정</span><span>④ 출력 요청 메일</span>
      </div>
      <div className="grid-2">
        <Card title="① 파일 형식 검사" subtitle="메이커스페이스는 3DWOX1에서 슬라이싱한 .gcode 파일만 접수합니다.">
          <Field label="파일 선택" hint="파일은 업로드되지 않고, 파일명만 검사합니다.">
            <input type="file" onChange={(e) => checkFile(e.target.files?.[0]?.name ?? "")} />
          </Field>
          <Field label="또는 파일명 입력">
            <div className="row">
              <input value={file} onChange={(e) => setFile(e.target.value)} placeholder="model.stl / 20261130_13_강채린.gcode" />
              <button className="btn" disabled={!file.trim()} onClick={() => checkFile(file)}>검사</button>
            </div>
          </Field>
          <ErrorNote error={validate.error} />
          {validate.data && (
            <>
              <Notice tone={validate.data.is_valid ? "ok" : "error"}>
                <span className="pre-line">{validate.data.message}</span>
              </Notice>
              {validate.data.conversion_guide && <Pre>{validate.data.conversion_guide.trim()}</Pre>}
            </>
          )}
          {fmt.data && (
            <Notice tone={fmt.data.is_valid ? "ok" : "warn"}>
              <span className="pre-line">{fmt.data.message}</span>
              {!fmt.data.is_valid && <div className="small">→ ②에서 올바른 파일명을 생성하세요.</div>}
            </Notice>
          )}
        </Card>

        <Card title="② 파일명 자동 생성" subtitle="규칙: 출력날짜_시간_이름.gcode">
          <div className="row-3">
            <Field label="출력 날짜"><input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></Field>
            <Field label="시간">
              <select value={hour} onChange={(e) => setHour(Number(e.target.value))}>
                {HOURS.map((h) => <option key={h} value={h}>{h}시</option>)}
              </select>
            </Field>
            <Field label="이름"><input value={name} onChange={(e) => setName(e.target.value)} placeholder="강채린" /></Field>
          </div>
          <button className="btn btn-primary" disabled={!date || !name.trim() || build.loading}
            onClick={() => build.run({ print_date: date, print_hour: hour, student_name: name })}>
            파일명 만들기
          </button>
          <ErrorNote error={build.error} />
          {build.data && (build.data.is_valid ? (
            <div className="filename-box">
              <code>{build.data.filename}</code>
              <CopyButton text={build.data.filename} />
            </div>
          ) : <Notice tone="warn">{build.data.message}</Notice>)}
        </Card>

        <Card title="③ 슬라이싱 설정 추천" subtitle="PLA 고정 · 신도리코 3DWOX1 기준">
          <div className="row-2">
            <Field label="출력 목적">
              <select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
                {PURPOSES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </Field>
            <label className="check">
              <input type="checkbox" checked={overhang} onChange={(e) => setOverhang(e.target.checked)} />
              돌출부(오버행)가 있어요
            </label>
          </div>
          <button className="btn" disabled={slicer.loading} onClick={() => slicer.run(purpose, overhang)}>추천 받기</button>
          <ErrorNote error={slicer.error} />
          {slicer.data && (
            <>
              <div className="stats">
                <Stat k="레이어 높이" v={`${slicer.data.layer_height_mm} mm`} />
                <Stat k="인필" v={`${slicer.data.infill_percent}%`} />
                <Stat k="속도" v={`${slicer.data.print_speed_mm_s} mm/s`} />
                <Stat k="서포트" v={slicer.data.support ? "켜기" : "끄기"} />
                <Stat k="브림" v={slicer.data.brim ? "켜기" : "끄기"} />
                <Stat k="필라멘트" v="PLA" />
              </div>
              <p className="muted small">{slicer.data.note}</p>
              <Notice tone="info">{slicer.data.three_dwox1_tip}</Notice>
            </>
          )}
        </Card>

        <Card title="④ 출력 요청 이메일 초안" subtitle={`수신: ${MAKERSPACE_EMAIL} · 초안만 생성하며 발송은 직접 합니다.`}>
          {!generatedName && <Notice tone="warn">먼저 ②에서 파일명을 생성하세요.</Notice>}
          <div className="row-2">
            <Field label="예약번호 (선택)"><input inputMode="numeric" value={resId} onChange={(e) => setResId(e.target.value.replace(/\D/g, ""))} /></Field>
            <Field label="특이사항 (선택)"><input value={special} onChange={(e) => setSpecial(e.target.value)} placeholder="예: 서포트 제거 부탁드려요" /></Field>
          </div>
          <button className="btn btn-primary" disabled={!generatedName || draft.loading}
            onClick={() => draft.run({
              student_name: name, print_date: date, print_hour: hour, gcode_filename: generatedName,
              reservation_id: Number(resId) || 0, special_requests: special,
            })}>
            초안 작성
          </button>
          <ErrorNote error={draft.error} />
          {draft.data && (
            <div className="email">
              <div className="email-meta">
                <div><span className="muted">받는 사람</span> {draft.data.to}</div>
                <div><span className="muted">제목</span> {draft.data.subject}</div>
                <div><span className="muted">첨부</span> {generatedName}</div>
              </div>
              <Pre>{draft.data.body}</Pre>
              <div className="row">
                <CopyButton text={draft.data.body} label="본문 복사" />
                <a className="btn btn-sm"
                  href={`mailto:${draft.data.to}?subject=${encodeURIComponent(draft.data.subject)}&body=${encodeURIComponent(draft.data.body)}`}>
                  메일 앱에서 열기
                </a>
              </div>
              <p className="muted small">메일 앱에서 .gcode 파일을 직접 첨부해 주세요.</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div className="stat">
      <span className="muted small">{k}</span>
      <strong>{v}</strong>
    </div>
  );
}
