# Web Channel API Documentation

## Base URL
All endpoints are relative to the web channel base URL: `http://<host>:<port>/api`

## Authentication
All requests must include an `empId` query parameter identifying the user. The `empId` must be in the `allow_from` list configured for the web channel.

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
