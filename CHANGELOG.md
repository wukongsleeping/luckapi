# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-01-15

### Added
- 用户管理 — 创建 / 编辑 / 删除用户，余额与用量统计（`api/users.py`）
- 模型管理 — 用户模型 CRUD，上游模型配置（`api/models.py`）
- API Key 自动生成与 Fernet 加密存储（`core/encryption.py`）
- Redis 基于 API Key 的限流中间件（`middleware/rate_limit.py`）
- 审计日志中间件（`middleware/audit.py`）
- SSE 实时推送模块（`notification.py`）
- Q&A 记录导出（JSONL 格式）
- UniApp 移动端客户端（深色主题，TabBar）
- JWT 认证中间件（`core/security.py`）
- 用户级 IP 白名单限制
- Docker Compose 一键部署（MySQL 8.0 + Redis 7）
- Nginx 生产环境配置（`nginx/`）
- 系统配置页面（API 端点管理）

### Fixed
- Redis 连接超时问题（连接池配置）
- N+1 查询问题（ORM eager loading）
- 审计日志重复/遗漏问题（中间件链修复）
- SSE 广播内存泄漏（连接清理）
- 数据库连接池大小配置（max_overflow 调整）

### Changed
- 用户密码存储由 plain → SHA-256 + salt
- 代理转发由 requests → aiohttp（全异步）
- 限流算法由简单计数器 → sliding window

### Security
- API Key 采用 Fernet 对称加密存储
- 密码采用 SHA-256 + salt 哈希存储
- CORS 白名单机制
- 请求体大小限制（10MB）

---

## [0.x.x] - Pre-release

### 0.1.0 (2024-12-01)
- 初始版本：用户 / 模型 CRUD
- 基础代理转发功能
