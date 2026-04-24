# AGENTS.md — LuckApi 源码指南

## 项目概述

LuckApi 是一个 API 代理/网关平台，后端为 **FastAPI**（Python 3.10+），前端为 **Vue 3**。用户配置上游模型，通过 OpenAI 兼容接口访问。API Key 以 Fernet 加密存储在数据库中。

**已配置 lint、格式化、类型检查和 CI 流水线。** 遵循代码中现有的约定。没有 Cursor 规则（`.cursor/rules/`、`.cursorrules`）或 Copilot 指令（`.github/copilot-instructions.md`）。目前没有编写任何测试。

---

## 后端（Python/FastAPI）

### 环境

**始终使用 `fast` conda 环境：**
```bash
conda activate fast
```

### 启动 & 命令

```bash
cd backend
cp .env.example .env                  # 配置 MySQL + Redis
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# 数据库初始化 / 单独运行迁移文件
python db_init.py
python migrations/<file>.py

# CI 流水线自动执行 lint 检查（push / PR 到 main 时触发）
# 本地手动运行：
# pip install black flake8 isort mypy safety
# black --check backend/app
# flake8 backend/app --max-line-length=100
# isort --check-only --profile black backend/app
# mypy backend/app
# safety check -r backend/requirements.txt
```

### 技术栈

FastAPI 0.115+ · SQLAlchemy 2.0 (async) · Pydantic v2 · asyncmy (MySQL) · redis (async) · aiohttp · httpx · tenacity (重试) · python-jose · passlib · cryptography · pydantic-settings。依赖：`backend/requirements.txt`。配置：`backend/.env`（pydantic-settings，参见 `.env.example`）。

### CI/CD 流水线

- `.github/workflows/lint.yml` — Python lint：black、flake8、isort、mypy、safety
- `.github/workflows/test.yml` — pytest 测试 + coverage（需要 MySQL 8.0 + Redis 7 service）
- `.github/workflows/docker.yml` — Docker build & push 到 ghcr.io（main / tags）

### 代码规范

- **PEP 8**，4 空格缩进，每行最多约 100 字符。使用 `logger`（不要使用 `print`）。为公共函数编写 docstrings。
- **导入顺序**：标准库 → 第三方库 → 本地 `app.xxx`，组之间用空行分隔。
- **命名**：函数/变量/参数用 `snake_case`；类、常量用 `PascalCase`。
- 每个参数和返回值都使用**类型注解**。不要用 `any` — 改用 `Optional[T]` 或 `Union`。
- 模块内引用使用**相对导入**（`from app.xxx import yyy`）。
- **错误处理**：抛出 `HTTPException(status_code=XXX, detail="...")`。通过 `logger.error()` 记录意外错误。仅在文档说明的情况下使用静默降级（如 Redis 不可用 → 允许请求），必要时使用 `# type: ignore[attr-defined]`。

### SQLAlchemy（2.0 async）

- 使用 `Mapped[T]` + `mapped_column()`（不要使用旧版 `Column()`）。表名：小写复数。
- 异步查询：`await db.execute(select(...))` → `.scalar_one_or_none()`、`.scalars().all()`。
- DB 列名与属性名不匹配时：使用 `Model.__table__.c.db_column_name`。

### Pydantic v2 数据模型

- `app/schemas/*.py` — 每个实体一个文件。后缀：`*Create`（输入）、`*Update`（部分更新）、`*Out`（输出）、`*List`（分页）。
- 使用 `Field()` 约束：`Field(..., min_length=1)`、`Field(..., ge=0)`、`Field(None, pattern=...)`。
- 输出数据模型：`class Config: from_attributes = True`。部分更新通过 `data.model_dump(exclude_unset=True)` 实现。

### API 模式

- `app/api/*.py` — 每个资源一个文件。`Depends(get_db)` 用于异步 session 注入。
- CRUD 路由顺序：list → get → create → update → delete。
- **中间件顺序**（外层 → 内层）：CORS → body_size_limit → audit → rate_limit。

### 数据访问注意事项

- `_get_user_models_from_cache()` 返回**ORM 对象**（使用缓存 ID 重新查询数据库），永远不是字典。
- `UserModel.api_key` 是一个属性 — getter 解密，setter 加密。DB 列名为 `_api_key`。
- `decrypt_api_key()` 在失败时返回明文 — 对未加密/旧数据具有容错性。

### 核心模块

| 路径 | 用途 |
|------|------|
| `app/api/proxy.py` | `/v1/` 代理：流式传输、模型路由、tenacity 重试 |
| `app/api/users.py` | 用户 CRUD：密码哈希（`sha256$salt$hash`）、自动生成 API Key |
| `app/api/models.py` | 用户模型 CRUD（上游模型管理） |
| `app/core/encryption.py` | API Key 的 Fernet 加密 |
| `app/core/security.py` | API Key 生成、token 工具 |
| `app/core/config.py` | pydantic-settings、`get_settings()` 单例 |
| `app/middleware/rate_limit.py` | 基于 Redis 的按 Key 限流 |
| `app/middleware/audit.py` | 审计日志中间件 |
| `app/middleware/body_size_limit.py` | 请求体大小限制（10MB） |
| `app/db/session.py` | Async engine + `get_db()` 依赖 |
| `app/db/redis.py` | Async Redis 连接 |
| `app/schemas/` | Pydantic v2 请求/响应数据模型 |

---

## 前端（Vue 3）

```bash
cd frontend
npm install
npm run dev        # 开发服务器（端口 3000，代理 /admin + /v1 → localhost:8000）
npm run build      # 生产构建 → dist/
npm run preview    # 预览生产构建
```

Vue 3 SFC（`<script setup>`） · Vite · Pinia · Element Plus · Vue Router · Axios。

- 路径别名 `@` → `src/`。
- API 客户端：`src/api/request.js` — axios 实例，baseURL `/admin/api`，30 秒超时，全局错误 `ElMessage.error()`。
- 结构：`src/views/` · `src/components/` · `src/stores/` · `src/router/`。

### 前端代码规范

- 统一使用 `<script setup lang="ts">` 或纯 `<script setup>`（当前代码使用纯写法）。
- 使用 Element Plus 组件（`el-table`、`el-form`、`el-dialog` 等）构建 UI。
- Axios 响应被拦截器自动解包 — `response.data` 直接返回。

---

## Docker

```bash
docker-compose up -d
```

| 服务         | URL                        |
|--------------|----------------------------|
| 后端 API     | `localhost:8000`（文档 `/docs`、`/redoc`） |
| 前端生产     | `localhost:80`             |
| 前端开发     | `localhost:3000`           |

服务：MySQL 8.0（端口 3306）、Redis 7（端口 6379）。MySQL 数据和 Redis 数据使用命名卷持久化。

---

## 移动端（UniApp）

**使用 HBuilderX 原生模板**（非 Vite 项目）。在 `uniapp/` 目录下直接打开即可。

```bash
# HBuilderX 操作
# 1. 文件 → 导入 → 从本地目录导入
# 2. 选择 uniapp/ 目录
# 3. 运行 → 运行到手机或模拟器 → 选择安卓设备
```

### 技术栈 & 特性

Vue 2 Options API · Pinia · `uni.request` / `uni.showToast` / `uni.navigateTo` · 深色主题（与 Web 版一致）。

### 安卓打包

**推荐方式**：使用 HBuilderX IDE 云打包（最简单）：
1. 打开 uniapp 目录
2. 菜单 → 发行 → 云打包 → 选择配置
3. 下载 APK 文件或安装到设备

**打包配置**：在 `manifest.json` 中配置安卓图标、启动页等。

### 目录结构

```
uniapp/
├── App.vue                    # 根组件（深色主题样式）
├── manifest.json              # UniApp 配置（Android 权限、应用信息）
├── pages.json                 # 页面路由 + 底部 TabBar（用户|模型|分组）
├── main.js                    # 应用入口 → Vue2 初始化 + Pinia
├── package.json               # 依赖声明（pinia）
├── api/
│   ├── request.js             # 请求封装（使用 uni.request，自动携带 Auth header，401 跳转）
│   ├── config.js              # baseURL: /admin/api
│   ├── auth.js                # login、logout、getMe
│   ├── groups.js              # 分组 CRUD + 添加/移除成员
│   └── admin_models.js        # 全局模型 CRUD
├── pages/
│   ├── login/login.vue        # 登录页（无 TabBar），已登录自动跳转
│   ├── users/users.vue        # 用户列表 + 浮动添加按钮，跳转至 userDetail
│   ├── users/userDetail.vue   # 用户编辑 + IP 白名单（picker 选择角色/状态）
│   ├── models/models.vue      # 模型列表 + 浮动添加按钮，跳转至 modelDetail
│   ├── models/modelDetail.vue # 模型创建/编辑表单
│   ├── groups/groups.vue      # 分组列表 + 浮动添加按钮
│   └── groupDetail/groupDetail.vue  # 分组成员管理 + 模型配置
├── store/
│   └── auth.js                # Pinia 认证状态（token、user、login/logout/fetchUser）
└── static/                    # TabBar 图标
```

### 与 Web 前端的区别

- 导航使用 `uni.navigateTo` / `uni.switchTab` / `uni.reLaunch`（无 Vue Router）。登录页无底部 TabBar。
- 认证状态通过 `uni.setStorageSync` / `uni.getStorageSync` 持久化（非 localStorage）。
- HTTP 请求使用 `uni.request` 封装而非 axios。
- UI 使用基础 `view`/`text`/`input`/`button` 组件（非 Element Plus）— 完全自定义深色主题样式。
- IP 白名单输入支持 → 添加（无内联编辑标签）。
- 角色和状态使用 picker 组件选择（非下拉框文本输入）。

---

## 错误处理参考

### 后端状态码
| 状态码 | 场景 |
|--------|------|
| 400  | 用户名已存在、验证失败 |
| 401  | 认证缺失/无效的 API Key |
| 403  | 账户未绑定模型、被封禁用户 |
| 404  | 资源未找到 |
| 413  | 请求体过大（body_size_limit 中间件） |
| 429  | 触发限流 |
| 502  | 上游代理错误 |
| 504  | 上游服务器超时 |

### 前端错误处理
- `src/api/request.js` 响应拦截器：出错时提取 `error.response.data.detail` 并显示 `ElMessage.error()`。始终返回 `Promise.reject(error)` 以便调用方仍可 `.catch()`。
