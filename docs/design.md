# nanobot Web Channel - 设计文档

## 开发原则

### 分支管理策略

本项目采用严格的分支管理，确保可以随时同步上游官方更新：

- **Main 分支**：只用于同步上游 nanobot 官方仓库，不进行开发
- **Feat/web-channel 分支**：Web Channel 功能开发，最小化对原有代码的修改

### 代码修改原则

**允许的修改**：
- ✅ 新增文件和功能
- ✅ 必要的配置扩展（添加新的配置类和字段）
- ✅ 添加新的依赖库

**禁止的修改**：
- ❌ 删除任何原有代码、配置或功能
- ❌ 修改现有频道的核心逻辑
- ❌ 修改基础类（除非绝对必要）

**判断标准**：
1. 这个修改是否绝对必要？
2. 能否通过新增代码而非修改代码实现？
3. 是否会影响现有功能？
4. 是否有更优雅的替代方案？

详见：[CLAUDE.md](../CLAUDE.md) 和 [development.md](./development.md#分支管理策略)

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         nanobot                            │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ChannelManager│────────▶│ MessageBus   │                 │
│  └──────┬───────┘         └──────┬───────┘                 │
│         │                        │                          │
│    ┌────┴────┐             ┌─────┴─────┐                   │
│    │WebChannel│             │ AgentLoop │                   │
│    └────┬────┘             └───────────┘                   │
│         │                                                   │
│  ┌──────┴──────────┐                                       │
│  │  FastAPI App    │                                       │
│  │  - REST API     │                                       │
│  │  - WebSocket    │                                       │
│  └──────┬──────────┘                                       │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
    ┌─────┴──────┐
    │  seekdb    │
    │ (Database) │
    └────────────┘
```

### 组件关系

```
nanobot/
├── channels/
│   ├── base.py          # BaseChannel 抽象基类
│   ├── manager.py       # ChannelManager（管理所有 channel）
│   └── web.py           # WebChannel 实现
├── web/                 # FastAPI 应用
│   ├── app.py           # FastAPI 应用主文件
│   ├── database.py      # 数据库连接池
│   ├── schemas.py       # Pydantic 数据模型
│   ├── init_db.py       # 数据库初始化脚本
│   ├── repositories/    # 数据访问层
│   └── routes/          # REST API 路由
├── config/
│   └── schema.py        # 配置模型（WebConfig, DatabaseConfig）
└── bus/
    └── events.py        # 消息事件（InboundMessage, OutboundMessage）
```

## 核心设计

### 1. WebChannel 设计

#### 1.1 类结构

```python
class WebChannel(BaseChannel):
    """Web channel 实现"""

    name = "web"

    def __init__(self, config: WebConfig, bus: MessageBus, ...):
        super().__init__(config, bus)
        self.config: WebConfig
        self.session_manager: SessionManager | None
        self._running: bool
        self._server_task: asyncio.Task | None
        self._uvicorn_server = None
        self._connections: dict[str, dict]  # session_id -> connection info

    async def start(self) -> None:
        """启动 FastAPI 服务器和分发器"""

    async def stop(self) -> None:
        """停止服务器和清理资源"""

    async def send(self, msg: OutboundMessage) -> None:
        """发送消息到 WebSocket 客户端"""

    async def handle_websocket(self, websocket, session_id, user_id):
        """处理 WebSocket 连接"""

    async def _dispatch_outbound(self) -> None:
        """分发出站消息"""
```

#### 1.2 WebSocket 消息协议

**客户端 → 服务端**
```json
// 发送消息
{"type": "message", "data": {"conversation_id": "...", "content": "..."}}

// 请求历史
{"type": "get_history", "data": {"conversation_id": "..."}}

// 心跳
{"type": "ping", "data": {}}
```

**服务端 → 客户端**
```json
// 连接确认
{"type": "connected", "data": {"session_id": "...", "conversation_id": "..."}}

// 新消息
{"type": "message", "data": {"conversation_id": "...", "content": "...", "role": "assistant"}}

// 历史消息
{"type": "history", "data": {"conversation_id": "...", "messages": [...]}}

// 错误
{"type": "error", "data": {"message": "..."}}

// 心跳响应
{"type": "pong", "data": {}}
```

### 2. FastAPI 应用设计

#### 2.1 应用结构

```python
# nanobot/web/app.py
app = FastAPI(title="nanobot Web API")

# 中间件
app.add_middleware(CORSMiddleware)

# 路由
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(search.router)

# 端点
@app.get("/health")
@app.get("/status")
@app.websocket("/ws/{session_id}")

# 全局对象
manager = ConnectionManager()  # WebSocket 连接管理
```

#### 2.2 ConnectionManager

```python
class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.web_channel: WebChannel | None = None

    async def connect(self, session_id: str, websocket: WebSocket):
        """接受连接"""

    def disconnect(self, session_id: str):
        """断开连接"""

    async def send_json(self, session_id: str, data: dict):
        """发送 JSON 消息"""

    async def broadcast(self, data: dict, exclude: str | None = None):
        """广播消息"""
```

### 3. 数据访问层设计

#### 3.1 Repository 模式

```python
# nanobot/web/repositories/conversation_repo.py
class ConversationRepository:
    """会话数据访问"""

    async def create(self, user_id: str, title: str, channel: str) -> dict:
        """创建会话"""

    async def get_by_user(self, user_id: str, limit: int) -> list[dict]:
        """获取用户会话列表"""

    async def get(self, conversation_id: str) -> dict | None:
        """获取单个会话"""

    async def update_title(self, conversation_id: str, title: str) -> bool:
        """更新标题"""

    async def increment_count(self, conversation_id: str) -> bool:
        """增加消息计数"""

    async def delete(self, conversation_id: str) -> bool:
        """删除会话"""

    async def exists(self, conversation_id: str) -> bool:
        """检查会话是否存在"""

# nanobot/web/repositories/message_repo.py
class MessageRepository:
    """消息数据访问"""

    async def add(self, conversation_id: str, role: str, content: str, metadata: dict) -> str:
        """添加消息"""

    async def get_by_conversation(self, conversation_id: str, limit: int) -> list[dict]:
        """获取会话消息"""

    async def search(self, user_id: str, keyword: str, limit: int) -> list[dict]:
        """搜索消息"""

    async def count(self, conversation_id: str) -> int:
        """统计消息数"""
```

#### 3.2 数据库连接池

```python
# nanobot/web/database.py
class Database:
    """数据库连接池"""

    def __init__(self, host, port, user, password, db, pool_size):
        self.pool: aiomysql.Pool | None = None

    async def create_pool(self):
        """创建连接池"""

    @asynccontextmanager
    async def get_connection(self):
        """获取连接（上下文管理器）"""

    async def close(self):
        """关闭连接池"""

    async def health_check(self) -> bool:
        """健康检查"""

# 全局数据库实例
_db: Database | None = None

async def init_database(...) -> Database:
    """初始化全局数据库实例"""
```

### 4. 消息流设计

#### 4.1 消息入站流程

```python
# 1. WebSocket 接收消息
async def handle_websocket(websocket, session_id, user_id):
    data = await websocket.receive_text()
    message = json.loads(data)

    # 2. 保存用户消息到数据库
    if config.persist_to_db:
        await msg_repo.add(
            conversation_id=session_id,
            role="user",
            content=message["content"]
        )

    # 3. 发布到消息总线
    await self._handle_message(
        sender_id=user_id,
        chat_id=session_id,
        content=message["content"]
    )
    # 内部调用: await self.bus.publish_inbound(InboundMessage(...))
```

#### 4.2 消息出站流程

```python
# 1. 订阅消息总线
async def _dispatch_outbound():
    while self._running:
        msg = await self.bus.consume_outbound()

        # 2. 只处理 web channel 的消息
        if msg.channel != self.name:
            continue

        # 3. 发送到 WebSocket
        await send_to_websocket(
            session_id=msg.chat_id,
            message_type="message",
            data={
                "conversation_id": msg.chat_id,
                "content": msg.content,
                "role": "assistant"
            }
        )

        # 4. 保存到数据库
        if config.persist_to_db:
            await msg_repo.add(...)
```

### 5. 配置集成设计

#### 5.1 配置文件结构

```python
# nanobot/config/schema.py
class WebConfig(BaseModel):
    """Web channel 配置"""
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8765
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    auth_token: str = ""
    allow_from: list[str] = Field(default_factory=list)
    max_connections: int = 100
    enable_history_api: bool = True
    persist_to_db: bool = True

class DatabaseConfig(BaseModel):
    """数据库配置"""
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 2881
    user: str = "root"
    password: str = ""
    database: str = "nanobot"
    pool_size: int = 10

class ChannelsConfig(BaseModel):
    """所有渠道配置"""
    whatsapp: WhatsAppConfig
    telegram: TelegramConfig
    discord: DiscordConfig
    feishu: FeishuConfig
    dingtalk: DingTalkConfig
    web: WebConfig  # 新增

class Config(BaseSettings):
    """根配置"""
    agents: AgentsConfig
    channels: ChannelsConfig
    providers: ProvidersConfig
    gateway: GatewayConfig
    tools: ToolsConfig
    database: DatabaseConfig  # 新增
```

#### 5.2 ChannelManager 集成

```python
# nanobot/channels/manager.py
class ChannelManager:
    def _init_channels(self) -> None:
        """初始化所有 channel"""

        # ... 其他 channels ...

        # Web channel
        if self.config.channels.web.enabled:
            from nanobot.channels.web import WebChannel
            self.channels["web"] = WebChannel(
                self.config.channels.web,
                self.bus,
                session_manager=self.session_manager,
            )
```

## 数据模型设计

### Pydantic Schemas

```python
# nanobot/web/schemas.py

class CreateConversationRequest(BaseModel):
    user_id: str
    title: Optional[str] = "新对话"
    channel: Optional[str] = "web"

class CreateConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    channel: str
    message_count: int
    created_at: Optional[str] = None

class MessageRequest(BaseModel):
    conversation_id: str
    content: str
    role: Optional[str] = "user"
    metadata: Optional[dict] = None

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: str

class HealthResponse(BaseModel):
    status: str
    database: Optional[bool] = None
    channels: Optional[dict] = None
```

## 错误处理设计

### 异常处理策略

```python
# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# WebSocket 错误处理
async def handle_websocket(...):
    try:
        # 消息处理逻辑
        pass
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except json.JSONDecodeError:
        await send_to_websocket(session_id, "error", {"message": "Invalid JSON"})
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)
```

### 数据库错误处理

```python
# Repository 错误处理
async def create(self, ...):
    try:
        # 数据库操作
        await cursor.execute(...)
    except aiomysql.MySQLError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
```

## 性能优化设计

### 1. 连接池管理
- 使用 aiomysql 连接池
- 最小连接数: 5
- 最大连接数: 10
- 自动重连机制

### 2. 异步处理
- 所有 I/O 操作使用 async/await
- 避免阻塞事件循环

### 3. 查询优化
- 使用索引加速查询
- 限制返回结果数量（limit）
- 分页加载

### 4. WebSocket 优化
- 心跳检测（30s）
- 自动重连（指数退避）
- 连接数限制

## 安全设计

### 1. CORS 配置
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 认证机制
```python
# Token 认证（可选）
if config.auth_token:
    token = websocket.query_params.get("token")
    if token != config.auth_token:
        await websocket.close(code=1008, reason="Invalid token")
        return
```

### 3. 权限控制
```python
# 用户白名单
if not self.is_allowed(user_id):
    await websocket.close(code=1003, reason="Access denied")
    return
```

### 4. SQL 注入防护
- 使用参数化查询
- Pydantic 数据验证

## 测试策略

### 单元测试
- Repository 层测试
- Schema 验证测试
- 工具函数测试

### 集成测试
- API 端点测试
- WebSocket 通信测试
- 数据库集成测试

### 端到端测试
- 完整消息流测试
- 多客户端并发测试
- 错误恢复测试
