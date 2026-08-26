const WEB_URL = "https://privacylens.site/";

export function encodeExtensionResult(payload: unknown) {
  const serialized = JSON.stringify(payload);
  if (serialized.length > 1_000_000) throw new Error("전달할 분석 결과가 너무 큽니다.");
  const bytes = new TextEncoder().encode(serialized);
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

// The fragment never reaches the web server. The dashboard consumes it and
// immediately removes it from the address bar without another API request.
export async function openWebResult(payload: unknown) {
  const url = `${WEB_URL}#result=${encodeExtensionResult(payload)}`;
  const existing = await chrome.tabs.query({ url: `${WEB_URL}*`, currentWindow: true });
  const tab = existing[0];
  if (tab?.id !== undefined) {
    await chrome.tabs.update(tab.id, { url, active: true });
    return;
  }
  await chrome.tabs.create({ url, active: true });
}
