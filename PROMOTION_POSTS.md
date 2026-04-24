# V2EX / Show HN / Reddit 发帖模板

## V2EX 帖子

**标题**：开源了一个自托管 AI 代理管理网关 LuckApi

**内容**：
> 大家好！
> 
> 因为需要管理多个 AI 模型 API Key，并且需要给团队分配使用权限，但市面上的开源方案要么太重（Kong、APISIX），要么太简单（几行脚本）。
> 
> 于是自己开发了一个轻量级的 AI 代理网关：
> - FastAPI + Vue3 前后端分离
> - 用户管理 + 模型绑定 + API Key 认证
> - Redis 限流 + 审计日志
> - 支持 Docker 一键部署
> - 开源协议 Apache 2.0
> - 含移动端（UniApp 深色主题）
> 
> 目前已在生产环境稳定运行，欢迎 Star 和提 Issue：
> https://github.com/luckapi/luckapi
> 
> 项目文档很详细，Docker 一行命令就能部署使用。

## Show HN 帖子

**标题**：Show HN: LuckApi — Self-hosted AI Proxy Gateway

**内容**：
> I built LuckApi to manage multiple AI model API keys and delegate access to my team with rate limiting and audit logs.
> 
> - FastAPI backend + Vue3 admin panel
> - Compatible with OpenAI API specification
> - Docker compose deployment
> - Redis-based rate limiting
> - User management & model routing
> 
> Open source under Apache 2.0. Would love feedback!
> https://github.com/luckapi/luckapi

## Reddit r/selfhosted 帖子

**标题**：I built a self-hosted AI proxy gateway to manage my team's LLM API usage

**内容**：
> I was frustrated having to manage API keys for multiple AI models without any user controls or usage tracking. The commercial solutions are either too heavy or too expensive for my needs.
> 
> So I built LuckApi:
> - User management with role-based access
> - Model routing (OpenAI compatible API)
> - API key authentication & rate limiting
> - Full audit logs with Q&A export
> - Docker one-command deployment
> 
> It's designed to be simple, self-hosted, and open source (Apache 2.0).
> https://github.com/luckapi/luckapi

## 知乎 / 掘金帖子

**标题**：自建 AI 代理网关：管理多模型 API,省了上万元

**内容**：（同 SEO_BLOG_POST.md）
