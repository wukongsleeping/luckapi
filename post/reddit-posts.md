# Reddit 发帖内容（r/selfhosted + r/opensource）

**发布地址**：
- https://www.reddit.com/r/selfhosted/submit
- https://www.reddit.com/r/opensource/submit

---

## 标题（r/selfhosted）

I built a self-hosted AI proxy gateway to manage my team's LLM API usage

## 正文（r/selfhosted）

I was frustrated having to manage API keys for multiple AI models without any user controls. The commercial solutions are either too heavy or too expensive for my needs.

So I built **LuckApi** — a self-hosted AI model proxy gateway that lets you:

### Features

- **User management** — Create users, assign models, role-based access
- **API Key authentication** — Auto-generated, Fernet encrypted in DB
- **Rate limiting** — Redis-based, per-user limits
- **Audit logs** — Track every API call, export Q&A records
- **OpenAI compatible** — Works with any OpenAI SDK or client
- **Mobile app** — Dark theme UniApp client
- **Streaming** — SSE/Streaming support with automatic retries

### Tech Stack

- **Backend:** FastAPI + SQLAlchemy async + Pydantic v2
- **Frontend:** Vue 3 + Element Plus
- **Database:** MySQL 8.0 + Redis 7
- **Deployment:** Docker Compose or native Linux server

### Quick Start

```bash
git clone https://github.com/wukongsleeping/luckapi.git
cd luckapi
docker-compose up -d
```

That's it. Access the dashboard at `http://localhost:80`.

[Full docs](https://github.com/wukongsleeping/luckapi/blob/main/INSTALL.md)

Open source under Apache 2.0. PRs welcome!

---

## 备选标题（r/opensource）

Open Source: LuckApi — Self-hosted AI Model Proxy Gateway (FastAPI + Vue3 + Docker)

## 正文（r/opensource 可复用上述内容）
