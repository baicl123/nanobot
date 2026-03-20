# nanobot Web API 文档

## 基础信息

- **Base URL**: `http://localhost:8765`
- **WebSocket URL**: `ws://localhost:8765/ws/{session_id}`
- **API 版本**: v1
- **数据格式**: JSON

## 目录

- [健康检查](#健康检查)
- [会话管理 API](#会话管理-api)
- [消息管理 API](#消息管理-api)
- [搜索 API](#搜索-api)
- [WebSocket API](#websocket-api)

---

## 健康检查

### GET /health

检查 API 和数据库健康状态。

**请求示例**:
```bash
curl http://localhost:8765/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "database": true
}
```

**状态码**:
- `200 OK`: 服务正常

---

### GET /status

获取 API 和通道状态。

**请求示例**:
```bash
curl http://localhost:8765/status
```

**响应示例**:
```json
{
  "api": "running",
  "connections": 3,
  "web_channel_enabled": true
}
```

**状态码**:
- `200 OK`: 成功

---

## 会话管理 API

### POST /api/conversations

创建新会话。

**请求体**:
```json
{
  "user_id": "user_123",
  "title": "新对话",
  "channel": "web"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户 ID |
| title | string | 否 | 会话标题（默认："新对话"）|
| channel | string | 否 | 渠道标识（默认："web"）|

**响应示例**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_123",
  "title": "新对话",
  "channel": "web",
  "message_count": 0,
  "created_at": "2024-02-20T10:30:00Z"
}
```

**状态码**:
- `200 OK`: 创建成功
- `500 Internal Server Error`: 服务器错误

---

### GET /api/conversations

获取用户的会话列表。

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| user_id | string | 是 | - | 用户 ID |
| limit | integer | 否 | 50 | 最大返回数量（1-100）|

**请求示例**:
```bash
curl "http://localhost:8765/api/conversations?user_id=user_123&limit=20"
```

**响应示例**:
```json
{
  "conversations": [
    {
      "id": "conv_1",
      "title": "Python 编程问题",
      "channel": "web",
      "created_at": "2024-02-20T10:00:00Z",
      "updated_at": "2024-02-20T10:30:00Z",
      "message_count": 15
    },
    {
      "id": "conv_2",
      "title": "新对话",
      "channel": "web",
      "created_at": "2024-02-19T15:00:00Z",
      "updated_at": "2024-02-19T15:00:00Z",
      "message_count": 0
    }
  ]
}
```

**状态码**:
- `200 OK`: 成功
- `500 Internal Server Error`: 服务器错误

---

### GET /api/conversations/{conversation_id}

获取单个会话详情。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 会话 ID |

**请求示例**:
```bash
curl http://localhost:8765/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**响应示例**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_123",
  "title": "Python 编程问题",
  "channel": "web",
  "created_at": "2024-02-20T10:00:00Z",
  "updated_at": "2024-02-20T10:30:00Z",
  "message_count": 15,
  "metadata": {}
}
```

**状态码**:
- `200 OK`: 成功
- `404 Not Found`: 会话不存在
- `500 Internal Server Error`: 服务器错误

---

### PUT /api/conversations/{conversation_id}/title

更新会话标题。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 会话 ID |

**请求体**:
```json
{
  "title": "新标题"
}
```

**响应示例**:
```json
{
  "success": true,
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "新标题"
}
```

**状态码**:
- `200 OK`: 更新成功
- `404 Not Found`: 会话不存在
- `500 Internal Server Error`: 服务器错误

---

### DELETE /api/conversations/{conversation_id}

删除会话（级联删除所有消息）。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 会话 ID |

**请求示例**:
```bash
curl -X DELETE http://localhost:8765/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**响应示例**:
```json
{
  "success": true,
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**状态码**:
- `200 OK`: 删除成功
- `404 Not Found`: 会话不存在
- `500 Internal Server Error`: 服务器错误

---

## 消息管理 API

### GET /api/messages/{conversation_id}

获取会话的消息列表。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 会话 ID |

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | 否 | 100 | 最大返回数量（1-500）|

**请求示例**:
```bash
curl "http://localhost:8765/api/messages/conv_123?limit=50"
```

**响应示例**:
```json
{
  "conversation_id": "conv_123",
  "messages": [
    {
      "id": "msg_1",
      "conversation_id": "conv_123",
      "role": "user",
      "content": "如何用 Python 实现快速排序？",
      "metadata": {},
      "created_at": "2024-02-20T10:00:00Z"
    },
    {
      "id": "msg_2",
      "conversation_id": "conv_123",
      "role": "assistant",
      "content": "以下是快速排序的 Python 实现...",
      "metadata": {},
      "created_at": "2024-02-20T10:00:05Z"
    }
  ]
}
```

**状态码**:
- `200 OK`: 成功
- `404 Not Found`: 会话不存在
- `500 Internal Server Error`: 服务器错误

---

### POST /api/messages

创建新消息。

**请求体**:
```json
{
  "conversation_id": "conv_123",
  "content": "这是一条新消息",
  "role": "user",
  "metadata": {}
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 会话 ID |
| content | string | 是 | 消息内容 |
| role | string | 否 | 角色（user/assistant/system，默认：user）|
| metadata | object | 否 | 元数据 |

**响应示例**:
```json
{
  "success": true,
  "message_id": "msg_456",
  "conversation_id": "conv_123"
}
```

**状态码**:
- `200 OK`: 创建成功
- `404 Not Found`: 会话不存在
- `500 Internal Server Error`: 服务器错误

---

### GET /api/messages/{conversation_id}/count

获取会话的消息数量。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 会话 ID |

**请求示例**:
```bash
curl http://localhost:8765/api/messages/conv_123/count
```

**响应示例**:
```json
{
  "conversation_id": "conv_123",
  "count": 42
}
```

**状态码**:
- `200 OK`: 成功
- `500 Internal Server Error`: 服务器错误

---

## 搜索 API

### GET /api/search/messages

跨会话搜索消息。

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| user_id | string | 是 | 用户 ID |
| limit | integer | 否 | 最大返回数量（默认：20，最大：100）|

**请求示例**:
```bash
curl "http://localhost:8765/api/search/messages?q=Python&user_id=user_123&limit=10"
```

**响应示例**:
```json
{
  "query": "Python",
  "count": 5,
  "results": [
    {
      "id": "msg_1",
      "content": "如何用 Python 实现快速排序？",
      "role": "user",
      "created_at": "2024-02-20T10:00:00Z",
      "title": "Python 编程问题",
      "conversation_id": "conv_123"
    },
    {
      "id": "msg_5",
      "content": "Python 的装饰器是如何工作的？",
      "role": "user",
      "created_at": "2024-02-19T15:30:00Z",
      "title": "装饰器问题",
      "conversation_id": "conv_456"
    }
  ]
}
```

**状态码**:
- `200 OK`: 搜索成功
- `400 Bad Request`: 搜索关键词为空
- `500 Internal Server Error`: 服务器错误

---

## WebSocket API

### 连接

**WebSocket URL**: `ws://localhost:8765/ws/{session_id}`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 否 | 认证令牌（如果配置）|
| user_id | string | 否 | 用户 ID（默认："anonymous"）|

**连接示例** (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8765/ws/session_123?user_id=user_456');
```

### 消息格式

所有消息都遵循以下格式：
```json
{
  "type": "message_type",
  "data": { /* 消息数据 */ }
}
```

### 客户端 → 服务端

#### 发送消息
```json
{
  "type": "message",
  "data": {
    "conversation_id": "conv_123",
    "content": "你好，请问有什么可以帮助？"
  }
}
```

#### 请求历史
```json
{
  "type": "get_history",
  "data": {
    "conversation_id": "conv_123"
  }
}
```

#### 心跳
```json
{
  "type": "ping",
  "data": {}
}
```

### 服务端 → 客户端

#### 连接确认
```json
{
  "type": "connected",
  "data": {
    "session_id": "session_123",
    "conversation_id": "conv_123"
  }
}
```

#### 新消息
```json
{
  "type": "message",
  "data": {
    "conversation_id": "conv_123",
    "content": "你好！我是 nanobot AI 助手...",
    "role": "assistant",
    "timestamp": "2024-02-20T10:30:00Z"
  }
}
```

#### 历史消息
```json
{
  "type": "history",
  "data": {
    "conversation_id": "conv_123",
    "messages": [
      {
        "id": "msg_1",
        "conversation_id": "conv_123",
        "role": "user",
        "content": "你好",
        "created_at": "2024-02-20T10:00:00Z"
      }
    ]
  }
}
```

#### 错误
```json
{
  "type": "error",
  "data": {
    "message": "会话不存在"
  }
}
```

#### 心跳响应
```json
{
  "type": "pong",
  "data": {}
}
```

### 错误码

| 关闭码 | 说明 |
|--------|------|
| 1000 | 正常关闭 |
| 1003 | 不支持的数据类型 |
| 1008 | 策略违反（如超出最大连接数）|
| 1011 | 服务器内部错误 |

### 使用示例

```javascript
// 建立 WebSocket 连接
const ws = new WebSocket('ws://localhost:8765/ws/my-session?user_id=user_123');

// 监听连接打开
ws.onopen = () => {
  console.log('WebSocket connected');
};

// 监听消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'connected':
      console.log('Connection confirmed:', message.data);
      break;
    case 'message':
      console.log('New message:', message.data);
      displayMessage(message.data);
      break;
    case 'error':
      console.error('Error:', message.data.message);
      break;
  }
};

// 发送消息
function sendMessage(content) {
  ws.send(JSON.stringify({
    type: 'message',
    data: {
      conversation_id: 'conv_123',
      content: content
    }
  }));
}

// 关闭连接
ws.close();
```

---

## 错误响应格式

所有 API 错误响应遵循以下格式：

```json
{
  "error": "错误类型",
  "detail": "详细错误信息"
}
```

**常见错误**:

| 状态码 | 错误类型 | 说明 |
|--------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |

---

## 数据类型

### Conversation
```typescript
interface Conversation {
  id: string;              // UUID
  user_id: string;         // 用户 ID
  title: string;           // 会话标题
  channel: string;         // 渠道标识
  created_at: string;      // ISO 8601 时间戳
  updated_at: string;      // ISO 8601 时间戳
  message_count: number;   // 消息数量
  metadata?: object;       // 元数据（可选）
}
```

### Message
```typescript
interface Message {
  id: string;              // UUID
  conversation_id: string; // 会话 ID
  role: 'user' | 'assistant' | 'system';  // 角色
  content: string;         // 消息内容
  metadata?: object;       // 元数据（可选）
  created_at: string;      // ISO 8601 时间戳
}
```

---

## 速率限制

当前版本未实现速率限制，计划在未来添加：

- 每用户每分钟最多 60 个请求
- WebSocket 每秒最多 10 条消息

---

## 更新日志

### v0.1.0 (2024-02-20)
- 初始版本
- 基础 REST API
- WebSocket 支持
- 数据库持久化
- 搜索功能
