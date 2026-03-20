# nanobot Web Channel - 部署文档

## 部署架构

```
┌─────────────────────────────────────────────────┐
│                    用户浏览器                   │
└──────────────────┬──────────────────────────────┘
                   │
                   │ HTTP/WSS
                   ▼
┌─────────────────────────────────────────────────┐
│           nanobot-web (Next.js)                │
│          http://localhost:3000                 │
└──────────────────┬──────────────────────────────┘
                   │
                   │ WebSocket/HTTP
                   ▼
┌─────────────────────────────────────────────────┐
│      nanobot (FastAPI WebChannel)              │
│           ws://localhost:8765                  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│          seekdb (Database)                     │
│         mysql://localhost:2881                 │
└─────────────────────────────────────────────────┘
```

## 环境要求

### 系统要求
- **操作系统**: Linux/macOS/Windows
- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 20.10+ (用于 seekdb)

### 网络要求
- 端口可用性:
  - `2881`: seekdb 数据库
  - `2886`: seekdb Web 管理界面
  - `8765`: nanobot WebChannel
  - `3000`: nanobot-web 前端（开发）

## 快速部署

### 1. 使用 Docker Compose（推荐）

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # seekdb 数据库
  seekdb:
    image: oceanbase/seekdb:latest
    container_name: nanobot-seekdb
    ports:
      - "2881:2881"  # 数据库端口
      - "2886:2886"  # 管理页面端口
    environment:
      - ROOT_PASSWORD=seekdb
    volumes:
      - seekdb_data:/root/ob
    command:
      - "-o"
      - "memory_limit=2G"
    restart: unless-stopped

volumes:
  seekdb_data:
```

**启动服务**:
```bash
docker-compose up -d
```

**验证服务**:
```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs seekdb

# 访问管理界面
open http://localhost:2886
```

### 2. 初始化数据库

```bash
cd /Users/white/dev/github/nanobot
python -m nanobot.web.init_db init
```

**预期输出**:
```
✓ seekdb 数据库表初始化完成
```

### 3. 配置 nanobot

编辑 `~/.nanobot/config.json`:

```json
{
  "database": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 2881,
    "user": "root",
    "password": "seekdb",
    "database": "nanobot",
    "pool_size": 10
  },
  "channels": {
    "web": {
      "enabled": true,
      "host": "127.0.0.1",
      "port": 8765,
      "cors_origins": ["http://localhost:3000"],
      "auth_token": "",
      "allow_from": [],
      "max_connections": 100,
      "enable_history_api": true,
      "persist_to_db": true
    }
  }
}
```

### 4. 启动 nanobot

```bash
cd /Users/white/dev/github/nanobot
nanobot gateway
```

**预期输出**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765
INFO:     Web channel enabled
INFO:     Outbound dispatcher started
```

### 5. 启动前端

```bash
cd /Users/white/dev/github/nanobot-ui
npm install  # 首次运行
npm run dev
```

**预期输出**:
```
  ▲ Next.js 14.2.35
  - Local:        http://localhost:3000
  - Network:      http://192.168.1.100:3000

 ✓ Ready in 2.3s
```

### 6. 验证部署

打开浏览器访问: http://localhost:3000

**检查清单**:
- [ ] 页面正常加载
- [ ] WebSocket 连接成功（浏览器控制台无错误）
- [ ] 可以发送消息
- [ ] 可以接收 AI 回复
- [ ] 会话列表正常显示
- [ ] 创建新会话正常
- [ ] 搜索功能正常

---

## 生产环境部署

### 1. 前端部署

#### 方案 A: Vercel（推荐）

```bash
cd /Users/white/dev/github/nanobot-ui

# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel

# 设置环境变量
vercel env add NEXT_PUBLIC_WS_URL production
# 输入: wss://your-domain.com

# 设置生产域名
vercel --prod
```

#### 方案 B: Docker

创建 `Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

构建和运行:
```bash
# 构建镜像
docker build -t nanobot-web .

# 运行容器
docker run -d -p 3000:3000 \
  -e NEXT_PUBLIC_WS_URL=wss://your-domain.com \
  nanobot-web
```

#### 方案 C: Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 2. 后端部署

#### 方案 A: Systemd 服务

创建 `/etc/systemd/system/nanobot.service`:

```ini
[Unit]
Description=nanobot AI Assistant
After=network.target

[Service]
Type=simple
User=nanobot
WorkingDirectory=/opt/nanobot
Environment="PATH=/opt/nanobot/venv/bin"
ExecStart=/opt/nanobot/venv/bin/nanobot gateway
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nanobot
sudo systemctl start nanobot
sudo systemctl status nanobot
```

#### 方案 B: Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8765

# 启动命令
CMD ["nanobot", "gateway"]
```

构建和运行:
```bash
# 构建镜像
docker build -t nanobot .

# 运行容器
docker run -d \
  --name nanobot \
  -p 8765:8765 \
  -v ~/.nanobot:/root/.nanobot \
  nanobot
```

#### 方案 C: Nginx 反向代理 + SSL

```nginx
upstream nanobot_backend {
    server localhost:8765;
}

server {
    listen 80;
    server_name api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://nanobot_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    # REST API 代理
    location /api/ {
        proxy_pass http://nanobot_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 3. 数据库部署

#### 生产环境配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  seekdb:
    image: oceanbase/seekdb:latest
    container_name: nanobot-seekdb
    ports:
      - "2881:2881"
      - "2886:2886"
    environment:
      - ROOT_PASSWORD=${DB_PASSWORD}
      - MEMORY_LIMIT=4G
    volumes:
      - seekdb_data:/root/ob
      - ./backup:/backup
    restart: always
    command:
      - "-o"
      - "memory_limit=4G"

volumes:
  seekdb_data:
```

#### 数据持久化

```bash
# 定期备份脚本
cat > backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec nanobot-seekdb mysqldump -uroot -p${DB_PASSWORD} nanobot > ${BACKUP_DIR}/nanobot_${DATE}.sql
# 保留最近 7 天的备份
find ${BACKUP_DIR} -name "nanobot_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到 crontab（每天凌晨 2 点备份）
crontab -e
# 0 2 * * * /path/to/backup.sh
```

---

## 监控和日志

### 日志配置

```python
# nanobot/config/logging.py
from loguru import logger

logger.add(
    "/var/log/nanobot/web.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    backtrace=True,
    diagnose=True
)
```

### 健康检查

```bash
# API 健康检查
curl http://localhost:8765/health

# 预期输出
{"status":"healthy","database":true}
```

### 监控指标

- WebSocket 连接数
- API 响应时间
- 数据库连接池状态
- 错误率

---

## 安全加固

### 1. CORS 配置

```json
{
  "channels": {
    "web": {
      "cors_origins": [
        "https://your-domain.com",
        "https://www.your-domain.com"
      ]
    }
  }
}
```

### 2. 认证配置

```json
{
  "channels": {
    "web": {
      "auth_token": "your-secret-token-here"
    }
  }
}
```

前端使用:
```javascript
const ws = new WebSocket('wss://api.your-domain.com/ws/session_id?token=your-secret-token-here');
```

### 3. 速率限制（计划中）

```python
# 使用 slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/conversations")
@limiter.limit("60/minute")
async def list_conversations():
    ...
```

---

## 故障排查

### 常见问题

#### 1. WebSocket 连接失败

**症状**: 浏览器控制台显示 `WebSocket connection failed`

**排查步骤**:
```bash
# 检查后端是否运行
curl http://localhost:8765/health

# 检查端口是否被占用
lsof -i :8765

# 检查防火墙
sudo ufw status
```

**解决方案**:
- 确认 nanobot gateway 正在运行
- 检查 CORS 配置是否包含前端域名
- 检查 WebSocket URL 是否正确

#### 2. 数据库连接失败

**症状**: `Database connection failed`

**排查步骤**:
```bash
# 检查 seekdb 是否运行
docker ps | grep seekdb

# 测试数据库连接
mysql -h127.0.0.1 -P2881 -uroot -pseekdb -e "SELECT 1"

# 检查数据库日志
docker logs nanobot-seekdb
```

**解决方案**:
- 启动 seekdb: `docker-compose up -d seekdb`
- 检查密码配置
- 初始化数据库表: `python -m nanobot.web.init_db init`

#### 3. 消息发送失败

**症状**: 发送消息后无响应

**排查步骤**:
```bash
# 检查 WebSocket 消息
# 浏览器控制台 -> Network -> WS -> Messages

# 检查后端日志
journalctl -u nanobot -f

# 检查 AgentLoop 是否运行
```

**解决方案**:
- 检查 LLM API 配置
- 检查消息总线状态
- 查看后端错误日志

#### 4. 前端构建失败

**症状**: `npm run build` 报错

**排查步骤**:
```bash
# 清理缓存
rm -rf .next node_modules
npm install

# 检查 Node 版本
node --version  # 应该 >= 18

# 检查类型错误
npm run type-check
```

---

## 性能调优

### 1. 数据库连接池

```json
{
  "database": {
    "pool_size": 20  // 增加连接池大小
  }
}
```

### 2. uvicorn 配置

```python
# nanobot/web/app.py
config = uvicorn.Config(
    app=app,
    host="0.0.0.0",
    port=8765,
    log_level="info",
    access_log=False,
    workers=4,              # 多进程
    limit_concurrency=1000,  # 最大并发连接
    timeout_keep_alive=30
)
```

### 3. 前端优化

```javascript
// next.config.js
module.exports = {
  // 生产环境优化
  swcMinify: true,
  reactStrictMode: true,

  // 压缩
  compress: true,

  // 图片优化
  images: {
    domains: ['your-domain.com'],
  },

  // 输出模式
  output: 'standalone',
}
```

---

## 升级策略

### 滚动升级

```bash
# 1. 拉取最新代码
git pull origin feat/web-channel

# 2. 更新依赖
pip install -e .

# 3. 重启服务
sudo systemctl restart nanobot
```

### 数据库迁移

```bash
# 备份
python -m nanobot.web.init_db backup

# 运行迁移脚本
python -m nanobot.web.migrations migrate
```

---

## 备份和恢复

### 完整备份

```bash
#!/bin/bash
# backup-all.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/nanobot"

# 备份数据库
docker exec nanobot-seekdb mysqldump -uroot -pseekdb nanobot > ${BACKUP_DIR}/db_${DATE}.sql

# 备份配置文件
cp ~/.nanobot/config.json ${BACKUP_DIR}/config_${DATE}.json

# 备份代码
tar -czf ${BACKUP_DIR}/nanobot_${DATE}.tar.gz /opt/nanobot

echo "Backup completed: ${DATE}"
```

### 恢复

```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1

# 恢复数据库
docker exec -i nanobot-seekdb mysql -uroot -pseekdb nanobot < /backup/nanobot/db_${BACKUP_DATE}.sql

# 恢复配置
cp /backup/nanobot/config_${BACKUP_DATE}.json ~/.nanobot/config.json

echo "Restore completed: ${BACKUP_DATE}"
```
