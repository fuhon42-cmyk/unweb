"use client";

import { useState } from "react";

interface CopyButtonProps {
  text: string;
  label: string;
}

export default function CopyButton({ text, label }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 text-sm text-zinc-300 transition-colors hover:bg-zinc-700 hover:text-zinc-100"
    >
      {copied ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-4 w-4 text-emerald-400"
        >
          <path
            fillRule="evenodd"
            d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
            clipRule="evenodd"
          />
        </svg>
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-4 w-4"
        >
          <path
            fillRule="evenodd"
            d="M15.988 3.012A2.25 2.25 0 0118 5.25v6.5A2.25 2.25 0 0115.75 14H13.5v-3.379a3 3 0 00-.879-2.121l-3.12-3.121a3 3 0 00-1.402-.791 2.25 2.25 0 012.15-1.176h2.55a2.25 2.25 0 011.75.762l.582.634A.75.75 0 0113.5 4.5h1.784a.75.75 0 01.704.512z"
            clipRule="evenodd"
          />
          <path
            fillRule="evenodd"
            d="M3.75 6A2.25 2.25 0 001.5 8.25v6.5A2.25 2.25 0 003.75 17h5.5A2.25 2.25 0 0011.5 14.75v-3.379a3 3 0 00-.879-2.121l-3.12-3.121a3 3 0 00-1.402-.791 2.252 2.252 0 00-1.625-.328A2.25 2.25 0 003.75 6z"
            clipRule="evenodd"
          />
        </svg>
      )}
      {copied ? "Copied" : label}
    </button>
  );
}
