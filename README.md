# Unweb

**Make the Web AI-Native**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Unweb gives every website an AI-readable endpoint. LLMs and AI agents can understand your web content — structured, fast, and reliable.

## Why?

The web was built for human eyes (HTML, CSS, JS). But in the AI era, 80% of traffic consumers will be AI agents. They shouldn't have to parse your `<div>` soup.

```
Before: 🤖 → HTML soup → slow, expensive token waste
After:  🤖 → unweb.ai/site → clean JSON → instant understanding
```

## Quick Start

### Website Owner
```bash
# 1. Install CLI
pip install unweb

# 2. Register your site
unweb publish https://my-site.com --name "My SaaS"

# 3. Done! Your site is now AI-readable at:
# https://api.unweb.ai/llms/my-site
```

### AI Agent Developer
```python
import httpx

# Extract any URL as structured JSON
r = httpx.get("https://api.unweb.ai/api/v1/extract",
    params={"url": "https://example.com"},
    headers={"Authorization": "Bearer YOUR_API_KEY"})

data = r.json()
print(data["title"])        # "Example Domain"
print(data["content"])      # Clean text, no HTML
print(data["actions"])      # ["Login", "Sign Up", "Search"]
```

## Features

- 🔍 **Universal Extraction** — Any URL → structured JSON
- 📤 **One-Click Publishing** — Register your site in seconds
- 🤖 **Agent-Optimized** — Minimal tokens, maximum information
- 🏷️ **AI-Ready Badge** — Show the world your site speaks AI
- 🔌 **Drop-in CLI/SDK** — Works with any AI agent framework
- 🌐 **Open Source** — AGPL-3.0, free forever

## API

```
POST /api/v1/extract   — Extract any URL
POST /api/v1/publish   — Register a site
GET  /api/v1/sites/:id — Get site info
GET  /api/v1/health    — Health check
```

[Full API Docs →](https://unweb.ai/docs)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python FastAPI |
| Frontend | Next.js + Tailwind |
| CLI | Python Click |
| DB | Supabase |
| AI | DeepSeek (structured extraction) |
| Deploy | Vercel + Railway |

## License

AGPL-3.0 — Free for open source. [Commercial license available](https://unweb.ai/pricing) for proprietary use.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributors must sign the CLA.

---
Built by [@fuhon](https://github.com/fuhon42-cmyk) • [unweb.ai](https://unweb.ai)
