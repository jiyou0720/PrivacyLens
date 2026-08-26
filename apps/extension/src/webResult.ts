const WEB_URL = "https://privacylens.site/";

// Called only by the user's button. No analysis request or server-side storage.
export async function openWebResult(payload: unknown) {
  const serialized = JSON.stringify(payload);
  if (serialized.length > 2_000_000) throw new Error("전달할 분석 결과가 너무 큽니다.");
  const id = crypto.randomUUID();
  const existing = await chrome.tabs.query({ url: `${WEB_URL}*`, currentWindow: true });
  const tab = existing[0] ?? await chrome.tabs.create({ url: WEB_URL, active: false });
  if (tab.id === undefined) throw new Error("웹 결과 탭을 열지 못했습니다.");
  const tabId = tab.id;
  await new Promise<void>((resolve, reject) => {
    const cleanup = () => { clearTimeout(timer); chrome.tabs.onUpdated.removeListener(listener); };
    const listener = (changedId: number, info: chrome.tabs.TabChangeInfo) => {
      if (changedId === tabId && info.status === "complete") { cleanup(); resolve(); }
    };
    const timer = setTimeout(() => { cleanup(); reject(new Error("웹페이지 로딩 시간이 초과되었습니다. 다시 시도해주세요.")); }, 20000);
    chrome.tabs.onUpdated.addListener(listener);
    void chrome.tabs.get(tabId).then((current) => {
      if (current.status === "complete") { cleanup(); resolve(); }
    }).catch((error) => { cleanup(); reject(error); });
  });
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    // sessionStorage must be written in the page's world so the dashboard can
    // consume it. The default isolated world is intentionally separate.
    world: "MAIN",
    func: (key: string, value: string) => {
      if (location.origin !== "https://privacylens.site") throw new Error("결과 전달 대상 주소가 다릅니다.");
      sessionStorage.setItem(`privacylens-result:${key}`, value);
      const nextHash = `analysis=${key}`;
      if (location.hash === `#${nextHash}`) location.hash = "";
      location.hash = nextHash;
      return true;
    },
    args: [id, serialized],
  });
  if (!results[0]?.result) throw new Error("분석 결과를 웹페이지로 전달하지 못했습니다.");
  await chrome.tabs.update(tabId, { active: true });
}
