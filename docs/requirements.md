# nanobot Web Channel - 需求文档

## 项目概述

为 nanobot AI 助手添加基于 Web 的聊天界面支持，通过 WebSocket 和 REST API 提供实时对话能力。

## 功能需求

### 1. 后端服务 (FastAPI)

#### 1.1 WebSocket 通信
- **WS /ws/{session_id}**
  - 支持实时双向通信
  - 会话隔离（每个 WebSocket 连接对应一个会话）
  - 心跳检测（30s 间隔）
  - 自动重连机制（指数退避）

#### 1.2 REST API

**会话管理 API**
- `POST /api/conversations` - 创建新会话
  - 自动生成会话 ID
  - 支持自定义标题和用户 ID
- `GET /api/conversations?user_id={id}` - 获取用户会话列表
  - 按更新时间倒序排列
  - 支持分页（limit 参数）
- `GET /api/conversations/{id}` - 获取单个会话详情
- `PUT /api/conversations/{id}/title` - 更新会话标题
- `DELETE /api/conversations/{id}` - 删除会话（级联删除消息）

**消息管理 API**
- `GET /api/messages/{conversation_id}` - 获取会话消息
  - 按时间顺序排列
  - 支持分页
- `POST /api/messages` - 创建消息
  - 自动保存到数据库
  - 更新会话消息计数
- `GET /api/messages/{conversation_id}/count` - 获取消息数量

**搜索 API**
- `GET /api/search/messages?q={keyword}&user_id={id}` - 跨会话搜索
  - 全文索引搜索
  - 支持中文分词
  - 返回匹配的消息和所属会话信息

**健康检查 API**
- `GET /health` - 健康检查
  - 检查数据库连接状态
  - 返回 API 状态
- `GET /status` - 通道状态
  - 当前连接数
  - WebChannel 启用状态

#### 1.3 权限控制
- 基于 `allow_from` 配置的白名单
- 支持 auth_token 认证（可选）
- 连接数限制（max_connections）

### 2. 数据持久化

#### 2.1 数据库支持
- 使用 seekdb（兼容 MySQL 协议）
- 连接池管理
- 自动重连机制

#### 2.2 数据模型

**会话表 (conversations)**
```sql
- id: VARCHAR(64) - UUID 主键
- user_id: VARCHAR(255) - 用户 ID
- channel: VARCHAR(50) - 渠道标识
- title: VARCHAR(500) - 会话标题
- created_at: TIMESTAMP - 创建时间
- updated_at: TIMESTAMP - 更新时间
- message_count: INT - 消息数量
- metadata: JSON - 元数据
```

**消息表 (messages)**
```sql
- id: VARCHAR(64) - UUID 主键
- conversation_id: VARCHAR(64) - 会话 ID（外键）
- role: ENUM - 角色 (user/assistant/system)
- content: TEXT - 消息内容
- metadata: JSON - 元数据
- created_at: TIMESTAMP - 创建时间
```

#### 2.3 索引设计
- 会话表: (user_id, updated_at) 复合索引
- 消息表: (conversation_id, created_at) 复合索引
- 消息表: content 全文索引（ngram 分词）

### 3. 消息流集成

#### 3.1 与 nanobot 消息总线集成
- 实现 `BaseChannel` 接口
- 接收 `InboundMessage` 并发布到总线
- 订阅 `OutboundMessage` 并发送到 WebSocket

#### 3.2 消息处理流程
```
用户消息
  ↓
WebSocket 接收
  ↓
WebChannel.handle_websocket()
  ↓
保存到数据库（可选）
  ↓
发布到消息总线 (InboundMessage)
  ↓
AgentLoop 处理
  ↓
生成响应 (OutboundMessage)
  ↓
WebChannel 发送到 WebSocket
  ↓
保存到数据库（可选）
  ↓
用户接收消息
```

### 4. 配置管理

#### 4.1 WebConfig 配置项
```json
{
  "enabled": true,              // 是否启用
  "host": "127.0.0.1",          // 监听地址
  "port": 8765,                 // 监听端口
  "cors_origins": [...],        // CORS 允许来源
  "auth_token": "",             // 认证令牌（可选）
  "allow_from": [],             // 用户白名单
  "max_connections": 100,       // 最大连接数
  "enable_history_api": true,   // 启用历史 API
  "persist_to_db": true         // 持久化到数据库
}
```

#### 4.2 DatabaseConfig 配置项
```json
{
  "enabled": true,              // 是否启用数据库
  "host": "127.0.0.1",          // 数据库主机
  "port": 2881,                 // 数据库端口
  "user": "root",               // 用户名
  "password": "seekdb",         // 密码
  "database": "nanobot",        // 数据库名
  "pool_size": 10               // 连接池大小
}
```

## 非功能需求

### 性能要求
- WebSocket 消息延迟 < 100ms
- REST API 响应时间 < 200ms (P95)
- 支持并发连接数 ≥ 100
- 数据库连接池复用

### 可靠性要求
- WebSocket 自动重连（指数退避）
- 数据库连接自动恢复
- 错误日志记录
- 优雅关闭

### 可扩展性要求
- 支持添加新的消息元数据字段
- 支持多数据库（通过配置切换）
- 支持 WebSocket 消息类型扩展

### 安全性要求
- CORS 配置
- 可选的 Token 认证
- 用户白名单机制
- SQL 注入防护（参数化查询）

## 技术约束

### 后端技术栈
- Python 3.11+
- FastAPI 0.104+
- uvicorn (ASGI 服务器)
- aiomysql (异步 MySQL 客户端)
- Pydantic (数据验证)

### 依赖项
- nanobot 消息总线 (`nanobot.bus`)
- nanobot 配置管理 (`nanobot.config`)
- nanobot session 管理 (`nanobot.session`)

## 未来增强功能

### Phase 2 (短期)
- [ ] Agent 自动生成会话标题
- [ ] 会话标题编辑历史
- [ ] 消息已读/未读状态
- [ ] 用户画像和偏好设置

### Phase 3 (中期)
- [ ] 文件上传和存储
- [ ] 语音消息转文字
- [ ] 流式响应（SSE）
- [ ] 消息编辑和删除

### Phase 4 (长期)
- [ ] 向量搜索集成
- [ ] 多模态消息（图片、视频）
- [ ] 会话分享和导出
- [ ] 实时协作（多用户）

## 验收标准

### 功能验收
- [ ] WebSocket 连接建立和断开
- [ ] 消息实时收发
- [ ] 会话 CRUD 操作
- [ ] 消息历史查询
- [ ] 跨会话搜索
- [ ] 数据库持久化

### 性能验收
- [ ] 100 并发连接无异常
- [ ] API 响应时间达标
- [ ] 内存占用稳定（无内存泄漏）

### 集成验收
- [ ] 与 nanobot 消息总线集成正常
- [ ] 与 AgentLoop 交互正常
- [ ] 不影响其他 channel（telegram, discord 等）
