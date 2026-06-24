export default function DocsPage() {
  const base = 'https://unweb-production-6f69.up.railway.app';
  const eps = [
    ['GET', '/api/v1/health', 'Health check'],
    ['POST', '/api/v1/extract', 'Extract structured content from a URL. Body: url, use_llm'],
    ['POST', '/api/v1/search', 'Search web + LLM summarize. Body: query, max_results'],
    ['POST', '/api/v1/publish', 'Register site for AI access. Body: url, site_name, content'],
    ['GET', '/llms/{name}', 'Public AI-readable endpoint (no auth)'],
    ['GET', '/api/v1/metrics', 'Usage dashboard (auth required)'],
  ];
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-bold">API Reference</h1>
      <p className="mt-2 text-zinc-300">Base: <code className="text-emerald-400">{base}</code></p>
      <div className="mt-10 space-y-6">
        {eps.map(([m, p, d]) => (
          <div key={p} className="rounded-xl border border-zinc-700 bg-zinc-900/50 p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className={m==='GET'?'text-green-400 font-mono text-sm':'text-blue-400 font-mono text-sm'}>{m}</span>
              <code className="text-zinc-200 text-sm">{p}</code>
            </div>
            <p className="text-zinc-300 text-sm">{d}</p>
          </div>
        ))}
      </div>
      <div className="mt-12 rounded-xl border border-zinc-700 bg-zinc-900/50 p-6">
        <h2 className="text-lg font-semibold mb-2">Auth</h2>
        <p className="text-zinc-300 text-sm">Include <code className="text-emerald-400">X-API-Key: your_key</code> header on all endpoints. Get a key via <code className="text-emerald-400">POST /api/v1/auth/register</code></p>
      </div>
    </div>
  );
}
