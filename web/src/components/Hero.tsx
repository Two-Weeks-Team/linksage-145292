"use client";

import { useState } from "react";
import { summarize, generateTags } from "@/lib/api";
import TagBadge from "@/components/TagBadge";

export default function Hero() {
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState<string | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError(null);
    try {
      const [generatedSummary, generatedTags] = await Promise.all([
        summarize(url),
        generateTags(url)
      ]);
      setSummary(generatedSummary);
      setTags(generatedTags);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="w-full max-w-2xl space-y-6">
      <h1 className="text-4xl font-bold text-primary text-center">
        Transform links into insights
      </h1>
      <p className="text-center text-muted">
        Paste a URL, let LinkSage summarize and tag it instantly.
      </p>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="url"
          placeholder="https://example.com/article"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 rounded-md border border-border bg-card px-4 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-primary px-5 py-2 text-white transition-transform hover:scale-105 disabled:opacity-50"
        >
          {loading ? "Processing…" : "Analyze"}
        </button>
      </form>
      {error && (
        <div className="rounded bg-warning/10 p-3 text-warning">
          {error}
        </div>
      )}
      {summary && (
        <div className="animate-fade-in rounded bg-card p-4 shadow-md">
          <h2 className="mb-2 text-xl font-semibold text-foreground">
            Summary
          </h2>
          <p className="text-muted whitespace-pre-wrap">{summary}</p>
        </div>
      )}
      {tags.length > 0 && (
        <div className="animate-fade-in rounded bg-card p-4 shadow-md">
          <h2 className="mb-2 text-xl font-semibold text-foreground">
            Suggested Tags
          </h2>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <TagBadge key={tag} tag={tag} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
