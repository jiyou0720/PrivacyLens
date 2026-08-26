import { expect, it } from "vitest";
import type { DetectedField } from "@privacylens/contracts";
import { fieldLabels } from "./fieldLabels";

const field = (category: DetectedField["category"], requirement: DetectedField["requirement"]): DetectedField => ({
  id: category, category, requirement, status: "confirmed", evidence: { attributes: { tagName: "input" } },
});
it("merges exact email aliases and form evidence without losing context", () => {
  const result = fieldLabels([
    { original_name: "이메일 주소", normalized_name: "email", collection_context: "회원가입" },
    { original_name: "이메일", normalized_name: "email", collection_context: "마케팅", applies_to_current_function: false },
  ], [field("email", "required")]);
  expect(result.size).toBe(1);
  expect(result.get("이메일")).toBe("이메일 · 회원가입 · 마케팅 (다른 기능) · 입력창: 필수");
});
it("localizes requirements and keeps compound data separate", () => {
  const result = fieldLabels([
    { original_name: "프로필 정보(별명, 사진)", normalized_name: "nickname" },
  ], [field("nickname", "optional"), field("password", "required"), field("email", "unknown")]);
  expect(result.size).toBe(4);
  expect(result.get("닉네임")).toContain("선택");
  expect(result.get("비밀번호 필드")).toContain("필수");
  expect(result.get("이메일")).toContain("필수 여부 확인 필요");
});
