export interface ScanResult {
  domain: string;
  dataTypes: string[];
  policyLinks: string[];
  preselectedConsents: string[];
}

export function scanPage(): ScanResult {
  const patterns: Array<[RegExp, string]> = [
    [/email|e-mail|이메일/i, "이메일"],
    [/tel|phone|mobile|휴대.*전화|전화번호/i, "휴대전화번호"],
    [/birth|birthday|생년월일/i, "생년월일"],
    [/address|주소/i, "주소"],
    [/name|이름|성명/i, "이름"],
  ];
  const fields = [...document.querySelectorAll<HTMLInputElement>("input, select, textarea")];
  const dataTypes = new Set<string>();
  for (const field of fields) {
    const label = field.labels ? [...field.labels].map((item) => item.textContent).join(" ") : "";
    const hint = [field.type, field.name, field.id, field.placeholder, label].join(" ");
    patterns.forEach(([pattern, type]) => pattern.test(hint) && dataTypes.add(type));
  }
  const policyLinks = [...document.querySelectorAll<HTMLAnchorElement>("a[href]")]
    .filter((link) => /개인정보|privacy|수집.?이용|제3자.?제공/i.test(link.textContent ?? ""))
    .map((link) => link.href);
  const preselectedConsents = fields
    .filter((field) => field.type === "checkbox" && field.checked)
    .map((field) => field.labels?.[0]?.textContent?.trim() ?? field.name)
    .filter((label) => /선택|마케팅|광고|수신/i.test(label));
  return { domain: location.hostname, dataTypes: [...dataTypes], policyLinks, preselectedConsents };
}
