import type { ExtensionMessage, PageScanResult, ScanErrorCode } from "@privacylens/contracts";
import { scanPage } from "./scanner";

const supportedProtocols = new Set(["http:", "https:"]);

export function createRequestId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `scan-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export async function requestPageScan(requestId = createRequestId()): Promise<ExtensionMessage> {
  await chrome.runtime.sendMessage({ type: "PAGE_SCAN_STARTED", requestId } satisfies ExtensionMessage).catch(() => undefined);
  try {
    const focusedTabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    const normalTabs = focusedTabs.length
      ? focusedTabs
      : await chrome.tabs.query({ active: true, windowType: "normal" });
    const tab = normalTabs.find((candidate) => {
      if (!candidate.url) return false;
      try { return supportedProtocols.has(new URL(candidate.url).protocol); } catch { return false; }
    }) ?? normalTabs[0];
    if (!tab.id) return failure(requestId, "NO_ACTIVE_TAB", "현재 활성 탭을 찾을 수 없습니다.");
    if (!tab.url || !supportedProtocols.has(new URL(tab.url).protocol)) {
      return failure(requestId, "UNSUPPORTED_PAGE", "이 페이지는 보안상 분석할 수 없습니다.");
    }
    const [{ result }] = await chrome.scripting.executeScript<[string], PageScanResult>({
      target: { tabId: tab.id }, func: scanPage, args: [requestId],
    });
    if (!result) return failure(requestId, "INJECTION_FAILED", "페이지 분석 결과를 받지 못했습니다.");
    const completed: ExtensionMessage = { type: "PAGE_SCAN_COMPLETED", requestId, payload: result };
    await chrome.runtime.sendMessage(completed).catch(() => undefined);
    return completed;
  } catch (cause) {
    return failure(requestId, "INJECTION_FAILED", cause instanceof Error ? cause.message : "알 수 없는 오류가 발생했습니다.");
  }
}

async function failure(requestId: string, code: ScanErrorCode, message: string): Promise<ExtensionMessage> {
  const failed: ExtensionMessage = { type: "PAGE_SCAN_FAILED", requestId, error: { code, message } };
  await chrome.runtime.sendMessage(failed).catch(() => undefined);
  return failed;
}
