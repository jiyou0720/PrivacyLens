import type {
  ConsentCategory,
  ConsentItem,
  DetectedField,
  DetectionStatus,
  DetectionWarning,
  ElementEvidence,
  PageScanResult,
  PersonalDataCategory,
  Requirement,
} from "@privacylens/contracts";

/**
 * Runs inside the inspected page through chrome.scripting.executeScript.
 * Keep this function self-contained: Chrome serializes only this function body.
 */
export function scanPage(requestId: string): PageScanResult {
  type FormControl = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

  const normalize = (text: string | null | undefined): string =>
    (text ?? "").replace(/\s+/g, " ").trim().slice(0, 300);

  const stableId = (prefix: string, index: number, element: Element): string => {
    const explicitId = normalize(element.getAttribute("id"));
    return explicitId ? `${prefix}-${explicitId.replace(/[^a-zA-Z0-9_-]/g, "-")}` : `${prefix}-${index + 1}`;
  };

  const visibleTextWithoutControls = (element: Element | null): string => {
    if (!element) return "";
    const clone = element.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("input, textarea, select, script, style").forEach((node) => node.remove());
    return normalize(clone.textContent);
  };

  const labelText = (control: FormControl): string => {
    const nativeLabels = "labels" in control && control.labels
      ? Array.from(control.labels).map((label) => visibleTextWithoutControls(label)).join(" ")
      : "";
    const labelledBy = normalize(control.getAttribute("aria-labelledby"))
      .split(" ")
      .filter(Boolean)
      .map((id) => visibleTextWithoutControls(document.getElementById(id)))
      .join(" ");
    return normalize([nativeLabels, control.getAttribute("aria-label"), labelledBy].join(" "));
  };

  const nearbyText = (control: FormControl): string => {
    const container = control.closest("label, fieldset, [role='group'], .field, .form-group, li, tr, div");
    return visibleTextWithoutControls(container);
  };

  const hintFor = (control: FormControl): string => normalize([
    control.tagName,
    control.getAttribute("type"),
    control.getAttribute("name"),
    control.getAttribute("id"),
    control.getAttribute("autocomplete"),
    control.getAttribute("placeholder"),
    labelText(control),
    nearbyText(control),
  ].join(" ")).toLowerCase();

  const fieldRules: Array<[PersonalDataCategory, RegExp, boolean]> = [
    ["email", /\bemail\b|e-mail|이메일|전자우편/, true],
    ["phone", /\btel\b|phone|mobile|휴대\s*전화|전화번호|연락처/, true],
    ["birth_date", /birth|birthday|date-of-birth|생년월일|생일/, true],
    ["address", /address|street-address|postal|우편번호|주소/, true],
    ["name", /\bname\b|given-name|family-name|성명|이름/, true],
    ["gender", /gender|sex|성별/, false],
    ["nickname", /nickname|user.?name|닉네임|별명/, false],
    ["location", /location|latitude|longitude|위치정보|현재 위치/, false],
    ["payment", /credit.?card|cc-number|payment|카드번호|결제정보/, false],
    ["identifier", /resident|national.?id|주민등록번호|외국인등록번호|고유식별/, false],
    ["password", /password|new-password|current-password|비밀번호/, true],
  ];

  const classifyField = (control: FormControl): [PersonalDataCategory, DetectionStatus] => {
    const hint = hintFor(control);
    const type = control.getAttribute("type")?.toLowerCase();
    if (type === "email") return ["email", "confirmed"];
    if (type === "tel") return ["phone", "confirmed"];
    if (type === "password") return ["password", "confirmed"];
    const match = fieldRules.find(([, pattern]) => pattern.test(hint));
    return match ? [match[0], match[2] ? "confirmed" : "inferred"] : ["unknown", "needs_review"];
  };

  const requirementOf = (control: FormControl, text: string): Requirement => {
    if (control.required || control.getAttribute("aria-required") === "true") return "required";
    if (/(^|[\s[(])필수([\s)\]]|$)|required|\*/i.test(text)) return "required";
    if (/(^|[\s[(])선택([\s)\]]|$)|optional/i.test(text)) return "optional";
    return "unknown";
  };

  const evidenceFor = (control: FormControl): ElementEvidence => ({
    label: labelText(control) || undefined,
    attributes: {
      tagName: control.tagName.toLowerCase() as "input" | "select" | "textarea",
      type: control.getAttribute("type") ?? undefined,
      name: control.getAttribute("name") ?? undefined,
      id: control.getAttribute("id") ?? undefined,
      autocomplete: control.getAttribute("autocomplete") ?? undefined,
      placeholder: control.getAttribute("placeholder") ?? undefined,
      required: control.required || undefined,
      ariaRequired: control.getAttribute("aria-required") === "true" || undefined,
    },
    nearbyText: nearbyText(control) || undefined,
  });

  const consentCategory = (text: string): ConsentCategory => {
    if (/전체\s*동의|모두\s*동의|agree.?all/i.test(text)) return "all";
    if (/제\s*3\s*자|third.?party/i.test(text)) return "third_party_sharing";
    if (/마케팅|광고|프로모션|이벤트|수신|marketing/i.test(text)) return "marketing";
    if (/위치정보|location/i.test(text)) return "location";
    if (/개인정보.{0,12}(수집|이용)|수집.{0,5}이용|privacy/i.test(text)) return "privacy_collection";
    if (/이용약관|서비스\s*약관|terms/i.test(text)) return "terms";
    return "unknown";
  };

  const allControls = Array.from(document.querySelectorAll<FormControl>("input, select, textarea"));
  const nativeConsents = allControls.filter(
    (control): control is HTMLInputElement => control instanceof HTMLInputElement && control.type === "checkbox",
  );
  const nativeConsentSet = new Set(nativeConsents);
  const ignoredInputTypes = new Set(["hidden", "button", "submit", "reset", "image"]);

  const fields: DetectedField[] = allControls
    .filter((control) => !nativeConsentSet.has(control as HTMLInputElement))
    .filter((control) => !(control instanceof HTMLInputElement && ignoredInputTypes.has(control.type)))
    .map((control, index) => {
      const [category, status] = classifyField(control);
      const text = normalize(`${labelText(control)} ${nearbyText(control)}`);
      return {
        id: stableId("field", index, control),
        category,
        requirement: requirementOf(control, text),
        status,
        evidence: evidenceFor(control),
      };
    })
    .filter((field) => field.category !== "unknown");

  const customConsents = Array.from(document.querySelectorAll<HTMLElement>("[role='checkbox'], [aria-checked]"))
    .filter((element) => !(element instanceof HTMLInputElement))
    .filter((element, index, elements) => !elements.some((other, otherIndex) => otherIndex !== index && other.contains(element)));
  const consentElements: Element[] = [...nativeConsents, ...customConsents];

  const consents: ConsentItem[] = consentElements.map((element, index) => {
    const native = element instanceof HTMLInputElement ? element : null;
    const container = element.closest("label, fieldset, li, [role='group'], div");
    const title = native
      ? labelText(native) || nearbyText(native) || native.name || `동의 항목 ${index + 1}`
      : visibleTextWithoutControls(container) || normalize(element.getAttribute("aria-label")) || `동의 항목 ${index + 1}`;
    const category = consentCategory(title);
    const relatedLink = container?.querySelector<HTMLAnchorElement>("a[href]");
    const requirement = native
      ? requirementOf(native, title)
      : /(^|[\s[(])필수([\s)\]]|$)|required|\*/i.test(title)
        ? "required"
        : /(^|[\s[(])선택([\s)\]]|$)|optional/i.test(title) ? "optional" : "unknown";
    return {
      id: stableId("consent", index, element),
      category,
      title,
      requirement,
      checkedByDefault: native ? native.defaultChecked : element.getAttribute("aria-checked") === "true",
      disabled: native ? native.disabled : element.getAttribute("aria-disabled") === "true",
      status: category === "unknown" ? "needs_review" : "confirmed",
      documentUrl: relatedLink?.href,
    };
  });
  const preselectedOptional = consents.filter(
    (consent) => consent.checkedByDefault && consent.requirement === "optional",
  );
  const warnings: DetectionWarning[] = preselectedOptional.length
    ? [{
        ruleId: "preselected-optional-consent",
        severity: "warning",
        message: "선택 동의 항목이 기본으로 선택되어 있습니다. 필요한 동의인지 확인해 보세요.",
        evidenceIds: preselectedOptional.map((consent) => consent.id),
      }]
    : [];

  const analysisParts = [
    document.title,
    ...fields.flatMap((field) => [field.evidence.label, field.evidence.nearbyText]),
    ...consents.map((consent) => consent.title),
    ...Array.from(document.querySelectorAll<HTMLElement>(
      "[class*=privacy i], [id*=privacy i], [class*=consent i], [id*=consent i], [class*=agree i], [id*=agree i]",
    )).map((element) => visibleTextWithoutControls(element)),
  ].filter((part): part is string => Boolean(part));
  const analysisText = Array.from(new Set(analysisParts))
    .join("\n")
    .replace(/\s+\n/g, "\n")
    .slice(0, 20_000);

  return {
    schemaVersion: "1.0",
    requestId,
    scannedAt: new Date().toISOString(),
    page: { domain: location.hostname, url: location.href, title: document.title },
    fields,
    consents,
    warnings,
    analysisText,
    privacy: { inputValuesCollected: false, fullHtmlCollected: false },
  };
}
