# Unweb — Make the Web AI-Native

## 一句话
任何 URL → 结构化 JSON，让 AI Agent 像读 API 一样读网页。

## 架构

```
┌─────────────────────────────────────────────┐
│                  用户层                       │
│  网站主 (发布)         Agent 开发者 (消费)       │
│  注册 → 管理 → 分析    API Key → 提取 → 集成    │
├─────────────────────────────────────────────┤
│                 API 网关 (FastAPI)            │
│  /api/v1/extract    /api/v1/publish          │
│  /api/v1/sites      /api/v1/stats            │
├─────────────────────────────────────────────┤
│                核心引擎                       │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Crawler  │ │Extractor │ │ Schema       │ │
│  │requests  │ │DeepSeek  │ │ Validator    │ │
│  │+ BS4     │ │+ Pydantic│ │              │ │
│  └──────────┘ └──────────┘ └─────────────┘ │
├─────────────────────────────────────────────┤
│                数据层 (Supabase)             │
│  sites / api_keys / extraction_logs          │
└─────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 |
|-----|------|
| 后端 | Python FastAPI + Pydantic |
| 前端 | Next.js (App Router) + Tailwind |
| CLI | Python Click (npm publish 同步) |
| 数据库 | Supabase (PostgreSQL) |
| AI | DeepSeek API (结构化提取) |
| 部署 | Vercel (前端) + Railway (后端) |
| 许可证 | AGPL-3.0 |

## 项目结构

```
unweb/
├── backend/
│   ├── main.py           # FastAPI app entry
│   ├── crawler.py         # URL fetching + HTML parsing
│   ├── extractor.py       # LLM-powered content extraction
│   ├── schemas.py         # Pydantic models
│   ├── auth.py            # API key auth
│   ├── rate_limit.py      # Rate limiting
│   └── requirements.txt
├── web/
│   ├── app/               # Next.js app router
│   ├── components/        # React components
│   └── lib/               # API client
├── cli/
│   ├── unweb.py           # Click CLI
│   └── setup.py
├── docs/
│   └── README.md
└── LICENSE
```

## API 设计

### POST /api/v1/extract
```
输入: { "url": "https://example.com" }
输出: {
  "title": "...",
  "description": "...",
  "content": "纯文本内容",
  "structured_data": { 自定义 schema },
  "actions": ["可执行的操作"],
  "metadata": { "site_name": "...", "language": "..." }
}
```

### POST /api/v1/publish
```
输入: { "url": "https://my-site.com", "content": "自定义内容" }
输出: { "llms_url": "https://api.unweb.ai/llms/my-site" }
```

## 开发阶段

Phase 1 (Day 1-3): 核心引擎 + API
Phase 2 (Day 4-5): Web 仪表盘
Phase 3 (Day 6): CLI SDK
Phase 4 (Day 7): 部署 + 文档

## 检查清单

- [ ] 爬虫反反爬策略 (User-Agent 轮换, robots.txt 尊重)
- [ ] LLM 输出验证 (Pydantic schema 强校验)
- [ ] API 限流 (100 req/min 免费用户)
- [ ] API Key 安全 (Supabase RLS)
- [ ] CORS 配置 (仅允许 web 域名)
- [ ] 错误处理 (优雅降级，HTML → 纯文本 fallback)
- [ ] 缓存策略 (相同 URL 5 分钟内不重复请求)
- [ ] 隐私合规 (不存储提取的内容)
- [ ] 中文支持 (中文网页优先测试)
