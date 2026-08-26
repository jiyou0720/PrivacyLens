import { describe, expect, it } from "vitest";
import { budgetDocuments } from "./documentBudget";

describe("document budget", () => {
  it("preserves retention clauses beyond the old per-document limit", () => {
    const source = "가".repeat(16000) + "회원 탈퇴 시 파기";
    const result = budgetDocuments("회원가입", [{ url: "https://example.com", text: source }]);
    expect(result.text).toContain("회원 탈퇴 시 파기");
    expect(result.truncated).toBe(false);
  });
  it("marks both partially included and omitted documents", () => {
    const result = budgetDocuments("가입", [
      { url: "https://a.test", text: "가".repeat(200) },
      { url: "https://b.test", text: "나".repeat(200) },
    ], 100);
    expect(result.text.length).toBe(100);
    expect(result.clippedUrls).toEqual(["https://a.test", "https://b.test"]);
    expect(result.truncated).toBe(true);
  });
});
