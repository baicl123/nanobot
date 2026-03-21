# Web Channel 多用户、多会话隔离改造方案

## Context

当前问题：
- Web Channel 所有用户共享同一个 workspace 目录
- 所有用户共享 MEMORY.md 和 HISTORY.md
- 会话文件虽有 user_id 前缀，但都在同一目录
- 没有同时在线用户数限制

需求（已确认）：
- **只改造 Web Channel**，其他 channel 保持不变
- **完全隔离**：每个用户有独立的 workspace 隔离层：`workspace/users/{empId}/`
- **记忆完全隔离**：每个用户有自己的 `memory/MEMORY.md` 和 `memory/HISTORY.md`
- **会话目录隔离**：会话存储在 `users/{empId}/sessions/`
- 最大同时在线用户数配置（web.json 中设置）
- **web.db 只存储元数据**，不存储对话记录
- **web.db 包含 users 表**：工号为 key，新用户时自动创建
- **用户验证由数据门户系统完成**，我们不做验证
- **维护文档**：`docs/web-api.md` 和 `docs/database.md`
- **采用 TDD 开发**：测试代码放在 `tests_web/` 目录

---

## 开发方法：TDD (Test-Driven Development)

### 测试策略

1. **先写测试**，再写实现代码
2. **测试独立**：放在 `tests_web/` 目录（不与现有 `tests/` 混在一起）
3. **测试覆盖**：
   - 路径函数测试
   - 数据库操作测试
   - SessionManager 路由测试
   - 同时在线用户限制测试

### tests_web/ 目录结构

```
tests_web/
├── __init__.py
├── test_paths.py           # 用户路径函数测试
├── test_db.py             # 数据库 CRUD 测试
├── test_session_manager.py # SessionManager 路由测试
└── test_web_channel.py     # Web Channel 集成测试
```

---

## web.db 设计

### 数据库表结构

web.db **只存储元数据**，对话内容存储在 JSONL 文件中。

#### users 表

用户信息表，工号为 primary key。

| 字段 | 类型 | 索引 | 可空 | 说明 |
|------|------|------|------|------|
| `emp_id` | TEXT | PK | NO | 工号，如 "60079031" |
| `deptname` | TEXT | NO | YES | 部门名称 |
| `created_at` | DATETIME | NO | NO | 首次访问时间 |
| `last_active_at` | DATETIME | NO | NO | 最后活跃时间 |
| `display_name` | TEXT | NO | YES | 显示名称 |

#### sessions 表

会话元数据表。

| 字段 | 类型 | 索引 | 可空 | 说明 |
|------|------|------|------|------|
| `session_id` | TEXT | PK | NO | 会话 ID，格式：`web:{empId}:{uuid}` |
| `emp_id` | TEXT | FK | NO | 用户工号，关联 users.emp_id |
| `name` | TEXT | NO | NO | 会话名称，默认 "New Chat" |
| `created_at` | DATETIME | NO | NO | 创建时间 |
| `updated_at` | DATETIME | NO | NO | 最后更新时间 |
| `last_message` | TEXT | NO | NO | 最后一条消息预览（截断到 100 字符） |

### 数据访问逻辑

1. **用户首次访问**：自动在 `users` 表创建记录
2. **用户后续访问**：更新 `users.last_active_at`
3. **用户验证**：不做验证，由数据门户系统完成

---

## 目录结构

### 项目结构
```
nanobot/
├── nanobot/
│   ├── channels/
│   │   └── web.py
│   ├── web/
│   │   ├── models.py
│   │   ├── db.py
│   │   └── dependencies.py
│   └── ...
│
├── frontend/                       ←【新增】前端目录
│   └── index.html                  ← Demo 前端页面（从 nanobot/web/static/ 移动）
│
├── tests_web/                      ←【新增】Web Channel 测试目录
│   ├── __init__.py
│   ├── test_paths.py
│   ├── test_db.py
│   ├── test_session_manager.py
│   └── test_web_channel.py
│
└── docs/
    ├── web-api.md
    └── database.md
```

### 运行时 Workspace 结构
```
~/.nanobot/
├── web.json                        ← Web Channel 独立配置
├── config.json                     ← 主配置
│
└── workspace/
    ├── memory/                     ←【其他 channel 使用】
    ├── sessions/                   ←【其他 channel 使用】
    ├── skills/                     ← 全局技能（所有用户共享）
    ├── AGENTS.md / SOUL.md         ← 全局 bootstrap
    ├── web.db                      ←【全局】Web Channel 数据库（users + sessions）
    │
    └── users/                      ←【Web Channel 新增】用户隔离层
        ├── 60079031/               ← 员工号 60079031 的用户级 workspace
        │   ├── memory/
        │   │   ├── MEMORY.md       ← 60079031 的跨会话记忆
        │   │   └── HISTORY.md      ← 60079031 的历史日志
        │   └── sessions/
        │       └── web_{uuid}.jsonl ← 60079031 的会话（简化命名）
        └── 60079214/              ← 员工号 60079214 的用户级 workspace
            ├── memory/
            └── sessions/
                └── web_{uuid}.jsonl
```

### 前端说明
- 前端位于 `frontend/index.html`
- 极简 Demo 页面，用于测试用户功能
- 访问方式：`http://localhost:9527/?empId=60079031&deptname=IT`
- **目前不涉及前端改动**

---

## 实施步骤（TDD 顺序）

### 第一步：同步文档（先做）

在开始代码修改前，先将设计文档同步到 `docs/` 目录：

1. **覆盖** `docs/web-api.md` - 更新配置字段、数据存储说明
2. **新增/覆盖** `docs/database.md` - Web Channel 数据库设计文档

### 第二步：编写测试（TDD - 先写测试）

在 `tests_web/` 目录下编写测试：

1. `tests_web/test_paths.py` - 测试用户路径函数
2. `tests_web/test_db.py` - 测试数据库 CRUD
3. `tests_web/test_session_manager.py` - 测试 SessionManager 路由
4. `tests_web/test_web_channel.py` - Web Channel 集成测试

### 第三步：实现代码

按以下顺序实现，让测试通过：

1. `nanobot/config/schema.py` - WebConfig 新增 `max_concurrent_users`
2. `nanobot/config/paths.py` - 新增用户路径函数
3. `nanobot/web/models.py` - 添加 UserModel，修改 SessionMetaModel
4. `nanobot/web/db.py` - 添加用户 CRUD 操作，更新会话操作
5. `nanobot/session/manager.py` - SessionManager 路由 Web 会话到用户目录
6. `nanobot/channels/web.py` - 实现用户记录管理、同时在线限制、静态文件路径
7. 移动前端文件到 `frontend/index.html`

---

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `docs/web-api.md` | 覆盖 | 更新配置字段、数据存储说明 |
| `docs/database.md` | 覆盖/新增 | Web Channel 数据库设计文档 |
| `tests_web/__init__.py` | 新增 | 测试包初始化 |
| `tests_web/test_paths.py` | 新增 | 用户路径函数测试 |
| `tests_web/test_db.py` | 新增 | 数据库 CRUD 测试 |
| `tests_web/test_session_manager.py` | 新增 | SessionManager 路由测试 |
| `tests_web/test_web_channel.py` | 新增 | Web Channel 集成测试 |
| `nanobot/config/schema.py` | 修改 | WebConfig 新增 `max_concurrent_users` |
| `nanobot/config/paths.py` | 修改 | 新增用户路径函数 |
| `nanobot/web/models.py` | 修改 | 添加 UserModel，修改 SessionMetaModel |
| `nanobot/web/db.py` | 修改 | 添加用户 CRUD 操作，更新会话操作 |
| `nanobot/session/manager.py` | 修改 | SessionManager 路由 Web 会话到用户目录 |
| `nanobot/channels/web.py` | 修改 | 1. 消息历史读取路径<br>2. 同时在线用户限制<br>3. 用户记录管理<br>4. 静态文件路径改到 frontend/ |
| `frontend/index.html` | 移动 | 从 `nanobot/web/static/index.html` 移动 |

**总计：16 个文件**

---

## 详细变更

### 1. docs/web-api.md - 更新

**更新配置字段说明表格**，添加：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `maxConcurrentUsers` | integer | 否 | 最大同时在线用户数，默认 100 |

**更新"数据存储"章节：

```
## 数据存储

### SQLite 数据库（web.db）
- 位置：`{workspace}/web.db`
- 用途：存储用户信息和会话元数据（不存储对话内容）
- 表结构详见 [database.md](./database.md)

### 消息历史文件（JSONL）
- 位置：`{workspace}/users/{empId}/sessions/web_{uuid}.jsonl`
- 格式：JSON Lines，每行一条消息
- 说明：每个用户有独立的会话目录
```

**新增"WebSocket Close Codes"条目：

| Code | Meaning |
|------|---------|
| 4029 | Too many concurrent users |

### 2. docs/database.md - 新增

```markdown
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
```

### 3. tests_web/test_paths.py - 新增

```python
"""Tests for user path functions."""

from pathlib import Path

import pytest

from nanobot.config.paths import (
    get_user_workspace_path,
    get_user_sessions_path,
    get_user_memory_path,
)


def test_user_workspace_path(monkeypatch, tmp_path: Path) -> None:
    """Test user workspace path generation."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    workspace = get_user_workspace_path("60079031")
    assert workspace == tmp_path / "users" / "60079031"
    assert workspace.exists()


def test_user_sessions_path(monkeypatch, tmp_path: Path) -> None:
    """Test user sessions path generation."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    sessions_dir = get_user_sessions_path("60079031")
    assert sessions_dir == tmp_path / "users" / "60079031" / "sessions"
    assert sessions_dir.exists()


def test_user_memory_path(monkeypatch, tmp_path: Path) -> None:
    """Test user memory path generation."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    memory_dir = get_user_memory_path("60079031")
    assert memory_dir == tmp_path / "users" / "60079031" / "memory"
    assert memory_dir.exists()


def test_different_users_have_different_paths(monkeypatch, tmp_path: Path) -> None:
    """Test different users have different workspace paths."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    workspace1 = get_user_workspace_path("60079031")
    workspace2 = get_user_workspace_path("60079214")

    assert workspace1 != workspace2
```

### 4. tests_web/test_db.py - 新增

（内容略，测试数据库 CRUD 操作）

### 5-9. 其他测试文件

（内容略，测试 SessionManager 路由和 Web Channel 集成测试）

### 10. nanobot/config/schema.py - 修改

```python
class WebConfig(Base):
    """Web channel configuration."""
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 18791
    allow_from: list[str] = Field(default_factory=list)
    cors_origins: list[str] = Field(default_factory=list)
    max_concurrent_users: int = 100  # 新增：最大同时在线用户数
```

### 11. nanobot/config/paths.py - 修改

新增 3 个函数：

```python
def get_user_workspace_path(emp_id: str, workspace: Path | None = None) -> Path:
    """Get the user-specific workspace path."""
    base = get_workspace_path(workspace)
    return ensure_dir(base / "users" / emp_id)


def get_user_sessions_path(emp_id: str, workspace: Path | None = None) -> Path:
    """Get the user-specific sessions directory."""
    return ensure_dir(get_user_workspace_path(emp_id, workspace) / "sessions")


def get_user_memory_path(emp_id: str, workspace: Path | None = None) -> Path:
    """Get the user-specific memory directory."""
    return ensure_dir(get_user_workspace_path(emp_id, workspace) / "memory")
```

### 12. nanobot/web/models.py - 修改

```python
"""SQLAlchemy models for web channel data."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel


Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy model for user information."""
    __tablename__ = "users"

    emp_id = Column(String, primary_key=True, index=True)
    deptname = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    display_name = Column(String, nullable=True)

    # Relationship to sessions
    sessions = relationship("SessionMetaModel", back_populates="user")


class SessionMetaModel(Base):
    """SQLAlchemy model for session metadata."""
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, index=True)
    emp_id = Column(String, ForeignKey("users.emp_id"), nullable=False, index=True)
    name = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message = Column(Text, nullable=False, default="")

    # Relationship to user
    user = relationship("UserModel", back_populates="sessions")


class User(BaseModel):
    """Pydantic model for user information."""
    emp_id: str
    deptname: Optional[str] = None
    created_at: datetime
    last_active_at: datetime
    display_name: Optional[str] = None

    class Config:
        from_attributes = True


class SessionMeta(BaseModel):
    """Pydantic model for session metadata."""
    session_id: str
    emp_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    last_message: str

    class Config:
        from_attributes = True
```

### 13. nanobot/web/db.py - 修改

（内容略，添加用户 CRUD 操作，更新会话操作使用 emp_id）

### 14. nanobot/session/manager.py - 修改

修改 `_get_session_path` 方法，路由 Web Channel 会话到用户目录：

```python
def _get_session_path(self, key: str) -> Path:
    """Get the file path for a session."""
    # Web Channel 会话路由到用户目录
    if key.startswith("web:"):
        parts = key.split(":", 2)
        if len(parts) == 3:
            emp_id = parts[1]
            session_uuid = parts[2]
            from nanobot.config.paths import get_user_sessions_path
            user_sessions_dir = get_user_sessions_path(emp_id, self.workspace)
            safe_key = safe_filename(f"web_{session_uuid}")
            return user_sessions_dir / f"{safe_key}.jsonl"

    # 其他 Channel 保持原有行为
    safe_key = safe_filename(key.replace(":", "_"))
    return self.sessions_dir / f"{safe_key}.jsonl"
```

### 15. nanobot/channels/web.py - 修改

（内容略，包含：
- 同时在线用户跟踪
- WebSocket 端点的用户检查
- 用户记录管理
- 会话历史读取路径
- 静态文件路径改到 frontend/）

---

## 验证清单

- [ ] 文档已同步：`docs/web-api.md` 和 `docs/database.md`
- [ ] 测试已编写：`tests_web/` 目录下所有测试
- [ ] 测试全部通过
- [ ] WebConfig 有 `max_concurrent_users` 字段
- [ ] web.db 包含 `users` 表和 `sessions` 表
- [ ] `sessions.emp_id` 是外键关联到 `users.emp_id`
- [ ] 用户首次访问时自动创建 users 记录
- [ ] 用户访问时更新 last_active_at
- [ ] Web Channel 会话文件存储在 `users/{empId}/sessions/`
- [ ] 其他 channel 会话继续存储在 `sessions/`
- [ ] 同时在线用户数超过限制时拒绝新连接（close code 4029）
- [ ] 同一用户的多个连接不算多个在线用户
- [ ] `/api/sessions/{session_id}/messages` 能正确读取用户目录下的文件
- [ ] 前端文件已移动到 `frontend/index.html`

---

## 第二期：MEMORY.md 隔离 + 用户身份信息注入

### 问题
1. **MEMORY.md 未隔离**：所有 Web Channel 用户共享全局 `workspace/memory/MEMORY.md`，应该使用 `workspace/users/{empId}/memory/MEMORY.md`
2. **用户身份未注入提示词**：empId 和 deptname 没有注入到 LLM 提示词中

### 实现方案

#### 1. MemoryStore 支持用户级别路径

修改 `nanobot/agent/memory.py`：
- `MemoryStore.__init__()` 接受可选的 `emp_id: str | None = None` 参数
- 如果提供 emp_id，使用 `get_user_memory_path(emp_id, workspace)` 作为 memory_dir
- 否则使用原有的 `workspace / "memory"`

#### 2. ContextBuilder 支持用户级别路径和身份注入

修改 `nanobot/agent/context.py`：

**2.1 ContextBuilder.__init__()**
- 接受可选的 `emp_id: str | None = None` 和 `deptname: str | None = None` 参数
- 如果提供 emp_id，初始化 `MemoryStore(workspace, emp_id=emp_id)`
- 保存 `emp_id` 和 `deptname` 为实例变量

**2.2 build_system_prompt()**
- 在系统提示词中添加用户身份信息（如果有）：
  ```
  ## User Identity
  Employee ID: {emp_id}
  Department: {deptname}
  ```

#### 3. AgentLoop 传递用户信息

修改 `nanobot/agent/loop.py`：

**3.1 _process_message()**
- 从 `msg.metadata` 中提取 `emp_id` 和 `deptname`
- 如果是 Web Channel 消息（session_key 以 "web:" 开头），创建一个临时的 `ContextBuilder`，传入 emp_id 和 deptname
- 使用这个临时 ContextBuilder 来调用 `build_messages()`

**或者更优雅的方案**：
- 修改 `ContextBuilder.build_messages()` 签名，接受可选的 `emp_id: str | None = None` 和 `deptname: str | None = None` 参数
- 在方法内部动态构建包含用户身份的系统提示词

#### 4. MemoryConsolidator 支持用户级别

修改 `nanobot/agent/memory.py`：
- `MemoryConsolidator.__init__()` 保持不变（全局 consolidation 不需要）
- 在 `maybe_consolidate_by_tokens()` 中，检查 session key
- 如果是 `web:{empId}:{uuid}` 格式，提取 empId，创建对应的 `MemoryStore(workspace, emp_id=empId)` 进行 consolidation

---

### 完整提示词结构（修改后）

```
[SYSTEM MESSAGE]
  # nanobot 🐈
  - Identity, runtime, workspace, guidelines

  ## User Identity (Web Channel only)
  Employee ID: 60079031
  Department: IT

  ## AGENTS.md
  ## SOUL.md
  ## USER.md
  ## TOOLS.md

  # Memory
  ## Long-term Memory
  (content from users/60079031/memory/MEMORY.md)

  # Active Skills
  ...
```

---

### 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `nanobot/agent/memory.py` | 修改 | MemoryStore 支持可选 emp_id 参数 |
| `nanobot/agent/context.py` | 修改 | 支持用户身份注入提示词 |
| `nanobot/agent/loop.py` | 修改 | 从 metadata 提取 emp_id/deptname 并传递 |

---

## 第三期：Bug 修复

### 问题 1：web.py get_session_messages 中 content 为 None 导致 AttributeError

**问题描述**：
```
AttributeError: 'NoneType' object has no attribute 'strip'
  at web.py line 248: content = msg.get("content", "").strip()
```

**根因**：
- `msg.get("content", "")` 只有在键不存在时才返回默认值 `""`
- 如果键存在但值是 `None` 时，它会返回 `None`
- 然后调用 `.strip()` 就报错了

**修复方案**：
```python
# 修改前
content = msg.get("content", "").strip()

# 修改后
content = (msg.get("content") or "").strip()
```

### 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `nanobot/channels/web.py` | 修改 | 修复 content 为 None 时的 AttributeError |

---

## 第四期：会话删除功能（已完成）

### 需求确认
- 用户在前端页面删除会话
- 删除数据库中的会话记录
- **不删除**对应的聊天记录文件（JSONL）

### 当前状态（已满足需求）
✅ `docs/web-api.md` 中已有 DELETE /api/sessions/{session_id} 文档
✅ 当前实现是**硬删除数据库记录**，但**保留 JSONL 聊天文件**
✅ `list_user_sessions()` 返回所有未删除的会话
✅ 前端删除会话功能完整实现

### 实现细节

#### 后端（nanobot/web/db.py）
- `delete_session(session_id)`: 从数据库删除 `SessionMetaModel` 记录
- **不删除** JSONL 文件
- `list_user_sessions(emp_id)`: 返回该用户所有未删除的会话

#### 前端（frontend/index.html）
- 删除按钮：点击后 confirm 确认
- 调用 `DELETE /api/sessions/{session_id}?empId={empId}`
- 删除成功后：
  - 重新加载会话列表
  - 清空当前会话显示
  - 禁用删除和清空按钮

### 总结
**现有实现已满足需求**，无需修改后端代码。

---

## 第五期：前端删除按钮 UI 优化

### 需求
- 将删除会话按钮从顶部工具栏移到会话列表项上
- 鼠标悬停在会话名称上时，右侧显示删除按钮
- 顶部工具栏的删除会话按钮可以移除或保留

### 实现方案

修改 `frontend/index.html`：

1. **修改会话列表渲染 (`renderSessions()`)**
   - 每个会话项在鼠标悬停时显示删除按钮
   - 删除按钮是一个小的 trash icon，在右侧
   - 点击删除按钮时阻止事件冒泡（不触发选中会话）

2. **移除或保留顶部删除按钮**
   - 可以移除顶部的"删除会话"按钮
   - 或者保留作为备选

3. **CSS 样式**
   - 默认隐藏删除按钮
   - `.session-item:hover .delete-btn { display: block; }`
   - 删除按钮样式：小尺寸、灰色、hover 变红色

### 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `frontend/index.html` | 修改 | 会话列表项添加悬停删除按钮 |

---

## 第六期：前端 Markdown 支持 + 会话命名优化

### 需求
- 聊天内容支持 Markdown 格式（nanobot 很多时候回复的是 Markdown）
- 每个新创建的会话，会话名称就用第一句聊天的前 10~20 个字符

### 实现方案

#### 1. Markdown 支持

修改 `frontend/index.html`：

**1.1 引入 marked.js**
```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

**1.2 修改 addMessage()**
- 对于 assistant 消息，使用 `marked.parse(content)` 渲染 Markdown
- 对于 user 消息，继续使用转义后的纯文本

**1.3 添加 CSS 样式**
- 添加 `.prose` 类样式，用于 Markdown 渲染
- 包括代码块、表格、列表等样式

#### 2. 会话命名优化

修改 `frontend/index.html`：

**修改 sendMessage()**
- 在发送第一条消息时，如果会话名称是 "新对话" 或 "New Chat"
- 使用第一句聊天内容的前 15 个字符作为新会话名称
- 调用 PUT /api/sessions/{session_id} 更新会话名称

### 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `frontend/index.html` | 修改 | 添加 Markdown 支持，会话命名优化 |
