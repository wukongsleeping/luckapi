# Show HN 发帖内容

**发布地址**：https://news.ycombinator.com/submit

---

## 标题

Show HN: LuckApi — Self-hosted AI Proxy Gateway

---

## 正文

I built LuckApi to manage multiple AI model API keys and delegate access to my team with rate limiting and audit logs.

The problem was simple: I needed to give my team access to OpenAI-compatible APIs, but managing API keys manually was getting out of hand. Commercial solutions like Kong or APISIX were too heavy, and simple proxy scripts lacked user controls entirely.

**What LuckApi does:**

- **User management** — Create/edit/delete users with API key auto-generation
- **Model routing** — Bind multiple upstream models per user (OpenAI compatible API)
- **Rate limiting** — Redix-based, supports distributed deployment
- **Audit logs** — All API calls recorded, Q&A exportable as JSONL
- **SSE streaming** — Real-time push on request status
- **Mobile app** — UniApp client with dark theme (similar to the web version)
- **Easy deployment** — Docker Compose one-command or native server

**Tech stack:** FastAPI + SQLAlchemy async + Pydantic v2 backend, Vue 3 + Element Plus frontend, Docker Compose / Nginx / systemd deployment.

Open source under Apache 2.0. Written in Python 3.10+.

GitHub: https://github.com/wukongsleeping/luckapi

Would love feedback!
