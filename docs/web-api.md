# Web Channel API 文档

Web Channel 提供了基于 HTTP + WebSocket 的聊天接口，支持多用户多会话。本文档详细描述了所有可用的 API 端点。

## 目录

- [配置](#配置)
- [REST API](#rest-api)
- [WebSocket API](#websocket-api)
- [前端访问](#前端访问)
- [权限模型](#权限模型)
- [CORS 配置](#cors-配置)
- [数据存储](#数据存储)
- [错误码](#错误码)

## 配置

Web Channel 支持两种配置方式：

### 1. 独立配置文件 (推荐)

配置文件位置：`~/.nanobot/web.json` （使用自定义 `--config` 时，位于同目录下）

示例配置：
```json
{
  "enabled": true,
  "host": "0.0.0.0",
  "port": 18791,
  "allowFrom": ["*"],
  "corsOrigins": []
}
```

配置字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `enabled` | boolean | 是 | 是否启用 Web Channel |
| `host` | string | 否 | 监听地址，默认 `0.0.0.0` |
| `port` | integer | 否 | 监听端口，默认 `18791` |
| `allowFrom` | string[] | 是 | 允许访问的用户 ID 列表，`["*"]` 允许所有 |
| `corsOrigins` | string[] | 否 | CORS 允许的源 |

如果独立配置文件存在，它会**完全覆盖**主配置 `config.json` 中的设置。如果不存在，回退到使用主配置。

### 2. 主配置中 (传统方式)

在主 `config.json` 的 `channels.web` 节配置，格式同上。

## Base URL
所有端点都相对于 Web Channel 根地址：`http://<host>:<port>`

## 认证
所有 API 请求必须包含 `empId` 查询参数标识用户。`empId` 必须在 `allowFrom` 列表中才允许访问。

---

## REST API Endpoints

### 1. List User Sessions
**GET /api/sessions**

Get all sessions for the current user.

**Query Parameters:**
- `empId` (required): User's employee ID

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "web:60079031:550e8400-e29b-41d4-a716-446655440000",
      "user_id": "60079031",
      "name": "New Chat",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:05:00Z",
      "last_message": "Hello, how can I help you?"
    }
  ]
}
```

---

### 2. Create New Session
**POST /api/sessions**

Create a new chat session for the user.

**Query Parameters:**
- `empId` (required): User's employee ID
- `name` (optional): Session name (default: "New Chat")

**Response:**
```json
{
  "session": {
    "session_id": "web:60079031:550e8400-e29b-41d4-a716-446655440000",
    "user_id": "60079031",
    "name": "New Chat",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "last_message": ""
  }
}
```

---

### 3. Update Session Name
**PUT /api/sessions/{session_id}**

Update the name of an existing session.

**Path Parameters:**
- `session_id` (required): ID of the session to update

**Query Parameters:**
- `empId` (required): User's employee ID
- `name` (required): New session name

**Response:**
```json
{
  "session": {
    "session_id": "web:60079031:550e8400-e29b-41d4-a716-446655440000",
    "user_id": "60079031",
    "name": "Project Planning",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:10:00Z",
    "last_message": "Hello, how can I help you?"
  }
}
```

---

### 4. Delete Session
**DELETE /api/sessions/{session_id}**

Delete a session.

**Path Parameters:**
- `session_id` (required): ID of the session to delete

**Query Parameters:**
- `empId` (required): User's employee ID

**Response:**
```json
{
  "success": true
}
```

---

## WebSocket API

### Connection
**URL:** `ws://<host>:<port>/ws?empId=<employee_id>&deptname=<department_name>`

**Query Parameters:**
- `empId` (required): User's employee ID
- `deptname` (optional): User's department name

**Connection Flow:**
1. Client connects to WebSocket endpoint with query parameters
2. Server validates `empId` against `allow_from` list
3. If valid, connection is accepted; otherwise, connection is closed with code 403

---

### Client to Server Messages

#### 1. Chat Message
Send a message to the agent.

```json
{
  "type": "message",
  "data": {
    "content": "What's the weather today?",
    "session_id": "web:60079031:550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 2. Ping
Heartbeat message to keep connection alive.

```json
{
  "type": "ping",
  "data": {}
}
```

---

### Server to Client Messages

#### 1. Assistant Message
Response from the agent (including streaming chunks).

```json
{
  "type": "message",
  "data": {
    "session_id": "web:60079031:550e8400-e29b-41d4-a716-446655440000",
    "content": "The weather today is sunny with a high of 25°C.",
    "role": "assistant",
    "metadata": {},
    "is_progress": false,
    "is_tool_hint": false
  }
}
```

**Fields:**
- `is_progress`: If `true`, this is a partial streaming chunk, not the complete response
- `is_tool_hint`: If `true`, this is a tool call hint (e.g., "Reading file: README.md")

#### 2. Pong
Response to ping message.

```json
{
  "type": "pong",
  "data": {}
}
```

#### 3. Error
Error message.

```json
{
  "type": "error",
  "data": {
    "message": "Invalid session ID"
  }
}
```

---

## Message Metadata
All messages include metadata with user information:
- `emp_id`: User's employee ID
- `deptname`: User's department name
- `session_id`: Current session ID

This metadata is automatically added to the system prompt so the agent is aware of the user's identity and department.

---

## Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Missing or invalid parameters |
| 403 | Forbidden - User not in allow_from list |
| 404 | Not Found - Session does not exist or does not belong to user |
| 500 | Internal Server Error |

---

## WebSocket Close Codes
| Code | Meaning |
|------|---------|
| 1000 | Normal closure |
| 1001 | Server shutting down |
| 403 | Access denied - Invalid empId |

---

## 前端访问 URL 格式

内置的前端页面可以通过 URL 参数传递用户信息:

```
http://localhost:9527/?empId=testuser&deptname=IT
```

参数:
- `empId` (必填): 用户 ID
- `deptname` (可选): 部门名称

## 权限模型

- `allowFrom` 为空: 拒绝所有连接
- `"*"` 在 `allowFrom` 中: 允许所有用户
- 否则: 只有列表中的用户 ID 允许连接

## CORS 配置

如果前端从不同域名访问，请在 `corsOrigins` 中添加允许的源:

```json
{
  "corsOrigins": ["https://your-frontend.com", "http://localhost:3000"]
}
```

## 数据存储

- 会话元数据存储在 SQLite 数据库: `{workspace}/sessions.db`
- 消息历史存储在 JSONL 文件: `{workspace}/sessions/web_{user_id}_{uuid}.jsonl`

## JavaScript 连接示例

```javascript
// 连接 WebSocket
const ws = new WebSocket(`ws://${window.location.host}/ws?empId=testuser&deptname=IT`);

ws.onopen = () => {
  console.log('Connected to nanobot web channel');
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'message') {
    const { content, isProgress } = msg.data;
    if (isProgress) {
      // 更新流式响应
      updateStreamingContent(content);
    } else {
      // 添加完整消息
      addMessage('assistant', content);
    }
  }
};

ws.onerror = () => {
  console.error('WebSocket connection error');
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // 自动重连
  setTimeout(() => connectWs(), 3000);
};

// 发送消息
function sendMessage(content, sessionId) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'message',
      data: { content, session_id: sessionId }
    }));
  }
}

// 心跳保持连接
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping', data: {} }));
  }
}, 30000);
```

## 完整示例

启动 gateway 后，通过以下步骤测试:

1. 确保 `web.json` 中 `enabled` 为 `true`，`allowFrom` 包含 `["*"]`
2. 启动 gateway: `nanobot gateway`
3. 打开浏览器访问: `http://localhost:9527/?empId=testuser&deptname=IT`
4. 页面会自动连接 WebSocket
5. 输入消息发送，nanobot 会通过 WebSocket 流式返回回复

## 相关文档

- [Web Channel 实现指南](./web-channel.md) - 架构设计、部署说明

