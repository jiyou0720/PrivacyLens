// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from "vitest";
import { scanPage } from "./scanner";

describe("scanPage", () => {
  beforeEach(() => {
    document.title = "PrivacyLens 샘플 회원가입";
    document.body.innerHTML = "";
    history.replaceState({}, "", "/signup");
  });

  it("개인정보 필드와 필수·선택 상태를 유형별로 탐지한다", () => {
    document.body.innerHTML = `
      <form>
        <label for="full-name">이름 (필수)</label>
        <input id="full-name" name="fullName" autocomplete="name" required />
        <label for="email">이메일</label>
        <input id="email" type="email" value="secret-person@example.com" />
        <div class="form-group"><span>휴대전화번호 선택</span><input name="mobilePhone" type="tel" /></div>
        <label for="address">주소</label><textarea id="address" autocomplete="street-address">비밀 주소</textarea>
        <label for="birthday">생년월일</label><select id="birthday" name="birthDate"><option>1999</option></select>
      </form>`;

    const result = scanPage("request-fields");
    expect(result.fields.map((field) => field.category)).toEqual([
      "name", "email", "phone", "address", "birth_date",
    ]);
    expect(result.fields.map((field) => field.requirement)).toEqual([
      "required", "unknown", "optional", "unknown", "unknown",
    ]);
    expect(result.requestId).toBe("request-fields");
    expect(result.privacy).toEqual({ inputValuesCollected: false, fullHtmlCollected: false });
  });

  it("동의 유형과 기본 선택된 선택 동의 경고를 반환한다", () => {
    document.body.innerHTML = `
      <fieldset>
        <label><input id="privacy" type="checkbox" required /> 개인정보 수집·이용 동의 (필수)</label>
        <label><input id="third-party" type="checkbox" /> 개인정보 제3자 제공 동의</label>
        <label><input id="marketing" type="checkbox" checked /> 마케팅 정보 수신 동의 (선택)</label>
      </fieldset>`;

    const result = scanPage("request-consents");
    expect(result.consents.map((consent) => consent.category)).toEqual([
      "privacy_collection", "third_party_sharing", "marketing",
    ]);
    expect(result.consents[2]).toMatchObject({
      requirement: "optional", checkedByDefault: true, disabled: false,
    });
    expect(result.warnings).toEqual([expect.objectContaining({
      ruleId: "preselected-optional-consent",
      evidenceIds: ["consent-marketing"],
    })]);
  });

  it("aria-label과 aria-required를 사용하고 불확실한 필드는 확인 필요로 둔다", () => {
    document.body.innerHTML = `
      <input id="contact" aria-label="연락처" aria-required="true" />
      <input id="custom" name="profileQuestion" />`;
    const result = scanPage("request-aria");
    expect(result.fields[0]).toMatchObject({ category: "phone", requirement: "required" });
    expect(result.fields).toHaveLength(1);
  });

  it("커스텀 체크박스를 동의 항목으로 탐지하고 숨김 필드를 제외한다", () => {
    document.body.innerHTML = `
      <input type="hidden" name="token" value="secret" />
      <div role="checkbox" aria-checked="false" aria-label="[필수] 개인정보 수집 및 이용 동의"></div>
      <div role="checkbox" aria-checked="true" aria-label="[선택] 마케팅 정보 수신 동의"></div>`;

    const result = scanPage("request-custom-consents");
    expect(result.fields).toEqual([]);
    expect(result.consents).toHaveLength(2);
    expect(result.consents[0]).toMatchObject({ category: "privacy_collection", requirement: "required" });
    expect(result.consents[1]).toMatchObject({ category: "marketing", requirement: "optional", checkedByDefault: true });
  });
  it("같은 출처의 약관 및 개인정보 링크를 수집한다", () => {
    document.body.innerHTML = `
      <a href="/policy/privacy">개인정보 처리방침 보기</a>
      <a href="https://external.example/terms">외부 약관</a>`;
    const result = scanPage("request-documents");
    expect(result.documentUrls).toEqual(["http://localhost:3000/policy/privacy", "https://external.example/terms"]);
  });
  it("이미 입력된 실제 값과 비밀번호를 결과 및 직렬화 데이터에 포함하지 않는다", () => {
    document.body.innerHTML = `
      <label>이메일<input type="email" value="never-leak@example.com" /></label>
      <label>비밀번호<input type="password" value="SuperSecret!234" /></label>
      <label>주소<textarea name="address">서울시 비밀 주소 101호</textarea></label>`;
    const serialized = JSON.stringify(scanPage("request-privacy"));
    expect(serialized).not.toContain("never-leak@example.com");
    expect(serialized).not.toContain("SuperSecret!234");
    expect(serialized).not.toContain("서울시 비밀 주소 101호");
    expect(serialized).not.toContain("outerHTML");
  });
});
