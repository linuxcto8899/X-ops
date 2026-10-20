# X-ops 开发文档

面向开发者：项目架构、模块说明、二次开发指南。

- **版权**：t.me/@linuxcto998 · QQ:5609648

---

## 一、技术栈

| 层 | 技术 |
|----|------|
| 后端 | Django 5.2 · DRF · SimpleJWT · Celery · Channels/Daphne · Paramiko · openpyxl |
| 前端 | Vue 3 · Vite · Ant Design Vue · ECharts · xterm.js · Pinia · vue-router |
| 数据库 | SQLite（默认）/ PostgreSQL |
| 缓存/队列 | Redis |
| WebSocket | Channels + Daphne（在线终端 / 批量执行回显） |

---

## 二、本地开发

### 2.1 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 环境变量（复制模板）
cp .env.example .env
# 编辑 DJANGO_SECRET_KEY 等

python manage.py migrate
# WebSocket 开发：用 daphne 而非 runserver
daphne -b 127.0.0.1 -p 8000 ops_platform.asgi:application
# 或纯 HTTP 调试：python manage.py runserver 127.0.0.1:8000
```

### 2.2 前端

```bash
cd frontend
npm install
npm run dev   # Vite dev server，默认代理 /api 到 8000
npm run build # 生产构建，输出 dist/
```

### 2.3 Celery（本地测试报警/监控定时任务）

```bash
celery -A ops_platform worker -l info --pool=solo   # 终端 1
celery -A ops_platform beat -l info                 # 终端 2
```

> 提示：单机部署时 `settings.py` 中 `CHANNEL_LAYERS` 已配置为内存后端，无需 Redis 即可运行 WebSocket；Celery 仍需 Redis broker。

---

## 三、项目结构

```
backend/
├── ops_platform/          # 项目配置
│   ├── settings.py        # 全局配置（.env 自动加载）
│   ├── asgi.py            # ASGI（WebSocket）
│   ├── celery.py          # Celery 应用 + beat 调度
│   └── urls.py            # 路由聚合
├── accounts/              # 用户 / 角色 / 权限
├── hosts/                 # 主机 / 分组 / 凭据 / SSH
│   ├── models.py          # Host（云商/地域/到期）、HostGroup、Credential
│   ├── ssh.py             # paramiko 封装：collect_facts/run_command/open_shell
│   └── crypto.py          # Fernet 加密
├── execution/             # 批量执行
│   ├── tasks.py           # 流式执行：逐行写入 ExecutionStream
│   └── models.py          # Execution / ExecutionResult / ExecutionStream
├── terminal/              # 在线终端
│   └── consumers.py       # WebSocket：SSH shell 桥接
├── files/                 # 文件管理 / 分发（SFTP）
├── deploy/                # 应用发布（Git 构建/发布/回滚/Webhook）
├── pipeline/              # 流水线编排
├── scheduler/             # 任务计划（once/cron/interval/报警）
├── monitor/               # 主机监控 + 报警
│   ├── collector.py       # 远程采集（base64 脚本）
│   ├── alerts.py          # 发信：SMTP/钉钉/企微/飞书/Server酱
│   └── models.py          # NotifyChannel/MonitorRule/Alert*
└── config_center/         # 配置中心（开放 API）

frontend/src/
├── api.js                 # axios 封装（JWT 拦截器）
├── store.js               # Pinia（token/user/lang）
├── router.js              # 路由
├── locales.js             # 中英双语
├── flags.js               # 国旗图片 + 云商映射
└── views/                 # 页面组件
```

---

## 四、核心机制

### 4.1 JWT 认证
- 登录：`POST /api/auth/token/` → `{access, refresh}`
- 请求头：`Authorization: Bearer <access>`
- WebSocket：`/ws/terminal/?token=<access>`

### 4.2 在线终端（WebSocket）
1. 前端连接 `/ws/terminal/?token=JWT`
2. Consumer 校验 JWT → paramiko 打开 SSH shell → 启动 reader 线程
3. `action: connect/input/resize/close` 驱动交互
4. 输出经 `run_coroutine_threadsafe` 推回浏览器

### 4.3 批量执行流式回显
1. `POST /api/exec/executions/` 创建执行 → Celery 异步执行
2. `execution/tasks.py` 用 `select` 逐块读取 stdout/stderr → 实时追加 `ExecutionStream.output`
3. 前端弹出 `/exec-stream/:executionId/:hostId` 页面：先轮询 streams 展示，同时可 WebSocket 交互

### 4.4 主机监控
- Celery beat 每 60s 调度 `monitor.tasks.collect_all_host_metrics`
- 采集脚本经 base64 传至远端执行（避免换行转义问题）
- 实时接口：`/api/monitor/host/<id>/live/`、`history/`、`processes/`

### 4.5 报警通知闭环
```
发信配置(NotifyChannel) → 联系人(AlertContact 引用渠道) → 通知组(AlertGroup)
    → 监控规则(MonitorRule.notify_group_id) → 报警触发 → notify_alert 逐渠道发送
```

---

## 五、二次开发示例

### 新增一个 App

```bash
cd backend
python manage.py startapp myapp
# settings.py INSTALLED_APPS 添加 'myapp'
# 编写 models/serializers/views/urls，参考 execution 模块
```

### 新增前端页面

```bash
# 在 frontend/src/views/ 新建 MyPage.vue
# router.js 添加路由
# Layout.vue 菜单添加入口
# locales.js 添加中英文文案
```

### 新增报警渠道

```python
# backend/monitor/models.py NotifyChannel.KIND_CHOICES 添加
# backend/monitor/alerts.py _deliver() / test_channel() 添加发送逻辑
# frontend/src/views/Alarm.vue KINDS 与配置表单添加
```

---

## 六、API 一览

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/auth/` | token / refresh |
| 账号 | `/api/accounts/` | users / roles / me / change-password |
| 主机 | `/api/hosts/` | hosts / groups / credentials |
| 执行 | `/api/exec/` | templates / executions / streams |
| 文件 | `/api/files/` | uploads / transfers / host/* |
| 发布 | `/api/deploy/` | apps / repositories / releases / webhook |
| 流水线 | `/api/pipeline/` | pipelines / runs |
| 监控 | `/api/monitor/` | rules / records / alerts / channels / host/* |
| 任务 | `/api/scheduler/` | tasks |
| 配置 | `/api/config/` | envs / services / configs / open |

---

**版权**：t.me/@linuxcto998 · QQ:5609648
