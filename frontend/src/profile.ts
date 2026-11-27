import { useEffect, useState } from "react";

// 이름·이메일만 브라우저에 저장 (학번·비밀번호는 절대 받지 않음 — 이용수칙)
export interface Profile {
  name: string;
  email: string;
}

const KEY = "makerspace.profile";

export function useProfile() {
  const [profile, setProfile] = useState<Profile>(() => {
    try {
      return { name: "", email: "", ...JSON.parse(localStorage.getItem(KEY) || "{}") };
    } catch {
      return { name: "", email: "" };
    }
  });
  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(profile));
  }, [profile]);
  return [profile, setProfile] as const;
}
