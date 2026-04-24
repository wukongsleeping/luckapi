# 我是如何搭建自己的 AI 代理网关（含完整开源方案）

> 自建 AI 代理网关一年省了上万元，还获得了完整的用户管理和流量控制能力。项目已开源！

---

## 为什么需要 AI 代理网关？

如果你接触过 OpenAI 或大模型服务，大概率遇到过这些问题：

- 不同模型 API Key 分散管理，更换、过期需要逐个更新
- 没有用户权限控制，谁都能用你的模型
- API 调用量失控，不知道谁用了多少
- 模型服务不稳定，需要自动重试
- 想开放给团队用，但没有鉴权和限流

我折腾了很久，发现市面上没有**轻量级的开源方案**能同时解决这些痛点——要么太重（Kong、APISIX），要么太简单（几行 Python 脚本）——所以我开发了 **LuckApi**。

## LuckApi 是什么

LuckApi 是一个开源的 AI 模型代理网关，基于 FastAPI + Vue3，提供：

1. **用户管理** — 创建用户、分配模型接口、角色权限控制
2. **模型绑定** — 为用户绑定多个上游模型（兼容 OpenAI API）
3. **API Key 认证** — 自动生成用户专属 Key，Fernet 加密存储
4. **限流保护** — 基于 Redis 的 API Key 限流，支持分布式
5. **审计日志** — 所有 API 调用记录，Q&A 导出 JSONL 格式
6. **流式转发** — SSE streaming 支持，tenacity 自动重试

## 架构

```
┌─────────────────────────────────────┐
│  Nginx (端口 8080)                   │
│  ├── 静态 SPA 资源                   │
│  ├── /admin/api/ 管理面板           │
│  └── /v1/   代理转发                │
└───────────────────┬─────────────────┘
                    │
┌───────────────────┴─────────────────┐
│  FastAPI (端口 8000)                │
│  ├── CORS → 审计 → 限流 → 安全检查    │
│  ├── 用户/模型 CRUD                 │
│  └── 代理路由                       │
└─────┬───────────────┬───────────────┘
      │               │
  MySQL 8           Redis 7
  持久化            缓存/限流
```

## 部署方案

### Docker 一键部署（推荐）

```bash
git clone https://github.com/luckapi/luckapi.git
cd luckapi
docker-compose up -d
```

访问 `http://localhost:80` 即可使用。

### 原生服务器部署

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
python db_init.py
uvicorn main:app --host 127.0.0.1 --port 8000

# 前端
cd ../frontend
npm install && npm run build
```

[完整安装文档 →](https://github.com/luckapi/luckapi/blob/main/INSTALL.md)

## 使用示例

### 创建用户

在管理面板创建用户，系统自动生成 API Key：

```bash
# 用户使用方式：
curl https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 绑定模型

在用户详情页面绑定任意 OpenAI 兼容接口：

- 模型名称：如 `gpt-4`
- API 地址：如 `http://your-vllm:8000/v1`
- API Key：上游模型的认证 Key

## 性能优化

我们做了多层优化：

1. **Redis 缓存** — 用户模型信息缓存 180 秒
2. **连接池** — MySQL 连接池 30/60
3. **异步 I/O** — 全站 async/await
4. **Nginx 关闭 buffer** — 流式传输不卡顿
5. **批量查询** — 修复 N+1 查询问题

[查看性能优化源码](https://github.com/luckapi/luckapi)

## 路线图

- [x] 用户/模型 CRUD
- [x] API Key 自动生成 + Fernet 加密
- [x] Redis 限流 + 审计日志
- [x] SSE 实时推送
- [x] UniApp 移动端
- [ ] 模型负载均衡
- [ ] Token 用量统计 & 计费
- [ ] 多租户支持

## 总结

如果你需要：

- 自托管 LLM 服务
- 管理多个 API Key
- 开放给团队使用
- 控制 AI 使用成本

LuckApi 可能正是你需要的。项目 **Apache 2.0 开源**，欢迎试用和贡献。

- 📖 文档：https://github.com/luckapi/luckapi
- 💬 问题：https://github.com/luckapi/luckapi/issues

---

**标签**：#AI #大模型 #API代理 #开源 #FastAPI #自托管 #代理网关 #LLM
