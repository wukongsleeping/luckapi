---
name: Bug Report
about: 报告 Bug，帮助改进 LuckApi
title: '[Bug]: '
labels: 'bug'
assignees: ''
---

## 环境信息

- **操作系统**：（如：macOS 14.2 / Ubuntu 22.04 / Windows 11）
- **Python 版本**：（如：3.12.1）
- **Docker 版本**：（如适用，运行 `docker --version`）
- **部署方式**：Docker Compose / 原生服务器 / 其他
- **LuckApi 版本**：（如：1.0.0 或 git commit hash）

## 问题描述

简要描述你遇到的问题。

## 复现步骤

1. 使用 `docker-compose up -d` 启动服务
2. 访问 http://localhost:80
3. 在用户管理页面点击「添加用户」
4. 填写用户名 `test`，密码 `123456`
5. 点击保存

## 预期行为

描述你期望看到的结果。

## 实际行为

描述你实际看到的结果。

## 日志 / 截图

**后端日志**：

```
（粘贴 backend 日志，运行 `docker logs luckapi-backend`）
```

**截图**：

（可拖拽上传截图或粘贴图片链接）

## 补充信息

在此添加任何额外的上下文信息，如：是否修改过 `.env` 配置、是否使用自定义 Nginx 配置等。
