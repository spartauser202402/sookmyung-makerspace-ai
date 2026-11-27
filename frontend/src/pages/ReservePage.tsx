import { useEffect, useMemo, useState } from "react";
import { api, formatDate, isToday, DAY_KO, type OverviewCell, type FreeSlots } from "../api";
import { Card, ErrorNote, Field, Notice, useAction } from "../components/ui";
import type { Profile } from "../profile";

const DOW = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const dowOf = (iso: string) => DOW[new Date(iso + "T00:00:00").getDay()];

type Selected = { date: string; hour: number } | null;

export default function ReservePage({ profile, setProfile }: { profile: Profile; setProfile: (p: Profile) => void }) {
  const overview = useAction(api.overview);
  const book = useAction(api.reserve);
  const wait = useAction(api.waitlist);
  const mine = useAction(api.myBookings);
  const cancel = useAction(api.cancel);
  const assign = useAction(api.runAssign);
  const timetable = useAction(api.freeSlots);

  const [selected, setSelected] = useState<Selected>(null);
  const [ttText, setTtText] = useState("");

  const refresh = () => {
    overview.run(7);
    if (profile.email) mine.run(profile.email);
  };
  useEffect(() => {
    overview.run(7);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cells = overview.data?.cells ?? [];
  const hours = overview.data?.hours ?? [11, 13, 15, 17];
  const dates = useMemo(() => [...new Set(cells.map((c) => c.slot_date))], [cells]);
  const cellMap = useMemo(() => {
    const m = new Map<string, OverviewCell>();
    cells.forEach((c) => m.set(`${c.slot_date}|${c.slot_hour}`, c));
    return m;
  }, [cells]);

  const freeSet = useMemo(() => {
    const d = timetable.data as FreeSlots | null;
    return d ? new Set(d.free_slots.map((s) => `${s.day}|${s.hour}`)) : null;
  }, [timetable.data]);

  const sel = selected ? cellMap.get(`${selected.date}|${selected.hour}`) : undefined;
  const isFull = sel ? sel.available === 0 : false;
  const canSubmit = !!selected && profile.name.trim() && /\S+@\S+\.\S+/.test(profile.email);

  const submit = async () => {
    if (!selected) return;
    const base = { student_name: profile.name.trim(), email: profile.email.trim() };
    if (isFull) {
      await wait.run({ slot_date: selected.date, slot_hour: selected.hour, ...base });
    } else {
      const r = await book.run({ target_date: selected.date, target_hour: selected.hour, ...base });
      if (r && !r.success) {
        // 그 사이 만석이 된 경우
        overview.run(7);
      }
    }
    refresh();
  };

  const result = isFull ? wait.data : book.data;

  return (
    <div className="grid-2">
      <div className="stack">
        <Card
          title="예약 현황"
          subtitle="내일부터 7일 · 평일 11/13/15/17시 · 슬롯당 2시간(50분 이용)"
          actions={<button className="btn btn-ghost btn-sm" onClick={refresh}>새로고침</button>}
        >
          <ErrorNote error={overview.error} />
          {overview.loading && !cells.length && <p className="muted">불러오는 중…</p>}
          {cells.length > 0 && (
            <div className="slot-grid" style={{ gridTemplateColumns: `56px repeat(${dates.length}, 1fr)` }}>
              <div />
              {dates.map((d) => (
                <div key={d} className="slot-col-head">{formatDate(d)}</div>
              ))}
              {hours.map((h) => (
                <FragmentRow key={h} hour={h} dates={dates} cellMap={cellMap} freeSet={freeSet}
                  selected={selected} onSelect={setSelected} />
              ))}
            </div>
          )}
          <div className="legend">
            <span><i className="dot dot-ok" /> 예약 가능</span>
            <span><i className="dot dot-low" /> 1대 남음</span>
            <span><i className="dot dot-full" /> 만석 (대기 등록)</span>
            {freeSet && <span><i className="dot dot-free" /> 내 공강</span>}
          </div>
        </Card>

        <Card title="시간표로 공강 찾기" subtitle="에브리타임 등에서 복사한 시간표를 붙여넣으면 수업과 겹치지 않는 슬롯을 표시합니다.">
          <Field label="시간표" hint="예: 운영체제 월 09:00-11:50 목 09:00-11:50 / 자료구조 화 13:00-14:15">
            <textarea rows={3} value={ttText} onChange={(e) => setTtText(e.target.value)}
              placeholder="과목명 요일 HH:MM-HH:MM …" />
          </Field>
          <div className="row">
            <button className="btn" disabled={!ttText.trim() || timetable.loading} onClick={() => timetable.run(ttText)}>
              공강 표시
            </button>
            {timetable.data && (
              <button className="btn btn-ghost" onClick={() => { timetable.setData(null); setTtText(""); }}>지우기</button>
            )}
          </div>
          <ErrorNote error={timetable.error} />
          {timetable.data && (
            <Notice tone="info">
              {timetable.data.free_slots.length}개 공강 슬롯 ·{" "}
              {Object.entries(groupByDay(timetable.data.free_slots)).map(([d, hs]) => `${DAY_KO[d]} ${hs.join("/")}시`).join(", ") || "없음"}
            </Notice>
          )}
        </Card>
      </div>

      <div className="stack">
        <Card title={isFull ? "대기 등록" : "예약하기"} subtitle="학번·비밀번호는 받지 않습니다. 이름과 알림용 이메일만 입력하세요.">
          <div className="selected-box">
            {selected ? (
              <>
                <strong>{formatDate(selected.date)} {selected.hour}:00</strong>
                <span className={`badge ${isFull ? "badge-full" : "badge-ok"}`}>
                  {isFull ? `만석 · 대기 ${sel?.waiting ?? 0}명` : `${sel?.available}/${sel?.machines}대 가능`}
                </span>
                {freeSet && !freeSet.has(`${dowOf(selected.date)}|${selected.hour}`) && (
                  <span className="badge badge-warn">수업과 겹침</span>
                )}
              </>
            ) : (
              <span className="muted">왼쪽 표에서 시간을 선택하세요.</span>
            )}
          </div>
          <Field label="이름">
            <input value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} placeholder="강채린" />
          </Field>
          <Field label="이메일">
            <input type="email" value={profile.email} onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              placeholder="you@sookmyung.ac.kr" />
          </Field>
          <button className="btn btn-primary btn-block" disabled={!canSubmit || book.loading || wait.loading} onClick={submit}>
            {isFull ? "대기열에 등록" : "예약 확정"}
          </button>
          <ErrorNote error={book.error || wait.error} />
          {result && <Notice tone={result.success ? "ok" : "warn"}>{result.message}</Notice>}
          <ul className="rules">
            <li>당일 취소 불가</li>
            <li>예약 10분 이내 미방문 3회 누적 시 1개월 이용 정지</li>
            <li>출력 파일은 <b>.gcode</b>만, 필라멘트는 <b>PLA</b> 고정</li>
          </ul>
        </Card>

        <Card
          title="내 예약"
          actions={
            <button className="btn btn-ghost btn-sm" disabled={!profile.email} onClick={() => mine.run(profile.email)}>
              조회
            </button>
          }
        >
          {!profile.email && <p className="muted">이메일을 입력하면 예약을 조회할 수 있습니다.</p>}
          <ErrorNote error={mine.error || cancel.error} />
          {cancel.data && <Notice tone={cancel.data.success ? "ok" : "warn"}>{cancel.data.message}</Notice>}
          {mine.data && (
            <ul className="list">
              {mine.data.reservations.map((r) => (
                <li key={`r${r.reservation_id}`} className={r.status === "cancelled" ? "dim" : ""}>
                  <div>
                    <strong>{formatDate(r.slot_date)} {r.slot_hour}시</strong> · 장비 {r.machine_no}번
                    <div className="muted small">예약번호 {r.reservation_id}</div>
                  </div>
                  {r.status === "confirmed" ? (
                    <button className="btn btn-danger btn-sm" disabled={isToday(r.slot_date) || cancel.loading}
                      title={isToday(r.slot_date) ? "당일 취소 불가" : ""}
                      onClick={async () => {
                        if (!confirm(`예약번호 ${r.reservation_id}을(를) 취소할까요?`)) return;
                        await cancel.run(r.reservation_id);
                        refresh();
                      }}>
                      취소
                    </button>
                  ) : (
                    <span className="badge">취소됨</span>
                  )}
                </li>
              ))}
              {mine.data.waitlist.map((w) => (
                <li key={`w${w.waitlist_id}`} className={w.status !== "waiting" ? "dim" : ""}>
                  <div>
                    <strong>{formatDate(w.slot_date)} {w.slot_hour}시</strong> · 대기
                    <div className="muted small">대기번호 {w.waitlist_id}</div>
                  </div>
                  <span className={`badge ${w.status === "assigned" ? "badge-ok" : "badge-warn"}`}>
                    {w.status === "waiting" ? "대기 중" : w.status === "assigned" ? "배정됨" : "만료"}
                  </span>
                </li>
              ))}
              {!mine.data.reservations.length && !mine.data.waitlist.length && <li className="muted">예약 내역이 없습니다.</li>}
            </ul>
          )}
        </Card>

        <Card title="대기자 자동 배정" subtitle="취소로 생긴 빈자리에 대기 순서대로 배정합니다 (WxO Monitor가 5~10분마다 실행).">
          <button className="btn" disabled={assign.loading} onClick={async () => { await assign.run(); refresh(); }}>
            지금 실행
          </button>
          <ErrorNote error={assign.error} />
          {assign.data && <Notice tone="info">{assign.data.message}</Notice>}
        </Card>
      </div>
    </div>
  );
}

function FragmentRow({ hour, dates, cellMap, freeSet, selected, onSelect }: {
  hour: number;
  dates: string[];
  cellMap: Map<string, OverviewCell>;
  freeSet: Set<string> | null;
  selected: Selected;
  onSelect: (s: Selected) => void;
}) {
  return (
    <>
      <div className="slot-row-head">{hour}:00</div>
      {dates.map((d) => {
        const c = cellMap.get(`${d}|${hour}`);
        if (!c) return <div key={d} className="slot-cell slot-none">—</div>;
        const state = c.available === 0 ? "full" : c.available === 1 ? "low" : "ok";
        const free = freeSet?.has(`${dowOf(d)}|${hour}`);
        const isSel = selected?.date === d && selected.hour === hour;
        return (
          <button
            key={d}
            className={`slot-cell slot-${state} ${isSel ? "is-selected" : ""} ${freeSet && !free ? "is-busy" : ""} ${free ? "is-free" : ""}`}
            onClick={() => onSelect({ date: d, hour })}
            aria-label={`${formatDate(d)} ${hour}시, ${c.available}대 가능`}
          >
            <span className="slot-num">{c.available === 0 ? "만석" : `${c.available}/${c.machines}`}</span>
            {c.waiting > 0 && <span className="slot-sub">대기 {c.waiting}</span>}
          </button>
        );
      })}
    </>
  );
}

function groupByDay(slots: { day: string; hour: number }[]) {
  const g: Record<string, number[]> = {};
  slots.forEach((s) => (g[s.day] ??= []).push(s.hour));
  return g;
}
