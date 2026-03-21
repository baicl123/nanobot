# Web Channel 数据库设计文档

## 概述

Web Channel 使用 SQLite 数据库存储**用户信息和会话元数据**，对话内容存储在 JSONL 文件中。

**注意**：用户验证由数据门户系统完成，本系统不做验证。

## 数据库位置

`{workspace}/web.db`

## 表结构

### users 表

用户信息表，工号为 primary key。

| 字段 | 类型 | 索引 | 可空 | 说明 |
|------|------|------|------|------|
| `emp_id` | TEXT | PK | NO | 工号，如 "60079031" |
| `deptname` | TEXT | NO | YES | 部门名称 |
| `created_at` | DATETIME | NO | NO | 首次访问时间 |
| `last_active_at` | DATETIME | NO | NO | 最后活跃时间 |
| `display_name` | TEXT | NO | YES | 显示名称 |

### sessions 表

会话元数据表。

| 字段 | 类型 | 索引 | 可空 | 说明 |
|------|------|------|------|------|
| `session_id` | TEXT | PK | NO | 会话 ID，格式：`web:{empId}:{uuid}` |
| `emp_id` | TEXT | FK | NO | 用户工号，关联 users.emp_id |
| `name` | TEXT | NO | NO | 会话名称，默认 "New Chat" |
| `created_at` | DATETIME | NO | NO | 创建时间 |
| `updated_at` | DATETIME | NO | NO | 最后更新时间 |
| `last_message` | TEXT | NO | NO | 最后一条消息预览（截断到 100 字符） |

## 数据访问逻辑

### 用户记录管理

1. **用户首次访问**：自动在 `users` 表创建记录
2. **用户后续访问**：更新 `users.last_active_at`
3. **用户验证**：不做验证，由数据门户系统完成

### 会话记录管理

1. **创建会话**：关联到 `users.emp_id`
2. **查询会话**：通过 `sessions.emp_id` 过滤
3. **删除会话**：级联删除（数据库层面不强制，应用层确保）

## 数据存储分层

```
web.db (元数据)
├── users 表 (用户信息)
└── sessions 表 (会话元数据)
    ↓ 只存储元数据
    ↓ 不存储对话内容

users/{empId}/sessions/web_{uuid}.jsonl (对话内容)
    ↓ 存储完整对话历史
    ↓ JSON Lines 格式
```

## 目录结构

```
workspace/
├── web.db                          ← SQLite 数据库
│   ├── users 表                    ← 用户信息
│   └── sessions 表                 ← 会话元数据
│
└── users/
    ├── 60079031/
    │   └── sessions/
    │       └── web_{uuid}.jsonl    ← 对话内容
    └── 60079214/
        └── sessions/
            └── web_{uuid}.jsonl
```

## 示例数据

### users 表示例

| emp_id | deptname | created_at | last_active_at |
|--------|----------|------------|----------------|
| 60079031 | IT | 2024-01-01T00:00:00Z | 2024-01-15T10:30:00Z |
| 60079214 | HR | 2024-01-02T00:00:00Z | 2024-01-14T09:15:00Z |

### sessions 表示例

| session_id | emp_id | name | created_at | last_message |
|------------|--------|------|------------|--------------|
| web:60079031:abc-123 | 60079031 | 技术咨询 | 2024-01-01T00:00:00Z | 如何配置 Python？ |
| web:60079031:def-456 | 60079031 | 项目讨论 | 2024-01-02T00:00:00Z | 好的，我们来... |
