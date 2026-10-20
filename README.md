# 🚀 X-ops 运维平台

一个轻量、开箱即用的运维管理平台，基于 **Django + Vue 3 + Ant Design Vue** 构建，支持中英双语。

> **版权** © 2025-2026 X-ops · t.me/@linuxcto998 · QQ:5609648
>
> 个人独立开发，仅供学习交流与自用部署。

---

## ✨ 功能特性

| 模块 | 说明 |
|------|------|
| 🖥️ **主机管理** | 分组、云服务商（含自建）、地域国旗、到期提醒、凭据加密、SSH 验证、Excel 批量导入、搜索 |
| 📊 **主机监控** | 卡片式展示 CPU/内存/磁盘/网络/负载/进程，实时 + 历史曲线，每分钟自动采集 |
| 🐳 **Docker 管理** | 远程主机容器管理（启动/停止/重启/暂停/删除/日志）、镜像列表与删除、网络查看、引擎概览 |
| ⚡ **批量执行** | 多主机命令执行，每台主机 WebSSH 交互式回显窗口 |
| 🖥️ **在线终端** | 浏览器 WebSocket 实时 SSH 终端 |
| 📁 **文件管理** | 目录浏览（面包屑导航）、上传/下载/删除、多主机分发 |
| 🚀 **应用发布** | 常规/自定义、审批、灰度、回滚、Webhook 自动发布 |
| 🔀 **流水线** | 节点编排（构建/执行/传输/上传/通知）、运行记录 |
| ⏰ **任务计划** | 一次性 / Cron / 固定间隔 / 报警触发 |
| ⚙️ **配置中心** | KV/文本/JSON、分环境、开放 API |
| 📈 **监控/报警中心** | 站点/端口/Ping/进程/脚本检测、发信配置（SMTP/钉钉/企微/飞书/Server酱）+ 测试发送 |
| 🔐 **凭据管理** | 集中密码/私钥（Fernet 加密） |
| 👥 **权限控制** | 用户/角色 RBAC，所有弹窗页面自适应屏幕宽度 |

## 📸 界面预览

![登录与仪表盘](docs/images/1.png)
![主机管理](docs/images/2.png)
![主机监控](docs/images/3.png)
![批量执行](docs/images/4.png)
![报警中心](docs/images/5.png)

## 🚀 快速开始

### Docker Compose（推荐）

```bash
git clone https://github.com/linuxcto8899/X-ops.git
cd X-ops

# 构建前端
cd frontend
npm install
npm run build
cp -r dist ../deploy/frontend-dist
cd ..

# 配置并启动
cd deploy
cp ../.env.example .env   # 修改 DJANGO_SECRET_KEY / POSTGRES_PASSWORD
docker compose up -d --build
```

详细步骤见 **[安装文档 docs/INSTALL.md](docs/INSTALL.md)**。

### 手动部署（systemd + Nginx + HTTPS）

```bash
# 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
daphne -b 0.0.0.0 -p 8000 ops_platform.asgi:application

# 前端（构建产物 + Nginx 代理）
cd frontend && npm install && npm run build
```

## 📁 项目结构

```
X-ops/
├── backend/               # Django 后端
│   ├── ops_platform/      # 项目配置（settings/asgi/celery/urls）
│   ├── accounts/          # 用户/角色/权限
│   ├── hosts/             # 主机/分组/凭据/SSH
│   ├── docker/            # Docker 管理（容器/镜像/网络/日志）
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
daphne -b 127.0.0.1 -p 8000 ops_platform.asgi:application   # WebSocket 需 daphne

# 前端
cd frontend
npm install
npm run dev
```

详见 **[开发文档 docs/DEVELOP.md](docs/DEVELOP.md)**。

## 🐳 Docker 镜像

```bash
# 构建并推送至 Docker Hub
cd X-ops
./deploy/docker-push.sh push <你的docker.io用户名>
```

## 📄 License

Copyright © 2025-2026 X-ops · t.me/@linuxcto998 · QQ:5609648

个人项目，保留所有权利，禁止未经授权用于商业用途。
