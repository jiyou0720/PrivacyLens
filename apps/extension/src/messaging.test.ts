import { beforeEach, describe, expect, it, vi } from "vitest";
import type { PageScanResult } from "@privacylens/contracts";
import { requestPageScan } from "./messaging";

const result: PageScanResult = {
  schemaVersion: "1.0", requestId: "request-ok", scannedAt: "2026-08-12T00:00:00.000Z",
  page: { domain: "example.com", url: "https://example.com/signup", title: "가입" },
  fields: [], consents: [], warnings: [],
  analysisText: "개인정보 수집 동의 테스트 문구입니다.",
  privacy: { inputValuesCollected: false, fullHtmlCollected: false },
};

describe("requestPageScan", () => {
  beforeEach(() => {
    vi.stubGlobal("chrome", {
      tabs: { query: vi.fn().mockResolvedValue([{ id: 7, url: "https://example.com/signup" }]) },
      scripting: { executeScript: vi.fn().mockResolvedValue([{ result }]) },
      runtime: { sendMessage: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("requestId가 포함된 성공 응답을 반환하고 공유한다", async () => {
    const response = await requestPageScan("request-ok");
    expect(response).toEqual({ type: "PAGE_SCAN_COMPLETED", requestId: "request-ok", payload: result });
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith({ type: "PAGE_SCAN_STARTED", requestId: "request-ok" });
    expect(chrome.runtime.sendMessage).toHaveBeenLastCalledWith(response);
  });

  it("Chrome 내부 페이지는 명시적인 실패 코드로 반환한다", async () => {
    vi.mocked(chrome.tabs.query).mockResolvedValue([
      { id: 8, url: "chrome://extensions" } as chrome.tabs.Tab,
    ]);
    const response = await requestPageScan("request-failed");
    expect(response).toMatchObject({
      type: "PAGE_SCAN_FAILED", requestId: "request-failed",
      error: { code: "UNSUPPORTED_PAGE" },
    });
  });
});
