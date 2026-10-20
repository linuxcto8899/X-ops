# X-ops 运维平台

一个轻量运维平台，基于 **Django + Vue 3 + Ant Design Vue** 构建，开箱即用、支持中英双语。

> **版权** © 2025-2026 X-ops · t.me/@linuxcto998 · QQ:5609648
>
> 本项目由个人独立开发维护，仅供学习交流与自用部署。

---

## ✨ 功能特性

| 模块 | 说明 |
|------|------|
| 🖥️ 主机管理 | 分组、云服务商（含自建）、地域、到期提醒、凭据加密、SSH 验证、Excel 批量导入、搜索 |
| 📊 主机监控 | 展示所有主机 CPU/内存/磁盘/网络/负载/进程，实时 + 历史曲线，每分钟自动采集 |
| ⚡ 批量执行 | 多主机命令执行，**带WebSSH 交互式回显窗口**，可继续输入命令 |
| 🖥️ 在线终端 | 浏览器 WebSocket 实时 SSH 终端 |
| 📁 文件管理 | 目录浏览、上传/下载/删除、多主机文件分发 |
| 🚀 应用发布 | 常规/自定义、审批、灰度、回滚、Webhook 自动发布 |
| 🔀 流水线 | 节点编排（构建/执行/传输/上传/通知）、条件分支 |
| ⏰ 任务计划 | 一次性 / Cron / 固定间隔 / 报警触发 |
| ⚙️ 配置中心 | KV / 文本 / JSON、分环境、开放 API |
| 📈 监控/报警中心 | 站点/端口/Ping/进程/脚本检测，**发信配置**（SMTP/钉钉/企业微信/飞书/Server酱）+ 测试发送，报警规则绑定通知组 |
| 🔐 凭据管理 | 集中密码/私钥（Fernet 加密） |
| 👥 权限控制 | 用户/角色 RBAC，中英双语 |

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/<你的用户名>/x-ops.git
cd x-ops

# 2. 构建前端
cd frontend
npm install
npm run build
cp -r dist ../deploy/frontend-dist
cd ..

# 3. 配置环境变量
cd deploy
cp ../.env.example .env
vim .env   # 修改 DJANGO_SECRET_KEY / POSTGRES_PASSWORD / XOPS_PUBLIC_URL

# 4. 启动
docker compose up -d --build
```

访问 `http://<服务器IP>`，默认管理员见安装文档。

### 方式二：手动部署（systemd + Nginx）

详见 [安装文档 INSTALL.md](docs/INSTALL.md)。

## 📁 项目结构

```
x-ops/
├── backend/               # Django 后端
│   ├── ops_platform/      # 项目配置（settings/asgi/celery/urls）
│   ├── accounts/          # 用户/角色/权限
│   ├── hosts/             # 主机/分组/凭据/SSH
│   ├── execution/         # 批量执行（流式回显）
│   ├── terminal/          # 在线终端（WebSocket）
│   ├── files/             # 文件管理/分发
│   ├── deploy/            # 应用发布
│   ├── pipeline/          # 流水线
│   ├── scheduler/         # 任务计划
│   ├── monitor/           # 主机监控/报警（发信配置）
│   └── config_center/     # 配置中心
├── frontend/              # Vue 3 前端
│   └── src/views/         # 页面组件
└── deploy/                # Docker/Nginx 部署配置
```

## 🛠️ 开发

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  # 或 daphne ops_platform.asgi:application（WebSocket）

# 前端
cd frontend
npm install
npm run dev
```

详见 [开发文档 DEVELOP.md](docs/DEVELOP.md)。

## 🐳 Docker 镜像

```bash
# 构建镜像
cd x-ops
docker build -f deploy/Dockerfile -t <docker.io用户名>/x-ops:latest .

# 推送至 Docker Hub
docker login
docker push <docker.io用户名>/x-ops:latest
```

编排文件见 `deploy/docker-compose.yml`。

## 📄 License

Copyright © 2025-2026 X-ops · t.me/@linuxcto998 · QQ:5609648

本项目为个人项目，保留所有权利。禁止未经授权用于商业用途。
