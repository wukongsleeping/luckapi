# V2EX 发帖内容

**发布地址**：https://www.v2ex.com/new/item

---

## 标题

开源了一个自托管 AI 代理管理网关 LuckApi

---

## 正文

大家好！

因为需要管理多个 AI 模型 API Key，并且需要给团队分配使用权限，但市面上的开源方案要么太重（Kong、APISIX），要么太简单（几行脚本）。

于是自己开发了一个轻量级的 AI 代理网关：**LuckApi**

### 核心功能

- **用户管理** — 创建 / 编辑 / 删除用户，余额与用量统计
- **模型绑定** — 为用户绑定多个上游模型（兼容 OpenAI API）
- **API Key 认证** — 自动生成用户专属 Key，Fernet 加密存储
- **限流保护** — 基于 Redis 的 API Key 限流，支持分布式
- **审计日志** — 所有 API 调用记录，Q&A 导出 JSONL 格式
- **流式转发** — SSE streaming 支持，tenacity 自动重试
- **移动端** — UniApp 客户端，深色主题，TabBar
- **SSE 实时推送** — 代理请求状态实时推送

### 技术栈

**后端**：FastAPI 0.115+ · SQLAlchemy 2.0 (async) · Pydantic v2 · asyncmy · Redis · aiohttp · tenacity  
**前端**：Vue 3 SFC · Vite · Pinia · Element Plus  
**移动端**：UniApp · Pinia · 深色主题  
**部署**：Docker Compose / Nginx / systemd

### 架构

```
Nginx (8080)
 ├── SPA 静态资源
 ├── /admin/api   管理面板
 └── /v1/         代理转发
   
FastAPI (8000)
 ├── 中间件: CORS → 限流 → 审计 → 安全检查
 ├── 用户/模型 CRUD
 └── 代理路由

MySQL 8.0    Redis 7
持久化      缓存/限流
```

### 快速开始

```bash
git clone https://github.com/wukongsleeping/luckapi.git
cd luckapi
docker-compose up -d
```

访问 `http://localhost:80` 即可使用。

[完整安装文档 →](https://github.com/wukongsleeping/luckapi/blob/main/INSTALL.md)

### 项目地址

GitHub: https://github.com/wukongsleeping/luckapi  
开源协议: Apache 2.0

目前已在生产环境稳定运行，欢迎 Star、提 Issue 和 PR！

---

## 标签建议

开发工具, 开源项目, AI, API 网关, FastAPI, Docker, 自托管
