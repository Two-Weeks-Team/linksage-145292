"use client";

export default function TagBadge({ tag }: { tag: string }) {
  return (
    <span className="rounded-full bg-accent px-3 py-1 text-sm font-medium text-white transition-colors hover:bg-accent/80">
      {tag}
    </span>
  );
}
