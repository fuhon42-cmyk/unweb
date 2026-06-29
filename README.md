# Unweb — Is your website ready for AI?

**Free AI-readability score for any website. No signup.**

[![AI Readability](https://unweb-production-6f69.up.railway.app/api/v1/badge?url=github.com)](https://unweb-production-6f69.up.railway.app)

> 80% of web traffic will be AI agents by 2028. Is your site ready?

## 🚀 Try it now

**[→ Get your website's AI-readability score](https://unweb-production-6f69.up.railway.app)**

Enter any URL, get an instant 8-point AI-readability report with actionable fixes.

## 📊 Embed the badge

Show your visitors your site is AI-friendly. Copy this into your HTML:

```html
<a href="https://unweb-production-6f69.up.railway.app">
  <img src="https://unweb-production-6f69.up.railway.app/api/v1/badge?url=YOURSITE.COM" alt="AI Readability Score">
</a>
```

## 🔧 For developers

Unweb also provides structured extraction for AI agents:

```python
import httpx
r = httpx.post("https://unweb-production-6f69.up.railway.app/api/v1/extract",
    json={"url": "https://news.ycombinator.com"})
data = r.json()
print(data["title"], data["content"])
```

## 📡 API

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/score` | Score any website (8 dimensions) |
| `GET /api/v1/badge?url=` | SVG badge for your site |
| `POST /api/v1/extract` | Structured JSON extraction |
| `GET /api/v1/health` | Health check |

## 🛠 Tech

Python FastAPI · Next.js · DeepSeek · Railway · AGPL-3.0

---

Built by [@fuhon42-cmyk](https://github.com/fuhon42-cmyk) · [Try Unweb →](https://unweb-production-6f69.up.railway.app)
Related
    - agent-taobao — Taobao affiliate SDK for AI agents
