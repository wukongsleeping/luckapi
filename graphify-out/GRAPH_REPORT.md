# Graph Report - .  (2026-04-24)

## Corpus Check
- Corpus is ~27,019 words - fits in a single context window. You may not need a graph.

## Summary
- 424 nodes · 625 edges · 20 communities detected
- Extraction: 69% EXTRACTED · 31% INFERRED · 0% AMBIGUOUS · INFERRED: 191 edges (avg confidence: 0.74)
- Token cost: 5,000 input · 3,000 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Model Creation Helpers|Model Creation Helpers]]
- [[_COMMUNITY_Global Model Schema|Global Model Schema]]
- [[_COMMUNITY_Model API Module|Model API Module]]
- [[_COMMUNITY_Backend Services|Backend Services]]
- [[_COMMUNITY_Admin Auth Utilities|Admin Auth Utilities]]
- [[_COMMUNITY_DB Migration Utilities|DB Migration Utilities]]
- [[_COMMUNITY_QA Records UI|QA Records UI]]
- [[_COMMUNITY_Proxy Engine|Proxy Engine]]
- [[_COMMUNITY_SSE Notification|SSE Notification]]
- [[_COMMUNITY_Token Auth Helpers|Token Auth Helpers]]
- [[_COMMUNITY_Audit Logging|Audit Logging]]
- [[_COMMUNITY_Group Member Management|Group Member Management]]
- [[_COMMUNITY_Request Helpers|Request Helpers]]
- [[_COMMUNITY_User Detail UI|User Detail UI]]
- [[_COMMUNITY_API Key Migration|API Key Migration]]
- [[_COMMUNITY_Model Create API|Model Create API]]
- [[_COMMUNITY_User Downgrade|User Downgrade]]
- [[_COMMUNITY_JWT Library|JWT Library]]
- [[_COMMUNITY_Migration Tooling|Migration Tooling]]
- [[_COMMUNITY_UI Assets|UI Assets]]

## God Nodes (most connected - your core abstractions)
1. `get()` - 36 edges
2. `Backend (FastAPI)` - 23 edges
3. `User` - 19 edges
4. `post()` - 15 edges
5. `ApiKey` - 12 edges
6. `UserModel` - 11 edges
7. `QaRecord` - 10 edges
8. `Base` - 10 edges
9. `LuckApi` - 10 edges
10. `get_settings()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `getUsers()` --calls--> `get()`  [INFERRED]
  /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/frontend/src/api/user.js → /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/request.js
- `getUser()` --calls--> `get()`  [INFERRED]
  /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/frontend/src/api/user.js → /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/request.js
- `getMe()` --calls--> `get()`  [INFERRED]
  /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/auth.js → /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/request.js
- `fetchApiKey()` --calls--> `get()`  [INFERRED]
  /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/users.js → /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/request.js
- `getModels()` --calls--> `get()`  [INFERRED]
  /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/admin_models.js → /Users/yanyy/Desktop/code/Python/LuckApi/LuckApi3.0/uniapp/api/request.js

## Hyperedges (group relationships)
- **Backend Tech Stack** — node_tech_fastapi, node_tech_sqlalchemy, node_tech_pydantic, node_tech_mysql, node_tech_redis, node_tech_uvicorn, node_tech_asyncmy, node_tech_cryptography [EXTRACTED 0.90]
- **Frontend Tech Stack** — node_tech_frontend_vue, node_tech_element_plus, node_tech_vue_router, node_tech_pinia, node_tech_vite, node_tech_axios [EXTRACTED 0.90]

## Communities

### Community 0 - "Model Creation Helpers"
Cohesion: 0.05
Nodes (48): createGlobalModel(), getGlobalModel(), getGlobalModels(), updateGlobalModel(), handleSave(), assignGroupModel(), assignGroupUser(), assignUserToGroup() (+40 more)

### Community 1 - "Global Model Schema"
Cohesion: 0.06
Nodes (32): GlobalModelCreate, GlobalModelList, GlobalModelOut, GlobalModelUpdate, create_global_model(), list_global_models(), BaseModel, GroupAssignUser (+24 more)

### Community 2 - "Model API Module"
Cohesion: 0.08
Nodes (32): Base, init_db(), DeclarativeBase, add_user_model(), ApiKey, GlobalModel, Group, GroupUser (+24 more)

### Community 3 - "Backend Services"
Cohesion: 0.05
Nodes (44): Backend (FastAPI), Frontend (Vue 3 SPA), Mobile (UniApp), Docker Deploy, Native Server Deploy, Nginx Reverse Proxy, Group API (groups.py), Model API (models.py) (+36 more)

### Community 4 - "Admin Auth Utilities"
Cohesion: 0.11
Nodes (20): admin_required(), admin_test_endpoint(), _check_login_rate_limit(), _create_token(), _decode_token(), get_current_user(), getMe(), login() (+12 more)

### Community 5 - "DB Migration Utilities"
Cohesion: 0.1
Nodes (14): add_expires_at_column(), Add the expires_at column to api_keys table., create_group_tables(), Create the groups and group_users tables., add_allowed_ips_column(), Add allowed_ips column to users table., create_qa_records_table(), Create qa_records table for saving Q&A conversation data. (+6 more)

### Community 6 - "QA Records UI"
Cohesion: 0.12
Nodes (8): copyText(), deleteQaRecord(), confirmDelete(), copyText(), handleSizeChange(), loadRecords(), resetFilter(), catch()

### Community 7 - "Proxy Engine"
Cohesion: 0.26
Nodes (17): _check_ip_whitelist(), _close_aiohttp(), _extract_stream_tokens(), _extract_tokens(), _forward_chat(), _get_client_ip(), get_user_by_api_key(), _get_user_models_from_cache() (+9 more)

### Community 8 - "SSE Notification"
Cohesion: 0.12
Nodes (11): _cleanup(), 轻量级 SSE 消息推送桥接器。  在代理请求完成（写入 QaRecord 后）触发 push()，所有连接的客户端实时收到事件。, 创建一个订阅队列，yield 供生成器使用。, 注册 push 事件回调（用于存储/审计）。, SSEBridge, events_stats(), SSE (Server-Sent Events) 通知端点。  前端建立长连接后，服务端实时推送代理请求结果。, SSE 推送流。连接到此端点即可持续接收事件。 (+3 more)

### Community 9 - "Token Auth Helpers"
Cohesion: 0.17
Nodes (10): decodeTokenPayload(), isTokenExpired(), utcnow(), _addRecentEvent(), _clearHeart(), _connect(), connectNotify(), disconnectNotify() (+2 more)

### Community 10 - "Audit Logging"
Cohesion: 0.14
Nodes (7): AuditMiddleware, 请求审计日志，记录所有 API 调用用于监控和计费。, BaseHTTPMiddleware, BodySizeLimitMiddleware, _get_api_key(), RateLimitMiddleware, 基于 API Key 的 Redis 限流，支持分布式部署。

### Community 11 - "Group Member Management"
Cohesion: 0.19
Nodes (5): addMember(), buildUserOptions(), fetchGroup(), fetchUserList(), onLoad()

### Community 12 - "Request Helpers"
Cohesion: 0.19
Nodes (7): baseURL(), getBaseUrl(), setBaseUrl(), confirmServer(), handleLogin(), isHttps(), openServerDialog()

### Community 13 - "User Detail UI"
Cohesion: 0.19
Nodes (5): fetchApiKey(), fetchUserDetail(), onLoad(), parseIpList(), getUser()

### Community 14 - "API Key Migration"
Cohesion: 0.27
Nodes (7): 遍历所有 UserModel 记录，重新用当前 key 加密 api_key。      解决：之前使用随机 Fernet key 加密，key 变更导致 de, reencrypt_all_keys(), decrypt_api_key(), encrypt_api_key(), 解密 API Key。      如果解密失败（旧数据/非 Fernet 格式），返回原文——兼容未加密的历史数据。, api_key(), model_api_key()

### Community 15 - "Model Create API"
Cohesion: 0.28
Nodes (7): createModel(), deleteModel(), getModel(), getModels(), updateModel(), fetchModel(), handleSave()

### Community 16 - "User Downgrade"
Cohesion: 0.5
Nodes (1): 修改 qa_records 表的 request_body 和 response_body 字段为 LongText  原因：Text 类型最大 64KB，op

### Community 37 - "JWT Library"
Cohesion: 1.0
Nodes (1): python-jose

### Community 38 - "Migration Tooling"
Cohesion: 1.0
Nodes (1): Alembic (pending migration)

### Community 39 - "UI Assets"
Cohesion: 1.0
Nodes (1): App Tabbar Icons

## Knowledge Gaps
- **56 isolated node(s):** `Make api_key column nullable in global_models table.`, `Create the groups and group_users tables.`, `修改 qa_records 表的 request_body 和 response_body 字段为 LongText  原因：Text 类型最大 64KB，op`, `Create qa_records table for saving Q&A conversation data.`, `Add the expires_at column to api_keys table.` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `User Downgrade`** (4 nodes): `downgrade()`, `修改 qa_records 表的 request_body 和 response_body 字段为 LongText  原因：Text 类型最大 64KB，op`, `upgrade()`, `006_upgrade_qa_records_to_longtext.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `JWT Library`** (1 nodes): `python-jose`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Migration Tooling`** (1 nodes): `Alembic (pending migration)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `UI Assets`** (1 nodes): `App Tabbar Icons`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get()` connect `Proxy Engine` to `Model Creation Helpers`, `Global Model Schema`, `Admin Auth Utilities`, `SSE Notification`, `Audit Logging`, `User Detail UI`, `Model Create API`?**
  _High betweenness centrality (0.328) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `DB Migration Utilities` to `Model API Module`, `Proxy Engine`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `assign_group_model()` connect `Global Model Schema` to `Proxy Engine`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `get()` (e.g. with `getGroups()` and `getGroup()`) actually correct?**
  _`get()` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Backend (FastAPI)` (e.g. with `Frontend (Vue 3 SPA)` and `Mobile (UniApp)`) actually correct?**
  _`Backend (FastAPI)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `User` (e.g. with `Base` and `LoginRequest`) actually correct?**
  _`User` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `post()` (e.g. with `createGroup()` and `assignGroupUser()`) actually correct?**
  _`post()` has 13 INFERRED edges - model-reasoned connections that need verification._