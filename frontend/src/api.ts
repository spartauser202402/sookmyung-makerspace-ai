// 백엔드(api/server.py) 호출 헬퍼. Vite dev 서버가 /api 를 :8000 으로 프록시합니다.

export const HOURS = [11, 13, 15, 17] as const;
export const MAKERSPACE_EMAIL = "makerspace@sookmyung.ac.kr";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

const qs = (params: Record<string, string | number>) =>
  "?" + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

// ── 타입 ──
export interface OverviewCell {
  slot_date: string;
  slot_hour: number;
  machines: number;
  available: number;
  waiting: number;
}
export interface ReservationResult {
  success: boolean;
  reservation_id: number | null;
  slot_date: string | null;
  slot_hour: number | null;
  machine_no: number | null;
  message: string;
}
export interface WaitlistResult {
  success: boolean;
  waitlist_id: number | null;
  message: string;
}
export interface MyBookings {
  reservations: {
    reservation_id: number;
    status: "confirmed" | "cancelled";
    slot_date: string;
    slot_hour: number;
    machine_no: number;
  }[];
  waitlist: {
    waitlist_id: number;
    status: "waiting" | "assigned" | "expired";
    slot_date: string;
    slot_hour: number;
  }[];
}
export interface FreeSlots {
  free_slots: { day: string; hour: number }[];
  busy_days: string[];
  message: string;
}
export interface GcodeValidation {
  is_valid: boolean;
  filename: string;
  detected_extension: string;
  message: string;
  conversion_guide: string;
}
export interface FilenameResult {
  filename: string;
  is_valid: boolean;
  message: string;
}
export interface SlicerRec {
  filament: string;
  profile_name: string;
  layer_height_mm: number;
  infill_percent: number;
  print_speed_mm_s: number;
  support: boolean;
  brim: boolean;
  note: string;
  three_dwox1_tip: string;
  message: string;
}
export interface EmailDraft {
  to: string;
  subject: string;
  body: string;
  filename_reminder: string;
  message: string;
}
export interface Requirements {
  idea_summary: string;
  estimated_size: string;
  shape_description: string;
  functional_requirement: string;
  pla_feasibility: string;
  recommended_next_step: string;
  message: string;
}
export interface CadTool {
  name: string;
  url: string;
  description: string;
  export: string;
  best_for: string;
}
export interface ModelHit {
  title: string;
  source: string;
  url: string;
  author: string;
  license: string;
  description: string;
}
export interface KbHit {
  document: string;
  section: string;
  snippet: string;
  score: number;
}

// ── 엔드포인트 ──
export const api = {
  health: () => request<{ ok: boolean; db: boolean }>("/api/health"),
  chat: (message: string) => post<{ reply: string }>("/api/chat", { message }),
  overview: (days = 7) => request<{ hours: number[]; cells: OverviewCell[] }>(`/api/slots/overview${qs({ days })}`),
  reserve: (b: { target_date: string; target_hour: number; student_name: string; email: string }) =>
    post<ReservationResult>("/api/reservations", b),
  cancel: (id: number) => request<ReservationResult>(`/api/reservations/${id}`, { method: "DELETE" }),
  myBookings: (email: string) => request<MyBookings>(`/api/reservations${qs({ email })}`),
  waitlist: (b: { slot_date: string; slot_hour: number; student_name: string; email: string }) =>
    post<WaitlistResult>("/api/waitlist", b),
  runAssign: () => post<{ assignments: unknown[]; message: string }>("/api/waitlist/assign", {}),
  freeSlots: (timetable_text: string) => post<FreeSlots>("/api/timetable/free-slots", { timetable_text }),

  validateGcode: (filename: string) => request<GcodeValidation>(`/api/gcode/validate${qs({ filename })}`),
  checkFilename: (filename: string) => request<FilenameResult>(`/api/filename/check${qs({ filename })}`),
  buildFilename: (b: { print_date: string; print_hour: number; student_name: string }) =>
    post<FilenameResult>("/api/filename/build", b),
  slicer: (print_purpose: string, has_overhang: boolean) =>
    post<SlicerRec>("/api/slicer/recommend", { print_purpose, has_overhang }),
  emailDraft: (b: {
    student_name: string;
    print_date: string;
    print_hour: number;
    gcode_filename: string;
    reservation_id?: number;
    special_requests?: string;
  }) => post<EmailDraft>("/api/email/draft", b),

  refineIdea: (b: { idea_description: string; estimated_size_cm: string; primary_function: string }) =>
    post<Requirements>("/api/idea/refine", b),
  cad: (user_level: string, primary_use: string) =>
    request<{ level: string; tools: CadTool[]; note: string }>(`/api/cad/recommend${qs({ user_level, primary_use })}`),
  models: (query: string) =>
    request<{ results: ModelHit[]; is_mock: boolean; message: string }>(`/api/models/search${qs({ query })}`),

  kbList: () => request<{ documents: string[] }>("/api/kb"),
  kbDoc: (name: string) => request<{ name: string; content: string }>(`/api/kb/${encodeURIComponent(name)}`),
  kbSearch: (q: string) => request<{ results: KbHit[] }>(`/api/kb-search${qs({ q })}`),
};

// ── 유틸 ──
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];
export function formatDate(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return `${d.getMonth() + 1}/${d.getDate()} (${WEEKDAYS[d.getDay()]})`;
}
export function localISO(offsetDays = 0) {
  const t = new Date();
  t.setDate(t.getDate() + offsetDays);
  return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`;
}
export const isToday = (iso: string) => iso === localISO();
export const DAY_KO: Record<string, string> = { MON: "월", TUE: "화", WED: "수", THU: "목", FRI: "금" };
