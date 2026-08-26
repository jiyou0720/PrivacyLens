import type { DetectedField } from "@privacylens/contracts";

type Item = { original_name: string; normalized_name: string; collection_context?: string; applies_to_current_function?: boolean | null };
const labels: Record<string, string> = {
  name: "이름", email: "이메일", phone: "휴대전화번호", address: "주소",
  birth_date: "생년월일", gender: "성별", nickname: "닉네임", location: "위치정보",
  payment: "결제정보", identifier: "고유식별정보", password: "비밀번호 필드", unknown: "확인 필요",
};
const requirements = { required: "필수", optional: "선택", unknown: "필수 여부 확인 필요" };
const canonical = (name: string) => {
  const key = name.toLowerCase().replace(/[\s_-]/g, "");
  const aliases: Record<string, string> = {
    email: "이메일", emailaddress: "이메일", 이메일: "이메일", 이메일주소: "이메일", 전자우편: "이메일",
    nickname: "닉네임", 닉네임: "닉네임", 별명: "닉네임",
    name: "이름", 이름: "이름", 성명: "이름",
    phone: "휴대전화번호", 휴대전화번호: "휴대전화번호", 휴대폰번호: "휴대전화번호",
    birthdate: "생년월일", 생년월일: "생년월일", gender: "성별", 성별: "성별",
  };
  return aliases[key] ?? name;
};

export function fieldLabels(items: Item[], fields: DetectedField[]): Map<string, string> {
  const groups = new Map<string, { label: string; notes: Set<string> }>();
  for (const item of items) {
    if (/비밀번호|password/i.test(`${item.original_name} ${item.normalized_name}`)) continue;
    // Only exact aliases are merged: compound/conditional items retain their scope.
    const key = canonical(item.original_name);
    const group = groups.get(key) ?? { label: key, notes: new Set<string>() };
    group.notes.add(`${item.collection_context || "동의문 명시"}${item.applies_to_current_function === false ? " (다른 기능)" : ""}`);
    groups.set(key, group);
  }
  const formRequirements = new Map<string, Set<string>>();
  for (const field of fields) {
    const key = labels[field.category] ?? "확인 필요";
    const values = formRequirements.get(key) ?? new Set<string>();
    values.add(requirements[field.requirement]);
    formRequirements.set(key, values);
  }
  for (const [key, values] of formRequirements) {
    const group = groups.get(key) ?? { label: key, notes: new Set<string>() };
    group.notes.add(`입력창: ${Array.from(values).join(" / ")}`);
    groups.set(key, group);
  }
  return new Map(Array.from(groups, ([key, group]) => [key, `${group.label} · ${Array.from(group.notes).join(" · ")}`]));
}
