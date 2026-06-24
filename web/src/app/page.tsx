export default function Home() {
  return (
    <div className="flex flex-col min-h-full bg-black text-zinc-100">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-6 pt-32 pb-24 text-center">
        <h1 className="max-w-3xl text-5xl font-bold tracking-tight sm:text-6xl">
          Make Your Website{" "}
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            AI-Ready
          </span>{" "}
          in 5 Minutes
        </h1>
        <p className="mt-6 max-w-xl text-lg leading-relaxed text-zinc-300">
          Unweb strips away complexity so LLMs, crawlers, and AI agents can read
          your site effortlessly. No config. No overhead. Just results.
        </p>
        <a
          href="/unweb/register"
          className="mt-10 inline-flex h-12 items-center gap-2 rounded-full bg-emerald-500 px-8 text-base font-semibold text-black transition-colors hover:bg-emerald-400"
        >
          Get Started
          <span className="text-lg">&rarr;</span>
        </a>
      </section>

      {/* How it works */}
      <section className="mx-auto w-full max-w-5xl px-6 py-24">
        <h2 className="text-center text-3xl font-bold">How It Works</h2>
        <div className="mt-16 grid gap-8 sm:grid-cols-3">
          {[
            {
              step: "01",
              title: "Add Unweb",
              desc: "Install the package with a single command — no complex setup or framework changes.",
            },
            {
              step: "02",
              title: "Configure Your Rules",
              desc: "Define which pages and elements to simplify for AI consumption using plain config.",
            },
            {
              step: "03",
              title: "Go Live",
              desc: "Deploy and watch your site become instantly understandable by every AI agent and crawler.",
            },
          ].map((item) => (
            <div
              key={item.step}
              className="rounded-xl border border-zinc-700 bg-zinc-900/50 p-8"
            >
              <span className="text-sm font-semibold text-emerald-400">
                {item.step}
              </span>
              <h3 className="mt-3 text-lg font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-300">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Developer */}
      <section className="mx-auto w-full max-w-3xl px-6 py-24">
        <h2 className="text-center text-3xl font-bold">For Developers</h2>
        <p className="mx-auto mt-4 max-w-lg text-center text-zinc-300">
          One command, zero friction. Integrate Unweb into your existing
          pipeline in seconds.
        </p>
        <div className="mt-10 overflow-hidden rounded-xl border border-zinc-700 bg-zinc-950">
          <div className="flex items-center gap-1.5 border-b border-zinc-700 px-4 py-3">
            <span className="h-3 w-3 rounded-full bg-red-500" />
            <span className="h-3 w-3 rounded-full bg-yellow-500" />
            <span className="h-3 w-3 rounded-full bg-green-500" />
          </div>
          <pre className="overflow-x-auto px-6 py-5 text-sm text-zinc-300">
            <code>{`npm install @unweb/cli

npx unweb init
# → Creates unweb.config.ts

npx unweb build
# → Outputs AI-optimized artifacts

npx unweb deploy`}</code>
          </pre>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-700 px-6 py-8 text-center text-sm text-zinc-400">
        <p>&copy; {new Date().getFullYear()} Unweb. AGPL-3.0 License.</p>
      </footer>
    </div>
  );
}
