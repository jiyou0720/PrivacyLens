// Keep full linked documents where possible; never silently label a clipped
// document as complete. Reserve the API's existing 100k character budget.
export function budgetDocuments(page: string, documents: Array<{ url: string; text: string }>, limit = 100_000) {
  let text = page.slice(0, limit);
  let truncated = page.length > limit;
  const clippedUrls: string[] = [];
  for (const document of documents) {
    const part = `\n\n[연결 문서: ${document.url}]\n${document.text}`;
    const remaining = Math.max(0, limit - text.length);
    if (part.length > remaining) {
      truncated = true;
      clippedUrls.push(document.url);
    }
    text += part.slice(0, remaining);
  }
  return { text, truncated, clippedUrls };
}
