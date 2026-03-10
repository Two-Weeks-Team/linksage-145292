export async function fetchItems(): Promise<any[]> {
  const res = await fetch("/api/links");
  if (!res.ok) {
    throw new Error("Failed to fetch bookmarks");
  }
  return await res.json();
}

export async function summarize(url: string): Promise<string> {
  const res = await fetch("/api/summarize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error?.message ?? "Summarization failed");
  }
  const data = await res.json();
  return data.summary;
}

export async function generateTags(url: string): Promise<string[]> {
  const res = await fetch("/api/generate-tags", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error?.message ?? "Tag generation failed");
  }
  const data = await res.json();
  return data.tags;
}
